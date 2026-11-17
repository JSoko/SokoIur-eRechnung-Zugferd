"""
utils.py
--------
Globale Hilfsfunktionen für Datumsberechnungen, Nummernkreise und Währungsformatierungen.
"""
import re
from datetime import datetime

EINHEITEN_LISTE = [
    "Stück (C62)", "Pauschale (LS)", "Stunde(n) (HUR)", 
    "Monat(e) (MON)", "Tag(e) (DAY)", "km (KMT)", "Satz (SET)"
]

EINHEITEN_MAPPING = {
    "C62": "Stück", "LS": "Pauschale", "HUR": "Stunde(n)",
    "MON": "Monat(e)", "DAY": "Tag(e)", "KMT": "km", "SET": "Satz"
}

def berechne_naechste_rechnungsnummer(letzte_nr):
    if not letzte_nr: return f"RE-{datetime.now().year}-001"
    match = re.search(r'(\d+)$', letzte_nr)
    if match:
        zahl_str = match.group(1)
        naechste_zahl = str(int(zahl_str) + 1).zfill(len(zahl_str))
        return letzte_nr[:match.start()] + naechste_zahl
    return letzte_nr + "-1"

def parse_flexible_date(d_str):
    if not d_str: return ""
    d_str = d_str.strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', d_str): return d_str
    formate = ["%d%m%y", "%d,%m,%y", "%d.%m.%Y", "%d,%m,%Y", "%d.%m.%y"]
    for fmt in formate:
        try: return datetime.strptime(d_str, fmt).strftime("%Y-%m-%d")
        except ValueError: continue
    return d_str

def parse_flexible_date_span(span_str):
    if not span_str: return ""
    span_str = span_str.strip()
    if "|" in span_str:
        parts = span_str.split('|', 1)
        return f"{parse_flexible_date(parts[0])}|{parse_flexible_date(parts[1])}"
    if "-" in span_str and not re.match(r'^\d{4}-\d{2}-\d{2}$', span_str):
        parts = span_str.split('-', 1)
        s = parse_flexible_date(parts[0])
        e = parse_flexible_date(parts[1])
        if re.match(r'^\d{4}-\d{2}-\d{2}$', s) and re.match(r'^\d{4}-\d{2}-\d{2}$', e):
            return f"{s}|{e}"
    return parse_flexible_date(span_str)

def formatiere_datum(d_str): return datetime.strptime(d_str, '%Y-%m-%d').strftime('%Y%m%d')
def formatiere_datum_lesbar(d_str): return datetime.strptime(d_str, '%Y-%m-%d').strftime('%d.%m.%Y')

def parse_lz_lesbar(lz_str):
    if not lz_str: return ""
    if "|" in lz_str:
        s, e = lz_str.split('|')
        s_lesbar = formatiere_datum_lesbar(s)
        e_lesbar = formatiere_datum_lesbar(e)
        if s_lesbar == e_lesbar:
            return s_lesbar
        return f"{s_lesbar} - {e_lesbar}"
    return formatiere_datum_lesbar(lz_str)

def safe_float(wert, fallback=0.0):
    try: return float(str(wert).replace(',', '.'))
    except (ValueError, TypeError): return fallback

def f_curr(val):
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def f_num(val):
    return f"{val:g}".replace('.', ',')

def check_lz_logic(kopf, positionen):
    def get_dates(lz_str):
        if not lz_str: return None, None
        parts = lz_str.split('|')
        try:
            s = datetime.strptime(parts[0], "%Y-%m-%d")
            e = datetime.strptime(parts[1] if len(parts) > 1 else parts[0], "%Y-%m-%d")
            return s, e
        except: return None, None

    g_s, g_e = get_dates(kopf.get('LeistungszeitraumKopf', '').strip())
    
    for pos in positionen:
        lz_pos = pos.get('LeistungszeitraumPos', '').strip()
        if not g_s and not lz_pos:
            return False, f"Fehler bei Position {pos.get('PosNr')}: Es wurde weder ein Leistungszeitraum für die gesamte Rechnung noch für diese Position angegeben."
        if g_s and g_e and lz_pos:
            p_s, p_e = get_dates(lz_pos)
            if p_s and p_e:
                if p_s < g_s or p_e > g_e:
                    return False, f"Fehler bei Position {pos.get('PosNr')}:\nDer Zeitraum der Position ({parse_lz_lesbar(lz_pos)}) liegt außerhalb des Zeitraums der Gesamtrechnung ({parse_lz_lesbar(kopf.get('LeistungszeitraumKopf', ''))}).\n\nBitte korrigieren Sie die Daten entsprechend."
    return True, ""