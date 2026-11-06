import csv
import os
import sys
import json
import argparse
import re
import webbrowser
import time
from datetime import datetime, timedelta
from io import BytesIO
import tkinter as tk

# GUI Bibliotheken
import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog

# PDF Bibliotheken
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, ArrayObject, StreamObject

CONFIG_DATEI = "config.json"
LOCK_FILE = "erechnung.lock"

EINHEITEN_LISTE = [
    "Stück (C62)", "Pauschale (LS)", "Stunde(n) (HUR)", 
    "Monat(e) (MON)", "Tag(e) (DAY)", "km (KMT)", "Satz (SET)"
]

# ==========================================
# KERNDATEN & LOGIK (Unverändert im Hintergrund)
# ==========================================

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def lade_config():
    if os.path.exists(CONFIG_DATEI):
        try:
            with open(CONFIG_DATEI, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def speichere_config(config):
    with open(CONFIG_DATEI, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def init_config():
    config = lade_config()
    defaults = {
        "firma_csv": "firma.csv", "rechnung_csv": "rechnung.csv",
        "briefbogen_pdf": "briefbogen.pdf", "zusatz_csv": "zusatz.csv",
        "gruss_csv": "gruss.csv", "header_csv": "header.csv",
        "einleitung_csv": "einleitung.csv", "ausgabe_ordner": "Rechnungen_PDF",
        "kunden_csv": "kunden.csv", "produkte_csv": "produkte.csv",
        "auswertungen_ordner": "Auswertungen",
        "faelligkeit_tage": "29",
        "letzte_rechnungsnummer": "",
        "window_geometry": "950x850",
        "letzte_einheit": "Stück (C62)",
        "keep_header": True,
        "keep_einleitung": True,
        "keep_gruss": True,
        "terms_accepted": False,
        "keep_raten": False,
        "keep_kunde_speichern": False
    }
    for k, v in defaults.items():
        if k not in config: config[k] = v
    if not os.path.exists(config["ausgabe_ordner"]): os.makedirs(config["ausgabe_ordner"])
    if not os.path.exists(config["auswertungen_ordner"]): os.makedirs(config["auswertungen_ordner"])
    return config

def berechne_naechste_rechnungsnummer(letzte_nr):
    if not letzte_nr: return f"RE-{datetime.now().year}-001"
    match = re.search(r'(\d+)$', letzte_nr)
    if match:
        zahl_str = match.group(1)
        naechste_zahl = str(int(zahl_str) + 1).zfill(len(zahl_str))
        return letzte_nr[:match.start()] + naechste_zahl
    return letzte_nr + "-1"

def lade_firma(pfad):
    with open(pfad, mode='r', encoding='utf-8-sig') as f:
        return next(csv.DictReader(f, delimiter=';'))

def lade_rechnungen(pfad):
    rechnungen = {}
    with open(pfad, mode='r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f, delimiter=';'):
            r_nr = row['Rechnungsnummer']
            if r_nr not in rechnungen: rechnungen[r_nr] = {'kopf': row, 'positionen': []}
            rechnungen[r_nr]['positionen'].append(row)
    return rechnungen

def lade_zusatz_csv(pfad):
    texte = []
    if not os.path.exists(pfad): return texte
    with open(pfad, mode='r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split(';', 1)
            if len(parts) == 2:
                texte.append({'pos': parts[0].strip(), 'text': parts[1].strip().replace('~cr', '\n')})
    return texte

def lade_textdatei(pfad):
    if not os.path.exists(pfad): return ""
    with open(pfad, mode='r', encoding='utf-8-sig') as f:
        return f.read().strip().replace('~cr', '\n')

def speichere_textdatei(pfad, text):
    if not pfad: return
    with open(pfad, 'w', encoding='utf-8-sig') as f:
        f.write(text.replace('\n', '~cr').strip())

def lade_kunden(pfad):
    kunden = []
    if not os.path.exists(pfad): return kunden
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f, delimiter=';'):
                kunden.append(row)
    except: pass
    return kunden

def speichere_alle_kunden(pfad, kunden_liste):
    fieldnames = ['Name', 'Strasse', 'PLZ_Ort', 'Land', 'KundeNr', 'Aktenzeichen']
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(kunden_liste)

def lade_produkte(pfad):
    produkte = []
    if not os.path.exists(pfad): return produkte
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f, delimiter=';'):
                produkte.append(row)
    except: pass
    return produkte

def speichere_alle_produkte(pfad, produkte_liste):
    fieldnames = ['Bezeichnung', 'Menge', 'Einheit', 'EinzelpreisNetto', 'Steuersatz']
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(produkte_liste)

def speichere_kunde(pfad, kunde_daten):
    kunden = lade_kunden(pfad)
    updated = False
    for k in kunden:
        if k['Name'].strip().lower() == kunde_daten['Name'].strip().lower():
            k.update(kunde_daten)
            updated = True
            break
    if not updated:
        kunden.append(kunde_daten)
    speichere_alle_kunden(pfad, kunden)

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
        return f"{formatiere_datum_lesbar(s)} - {formatiere_datum_lesbar(e)}"
    return formatiere_datum_lesbar(lz_str)

def safe_float(wert, fallback=0.0):
    try: return float(str(wert).replace(',', '.'))
    except (ValueError, TypeError): return fallback

def f_curr(val):
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def f_num(val):
    return f"{val:g}".replace('.', ',')

EINHEITEN_MAPPING = {
    "C62": "Stück", "LS": "Pauschale", "HUR": "Stunde(n)",
    "MON": "Monat(e)", "DAY": "Tag(e)", "KMT": "km", "SET": "Satz"
}

def esc_xml(text):
    if text is None: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def clean_xml_text(text):
    text = re.sub(r'~f|f~|~k|k~', '', str(text))
    return esc_xml(text)

def zeichne_formatierten_text(c, x, y, text, size=10, align="left"):
    is_bold = False
    is_italic = False
    tokens = re.split(r'(~f|f~|~k|k~)', text)
    
    total_width = 0
    for token in tokens:
        if token in ('~f', 'f~', '~k', 'k~', ''): continue
        if is_bold and is_italic: font = "Helvetica-BoldOblique"
        elif is_bold: font = "Helvetica-Bold"
        elif is_italic: font = "Helvetica-Oblique"
        else: font = "Helvetica"
        total_width += c.stringWidth(token, font, size)
        
    if align == "center": current_x = (A4[0] / 2.0) - (total_width / 2.0)
    elif align == "right": current_x = x - total_width
    else: current_x = x
        
    is_bold = False
    is_italic = False
    for token in tokens:
        if token == '~f': is_bold = True; continue
        if token == 'f~': is_bold = False; continue
        if token == '~k': is_italic = True; continue
        if token == 'k~': is_italic = False; continue
        if not token: continue

        if is_bold and is_italic: font = "Helvetica-BoldOblique"
        elif is_bold: font = "Helvetica-Bold"
        elif is_italic: font = "Helvetica-Oblique"
        else: font = "Helvetica"

        c.setFont(font, size)
        c.drawString(current_x, y, token)
        current_x += c.stringWidth(token, font, size)

def split_text_to_lines(text, width_limit, c, font="Helvetica", size=10):
    c.setFont(font, size)
    words = str(text).split()
    if not words: return [""]
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font, size) <= width_limit:
            current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    return lines

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


def generiere_rechnung_text_pdf(firma, kopf, positionen, gesamt_netto, gesamt_steuer, gesamt_brutto, zusatztexte, gruss_text, header_text, einleitung_text):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    breite, hoehe = A4
    page_num = 1
    
    def check_page_break(y, req_height):
        nonlocal page_num
        if y - req_height < 100:
            c.showPage()
            page_num += 1
            c.setFillColorRGB(1, 1, 1)
            c.rect(0, hoehe - 140, breite, 140, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 10)
            c.drawCentredString(breite / 2.0, hoehe - 50, f"- {page_num} -")
            return hoehe - 100
        return y
    
    c.setFont("Helvetica", 7)
    c.drawString(60, hoehe - 130, f"{firma['FirmaName']}, {firma['Strasse']}, {firma['PLZ']} {firma['Ort']}")
    
    c.setFont("Helvetica", 11)
    c.drawString(60, hoehe - 160, kopf['KundeName'])
    c.drawString(60, hoehe - 175, kopf['KundeStrasse'])
    c.drawString(60, hoehe - 190, f"{kopf['KundePLZ']} {kopf['KundeOrt']}")
    if kopf['KundeLand'] != 'DE': c.drawString(60, hoehe - 205, kopf['KundeLand'])
        
    y_tabelle = hoehe - 240
    
    if header_text:
        for zeile in header_text.split('\n'):
            zeichne_formatierten_text(c, 0, y_tabelle, zeile, 12, align="center")
            y_tabelle -= 18
        y_tabelle -= 10
    
    r_nr = kopf['Rechnungsnummer']
    r_dat = formatiere_datum_lesbar(kopf['Rechnungsdatum'])
    f_dat = formatiere_datum_lesbar(kopf['Faelligkeitsdatum'])
    
    rech_zeile = f"Rechnung Nr.: {r_nr}  |  Datum: {r_dat}  |  Fällig bis: {f_dat}"
    zeichne_formatierten_text(c, 60, y_tabelle, f"~f{rech_zeile}f~", 11, align="left")
    y_tabelle -= 18
    
    kd_az_zeilen = []
    kdnr = kopf.get('KundeNr', '').strip()
    az = kopf.get('Aktenzeichen', '').strip()
    lz = parse_lz_lesbar(kopf.get('LeistungszeitraumKopf', ''))

    if kdnr or az:
        parts = []
        if kdnr: parts.append(f"Kunden-Nr.: {kdnr}")
        if az: parts.append(f"Aktenzeichen: {az}")
        kd_az_zeilen.append("  |  ".join(parts))
    if lz: kd_az_zeilen.append(f"Leistungszeitraum: {lz}")

    for zeile in kd_az_zeilen:
        zeichne_formatierten_text(c, 60, y_tabelle, f"~f{zeile}f~", 10, align="left")
        y_tabelle -= 15
    if kd_az_zeilen: y_tabelle -= 5
    y_tabelle -= 5 
    
    if einleitung_text:
        for zeile in einleitung_text.split('\n'):
            y_tabelle = check_page_break(y_tabelle, 15)
            zeichne_formatierten_text(c, 60, y_tabelle, zeile, 10, align="left")
            y_tabelle -= 15
        y_tabelle -= 10
    else: y_tabelle -= 10

    y_tabelle = check_page_break(y_tabelle, 20)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_tabelle, "Pos.")
    c.drawString(100, y_tabelle, "Bezeichnung")
    c.drawRightString(350, y_tabelle, "Menge")
    c.drawRightString(440, y_tabelle, "Einzelpreis")
    c.drawRightString(530, y_tabelle, "Gesamt")
    y_tabelle -= 20
    
    c.setFont("Helvetica", 10)
    for pos in positionen:
        menge = safe_float(pos['Menge'], 1.0)
        preis = safe_float(pos['EinzelpreisNetto'], 0.0)
        
        einheit_raw = pos.get('Einheit', 'C62').strip()
        match = re.search(r'\((.*?)\)', einheit_raw)
        code = match.group(1).strip() if match else einheit_raw
        einheit_lesbar = EINHEITEN_MAPPING.get(code, code)
        menge_str = f"{f_num(menge)} {einheit_lesbar}"
        
        bez_lines = split_text_to_lines(pos['Bezeichnung'], 230, c)
        lz_pos_str = parse_lz_lesbar(pos.get('LeistungszeitraumPos', ''))
        
        req_height = (len(bez_lines) * 12) + (15 if lz_pos_str else 5)
        y_tabelle = check_page_break(y_tabelle, req_height)
        
        c.setFont("Helvetica", 10)
        c.drawString(60, y_tabelle, str(pos['PosNr']))
        c.drawRightString(350, y_tabelle, menge_str) 
        c.drawRightString(440, y_tabelle, f_curr(preis))
        c.drawRightString(530, y_tabelle, f_curr(menge * preis))
        
        for i, b_line in enumerate(bez_lines):
            c.drawString(100, y_tabelle - (i * 12), b_line)
        y_tabelle -= (len(bez_lines) * 12)
        
        if lz_pos_str:
            zeichne_formatierten_text(c, 100, y_tabelle, f"~kLeistungszeitraum: {lz_pos_str}k~", 9)
            y_tabelle -= 15
        else: y_tabelle -= 5
            
    y_tabelle -= 10
    y_tabelle = check_page_break(y_tabelle, 80)
    
    c.line(380, y_tabelle + 10, 530, y_tabelle + 10)
    c.drawString(380, y_tabelle - 5, "Netto Gesamt:")
    c.drawRightString(530, y_tabelle - 5, f_curr(gesamt_netto))
    y_tabelle -= 15
    
    steuer_gruppen = {}
    for pos in positionen:
        satz = safe_float(pos.get('Steuersatz', 19.0))
        st = safe_float(pos['Menge'], 1.0) * safe_float(pos['EinzelpreisNetto'], 0.0) * (satz / 100.0)
        if satz > 0:
            if satz not in steuer_gruppen: steuer_gruppen[satz] = 0.0
            steuer_gruppen[satz] += st
            
    for satz, s_wert in sorted(steuer_gruppen.items()):
        c.drawString(380, y_tabelle - 5, f"zzgl. {f_num(satz)}% MwSt.:")
        c.drawRightString(530, y_tabelle - 5, f_curr(s_wert))
        y_tabelle -= 15
        
    c.setFont("Helvetica-Bold", 10)
    c.drawString(380, y_tabelle - 5, "Rechnungsbetrag:")
    c.drawRightString(530, y_tabelle - 5, f_curr(gesamt_brutto))
    y_tabelle -= 30
    
    if zusatztexte:
        for z in zusatztexte:
            lines = z['text'].split('\n')
            req_h = len(lines) * 15 + (15 if z['pos'] != '0' else 0)
            y_tabelle = check_page_break(y_tabelle, req_h)
            if z['pos'] != '0': 
                c.setFont("Helvetica-Bold", 10)
                c.drawString(60, y_tabelle, f"Zu Position(en) {z['pos']}:")
                y_tabelle -= 15
            for zeile in lines:
                zeichne_formatierten_text(c, 60, y_tabelle, zeile, 10)
                y_tabelle -= 15
            y_tabelle -= 5

    z_csv = kopf.get('Zusatztext', '').strip()
    if z_csv:
        lines = z_csv.split('\\n')
        y_tabelle = check_page_break(y_tabelle, len(lines) * 15)
        for zeile in lines:
            zeichne_formatierten_text(c, 60, y_tabelle, zeile, 10)
            y_tabelle -= 15
        y_tabelle -= 10 

    y_tabelle -= 10
    y_tabelle = check_page_break(y_tabelle, 80)
    
    c.setFont("Helvetica", 10)
    if gesamt_brutto < 0:
        c.drawString(60, y_tabelle, "Dieser Beleg weist ein Guthaben zu Ihren Gunsten aus.")
        c.drawString(60, y_tabelle - 15, "Eine Zahlung Ihrerseits ist nicht erforderlich.")
        y_tabelle -= 45
    elif gesamt_brutto == 0:
        c.drawString(60, y_tabelle, "Der Rechnungsbetrag beläuft sich auf 0,00 €.")
        c.drawString(60, y_tabelle - 15, "Eine Zahlung Ihrerseits ist nicht erforderlich.")
        y_tabelle -= 45
    else:
        bank_name = firma.get('BankName', '')
        iban = firma.get('IBAN', '')
        bic = firma.get('BIC', '')
        is_raten = str(kopf.get('Ratenzahlung', '')).lower() in ['true', '1', 'ja', 'yes']
        
        if is_raten:
            zahl_text = f"Bitte überweisen Sie den Betrag bis zum {f_dat} auf unser Konto bei der {bank_name} oder nehmen Sie bis zu diesem Termin monatliche Ratenzahlungen auf."
        else:
            zahl_text = f"Bitte überweisen Sie den Betrag bis zum {f_dat} auf unser Konto bei der {bank_name}."
            
        zahl_lines = split_text_to_lines(zahl_text, 470, c)
        for zl in zahl_lines:
            c.drawString(60, y_tabelle, zl)
            y_tabelle -= 15
            
        c.drawString(60, y_tabelle, f"IBAN: {iban} | BIC: {bic}")
        y_tabelle -= 30
    
    if gruss_text:
        lines = gruss_text.split('\n')
        y_tabelle = check_page_break(y_tabelle, len(lines) * 15)
        for zeile in lines:
            zeichne_formatierten_text(c, 60, y_tabelle, zeile, 10)
            y_tabelle -= 15

    c.save()
    packet.seek(0)
    return packet

def erstelle_zugferd_pdf(firma, rechnung_daten, brief_pfad, zusatztexte, gruss_text, header_text, einleitung_text, ausgabe_ordner):
    kopf, positionen = rechnung_daten['kopf'], rechnung_daten['positionen']
    r_nr = kopf['Rechnungsnummer']
    
    kunde_name_xml = esc_xml(kopf.get('KundeName', '').strip())
    if not kunde_name_xml: kunde_name_xml = "Nicht angegeben"
    
    r_datum, f_datum = formatiere_datum(kopf['Rechnungsdatum']), formatiere_datum(kopf['Faelligkeitsdatum'])
    
    # NEU: Entferne alle Leerzeichen aus IBAN und BIC für ZUGFeRD-Validierung (BR-DE-19)
    iban_clean = re.sub(r'\s+', '', firma.get('IBAN', ''))
    bic_clean = re.sub(r'\s+', '', firma.get('BIC', ''))
    
    gesamt_netto = gesamt_steuer = 0.0
    xml_positionen = ""
    steuer_gruppen = {}
    
    for pos in positionen:
        menge = safe_float(pos['Menge'], 1.0)
        preis = safe_float(pos['EinzelpreisNetto'], 0.0)
        steuersatz = safe_float(pos['Steuersatz'], 19.0)
        
        pos_netto = menge * preis
        pos_steuer = pos_netto * (steuersatz / 100.0)
        
        gesamt_netto += pos_netto
        gesamt_steuer += pos_steuer
        
        if steuersatz not in steuer_gruppen: steuer_gruppen[steuersatz] = {'netto': 0.0, 'steuer': 0.0}
        steuer_gruppen[steuersatz]['netto'] += pos_netto
        steuer_gruppen[steuersatz]['steuer'] += pos_steuer
        
        einheit_raw = str(pos.get('Einheit', 'C62')).strip()
        match = re.search(r'\((.*?)\)', einheit_raw)
        einheit_code = match.group(1).strip() if match else einheit_raw
        if not einheit_code.isalnum(): einheit_code = "C62"
        
        cat_code = "S" if steuersatz > 0 else "E"
        
        if preis < 0:
            preis_xml = abs(preis)
            menge_xml = pos_netto / preis_xml if preis_xml != 0 else 0.0
        else:
            preis_xml = preis
            menge_xml = menge
        
        lz_pos_raw = pos.get('LeistungszeitraumPos', '').strip()
        xml_billing_period_pos = ""
        if lz_pos_raw:
            if "|" in lz_pos_raw:
                start_d, end_d = lz_pos_raw.split('|')
                xml_billing_period_pos = f"""
                <ram:BillingSpecifiedPeriod>
                    <ram:StartDateTime><udt:DateTimeString format="102">{formatiere_datum(start_d)}</udt:DateTimeString></ram:StartDateTime>
                    <ram:EndDateTime><udt:DateTimeString format="102">{formatiere_datum(end_d)}</udt:DateTimeString></ram:EndDateTime>
                </ram:BillingSpecifiedPeriod>"""
            else:
                s_date = formatiere_datum(lz_pos_raw)
                xml_billing_period_pos = f"""
                <ram:BillingSpecifiedPeriod>
                    <ram:StartDateTime><udt:DateTimeString format="102">{s_date}</udt:DateTimeString></ram:StartDateTime>
                    <ram:EndDateTime><udt:DateTimeString format="102">{s_date}</udt:DateTimeString></ram:EndDateTime>
                </ram:BillingSpecifiedPeriod>"""
        
        xml_positionen += f"""
        <ram:IncludedSupplyChainTradeLineItem>
            <ram:AssociatedDocumentLineDocument><ram:LineID>{esc_xml(pos.get('PosNr', ''))}</ram:LineID></ram:AssociatedDocumentLineDocument>
            <ram:SpecifiedTradeProduct><ram:Name>{esc_xml(pos.get('Bezeichnung', ''))}</ram:Name></ram:SpecifiedTradeProduct>
            <ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>{preis_xml:.2f}</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>
            <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="{esc_xml(einheit_code)}">{menge_xml:.2f}</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
            <ram:SpecifiedLineTradeSettlement>
                <ram:ApplicableTradeTax><ram:TypeCode>VAT</ram:TypeCode><ram:CategoryCode>{cat_code}</ram:CategoryCode><ram:RateApplicablePercent>{steuersatz:.2f}</ram:RateApplicablePercent></ram:ApplicableTradeTax>
                {xml_billing_period_pos}
                <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>{pos_netto:.2f}</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
            </ram:SpecifiedLineTradeSettlement>
        </ram:IncludedSupplyChainTradeLineItem>"""

    gesamt_brutto = gesamt_netto + gesamt_steuer

    xml_tax_totals = ""
    for satz, werte in steuer_gruppen.items():
        cat_code = "S" if satz > 0 else "E"
        xml_tax_totals += f"""
            <ram:ApplicableTradeTax>
                <ram:CalculatedAmount>{werte['steuer']:.2f}</ram:CalculatedAmount>
                <ram:TypeCode>VAT</ram:TypeCode>
                <ram:BasisAmount>{werte['netto']:.2f}</ram:BasisAmount>
                <ram:CategoryCode>{cat_code}</ram:CategoryCode>
                <ram:RateApplicablePercent>{satz:.2f}</ram:RateApplicablePercent>
            </ram:ApplicableTradeTax>"""
            
    lz_kopf = kopf.get('LeistungszeitraumKopf', '').strip()
    xml_delivery_event = ""
    xml_billing_period_header = ""

    if lz_kopf:
        if "|" in lz_kopf:
            start_d, end_d = lz_kopf.split('|')
            xml_billing_period_header = f"""
            <ram:BillingSpecifiedPeriod>
                <ram:StartDateTime><udt:DateTimeString format="102">{formatiere_datum(start_d)}</udt:DateTimeString></ram:StartDateTime>
                <ram:EndDateTime><udt:DateTimeString format="102">{formatiere_datum(end_d)}</udt:DateTimeString></ram:EndDateTime>
            </ram:BillingSpecifiedPeriod>"""
            xml_delivery_event = f"""<ram:ActualDeliverySupplyChainEvent><ram:OccurrenceDateTime><udt:DateTimeString format="102">{r_datum}</udt:DateTimeString></ram:OccurrenceDateTime></ram:ActualDeliverySupplyChainEvent>"""
        else:
            deliv_d_xml = formatiere_datum(lz_kopf)
            xml_delivery_event = f"""<ram:ActualDeliverySupplyChainEvent><ram:OccurrenceDateTime><udt:DateTimeString format="102">{deliv_d_xml}</udt:DateTimeString></ram:OccurrenceDateTime></ram:ActualDeliverySupplyChainEvent>"""
    else:
        xml_delivery_event = f"""<ram:ActualDeliverySupplyChainEvent><ram:OccurrenceDateTime><udt:DateTimeString format="102">{r_datum}</udt:DateTimeString></ram:OccurrenceDateTime></ram:ActualDeliverySupplyChainEvent>"""
    
    xml_notes_str = ""
    if header_text: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(header_text)}</ram:Content></ram:IncludedNote>\n"
    if einleitung_text: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(einleitung_text)}</ram:Content></ram:IncludedNote>\n"
    for z in zusatztexte:
        pre = f"Zu Position(en) {z['pos']}:\n" if z['pos'] != '0' else ""
        xml_notes_str += f"<ram:IncludedNote><ram:Content>{pre}{clean_xml_text(z['text'])}</ram:Content></ram:IncludedNote>\n"
    z_csv = kopf.get('Zusatztext', '').strip()
    if z_csv: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(z_csv.replace('\\n', '\n'))}</ram:Content></ram:IncludedNote>\n"
    if gruss_text: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(gruss_text)}</ram:Content></ram:IncludedNote>\n"
    
    xml_buyer_ref = f"<ram:BuyerReference>{esc_xml(kopf.get('Aktenzeichen', '').strip())}</ram:BuyerReference>" if kopf.get('Aktenzeichen', '').strip() else ""
    xml_buyer_id = f"<ram:ID>{esc_xml(kopf.get('KundeNr', '').strip())}</ram:ID>" if kopf.get('KundeNr', '').strip() else ""
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
    <rsm:ExchangedDocumentContext><ram:GuidelineSpecifiedDocumentContextParameter><ram:ID>urn:cen.eu:en16931:2017</ram:ID></ram:GuidelineSpecifiedDocumentContextParameter></rsm:ExchangedDocumentContext>
    <rsm:ExchangedDocument><ram:ID>{esc_xml(r_nr)}</ram:ID><ram:TypeCode>380</ram:TypeCode><ram:IssueDateTime><udt:DateTimeString format="102">{r_datum}</udt:DateTimeString></ram:IssueDateTime>{xml_notes_str.strip()}</rsm:ExchangedDocument>
    <rsm:SupplyChainTradeTransaction>
        {xml_positionen}
        <ram:ApplicableHeaderTradeAgreement>
            {xml_buyer_ref}
            <ram:SellerTradeParty>
                <ram:Name>{esc_xml(firma['FirmaName'])}</ram:Name>
                <ram:PostalTradeAddress><ram:PostcodeCode>{esc_xml(firma['PLZ'])}</ram:PostcodeCode><ram:LineOne>{esc_xml(firma['Strasse'])}</ram:LineOne><ram:CityName>{esc_xml(firma['Ort'])}</ram:CityName><ram:CountryID>{esc_xml(firma['Land'])}</ram:CountryID></ram:PostalTradeAddress>
                <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">{esc_xml(firma['UStId'])}</ram:ID></ram:SpecifiedTaxRegistration>
            </ram:SellerTradeParty>
            <ram:BuyerTradeParty>
                {xml_buyer_id}
                <ram:Name>{kunde_name_xml}</ram:Name>
                <ram:PostalTradeAddress><ram:PostcodeCode>{esc_xml(kopf.get('KundePLZ',''))}</ram:PostcodeCode><ram:LineOne>{esc_xml(kopf.get('KundeStrasse',''))}</ram:LineOne><ram:CityName>{esc_xml(kopf.get('KundeOrt',''))}</ram:CityName><ram:CountryID>{esc_xml(kopf.get('KundeLand','DE'))}</ram:CountryID></ram:PostalTradeAddress>
            </ram:BuyerTradeParty>
        </ram:ApplicableHeaderTradeAgreement>
        <ram:ApplicableHeaderTradeDelivery>
            {xml_delivery_event}
        </ram:ApplicableHeaderTradeDelivery>
        <ram:ApplicableHeaderTradeSettlement>
            <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
            <ram:SpecifiedTradeSettlementPaymentMeans>
                <ram:TypeCode>58</ram:TypeCode>
                <ram:PayeePartyCreditorFinancialAccount><ram:IBANID>{esc_xml(iban_clean)}</ram:IBANID></ram:PayeePartyCreditorFinancialAccount>
                <ram:PayeeSpecifiedCreditorFinancialInstitution><ram:BICID>{esc_xml(bic_clean)}</ram:BICID></ram:PayeeSpecifiedCreditorFinancialInstitution>
            </ram:SpecifiedTradeSettlementPaymentMeans>
            {xml_tax_totals}
            {xml_billing_period_header}
            <ram:SpecifiedTradePaymentTerms><ram:DueDateDateTime><udt:DateTimeString format="102">{f_datum}</udt:DateTimeString></ram:DueDateDateTime></ram:SpecifiedTradePaymentTerms>
            <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                <ram:LineTotalAmount>{gesamt_netto:.2f}</ram:LineTotalAmount><ram:TaxBasisTotalAmount>{gesamt_netto:.2f}</ram:TaxBasisTotalAmount>
                <ram:TaxTotalAmount currencyID="EUR">{gesamt_steuer:.2f}</ram:TaxTotalAmount><ram:GrandTotalAmount>{gesamt_brutto:.2f}</ram:GrandTotalAmount><ram:DuePayableAmount>{gesamt_brutto:.2f}</ram:DuePayableAmount>
            </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        </ram:ApplicableHeaderTradeSettlement>
    </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>"""

    text_pdf_stream = generiere_rechnung_text_pdf(firma, kopf, positionen, gesamt_netto, gesamt_steuer, gesamt_brutto, zusatztexte, gruss_text, header_text, einleitung_text)
    text_pdf = PdfReader(text_pdf_stream)
    writer = PdfWriter()
    
    writer._header = b"%PDF-1.7"
    
    try:
        briefbogen_pfad = brief_pfad if os.path.exists(brief_pfad) else None
        
        if briefbogen_pfad:
            brief_reader = PdfReader(briefbogen_pfad)
            seite_1 = brief_reader.pages[0]
            seite_1.merge_page(text_pdf.pages[0])
            writer.add_page(seite_1)
            
            for i in range(1, len(text_pdf.pages)):
                brief_reader_neu = PdfReader(briefbogen_pfad) 
                weitere_seite = brief_reader_neu.pages[1] if len(brief_reader_neu.pages) > 1 else brief_reader_neu.pages[0]
                weitere_seite.merge_page(text_pdf.pages[i])
                writer.add_page(weitere_seite)
        else:
            for page in text_pdf.pages: writer.add_page(page)
    except Exception as e:
        print(f"Merge Fehler: {e}")
        for page in text_pdf.pages: writer.add_page(page)

    writer.add_attachment("factur-x.xml", xml_content.encode("utf-8"))
    
    xmp_xml = f"""<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">
      <pdfaid:part>3</pdfaid:part>
      <pdfaid:conformance>B</pdfaid:conformance>
    </rdf:Description>
    <rdf:Description rdf:about="" xmlns:fx="urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#">
      <fx:DocumentType>INVOICE</fx:DocumentType>
      <fx:DocumentFileName>factur-x.xml</fx:DocumentFileName>
      <fx:Version>1.0</fx:Version>
      <fx:ConformanceLevel>EN 16931</fx:ConformanceLevel>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""

    try:
        metadata_stream = StreamObject()
        metadata_stream._data = xmp_xml.encode("utf-8")
        metadata_stream.update({
            NameObject("/Type"): NameObject("/Metadata"),
            NameObject("/Subtype"): NameObject("/XML")
        })
        xmp_ref = writer._add_object(metadata_stream)
        writer._root_object.update({NameObject("/Metadata"): xmp_ref})
        
        for obj in writer._objects:
            if isinstance(obj, DictionaryObject) and obj.get(NameObject("/Type")) == "/Filespec":
                f_val = obj.get(NameObject("/F"))
                if f_val and str(f_val) == "factur-x.xml":
                    obj.update({NameObject("/AFRelationship"): NameObject("/Data")})
                    af_array = ArrayObject([obj.indirect_reference])
                    writer._root_object.update({NameObject("/AF"): af_array})
                    break
    except Exception as e:
        print(f"XMP-Injection Warnung (übersprungen): {e}")

    ausgabe_datei = os.path.join(ausgabe_ordner, f"Rechnung_{r_nr}.pdf")
    
    with open(ausgabe_datei, "wb") as out_pdf: writer.write(out_pdf)
    
    try:
        if r_datum and r_nr:
            date_obj = datetime.strptime(r_datum, "%Y%m%d")
            journal_filename = f"re{date_obj.strftime('%Y%m')}.csv"
            journal_path = os.path.join(ausgabe_ordner.replace('Rechnungen_PDF', config.get('auswertungen_ordner', 'Auswertungen')), journal_filename)
            
            j_dir = os.path.dirname(journal_path)
            if not os.path.exists(j_dir): os.makedirs(j_dir)
            
            st_19 = steuer_gruppen.get(19.0, {}).get('steuer', 0.0)
            st_7 = steuer_gruppen.get(7.0, {}).get('steuer', 0.0)
            st_0 = steuer_gruppen.get(0.0, {}).get('steuer', 0.0)
            
            file_exists = os.path.exists(journal_path)
            with open(journal_path, 'a', newline='', encoding='utf-8-sig') as f:
                writer_j = csv.writer(f, delimiter=';')
                if not file_exists:
                    writer_j.writerow(["Rechnungsnummer", "Datum", "Empfaenger", "Netto", "MwSt_19", "MwSt_7", "MwSt_0", "Brutto"])
                writer_j.writerow([r_nr, date_obj.strftime("%d.%m.%Y"), kopf.get('KundeName', ''), f"{gesamt_netto:.2f}", f"{st_19:.2f}", f"{st_7:.2f}", f"{st_0:.2f}", f"{gesamt_brutto:.2f}"])
    except Exception as e:
        print(f"Fehler beim Schreiben des Journals: {e}")
        
    return ausgabe_datei

def run_auto_generation(config, logger_callback=None):
    def log(msg):
        if logger_callback: logger_callback(msg)
        else: print(msg)
        
    if not os.path.exists(config['firma_csv']): return log(f"❌ Fehler: '{config['firma_csv']}' fehlt.")
    if not os.path.exists(config['rechnung_csv']): return log(f"❌ Fehler: '{config['rechnung_csv']}' fehlt.")
    if not os.path.exists(config['ausgabe_ordner']): os.makedirs(config['ausgabe_ordner'])

    log("Lese Daten und erstelle ZUGFeRD PDFs...")
    try:
        firma = lade_firma(config['firma_csv'])
        rechnungen = lade_rechnungen(config['rechnung_csv'])
        zusatztexte = lade_zusatz_csv(config['zusatz_csv'])
        gruss = lade_textdatei(config['gruss_csv'])
        header = lade_textdatei(config['header_csv'])
        einleitung = lade_textdatei(config['einleitung_csv'])
        
        for r_nr, daten in rechnungen.items():
            valid, msg = check_lz_logic(daten['kopf'], daten['positionen'])
            if not valid:
                log(f"❌ Fehler bei RE '{r_nr}': {msg}\nWird übersprungen.")
                continue
                
            pfad = erstelle_zugferd_pdf(firma, daten, config['briefbogen_pdf'], zusatztexte, gruss, header, einleitung, config['ausgabe_ordner'])
            log(f"✅ Erstellt: {os.path.basename(pfad)}")
        log("Fertig! Generierung abgeschlossen.")
    except PermissionError:
        log("❌ Zugriff verweigert: Die PDF-Datei ist wahrscheinlich in einem anderen Programm geöffnet. Bitte schließen Sie diese!")
    except Exception as e:
        log(f"❌ Schwerer Fehler bei PDF-Erstellung: {e}")


# ==========================================
# GRAFISCHE BENUTZEROBERFLÄCHE (GUI)
# ==========================================

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self, config, start_in_edit=False):
        super().__init__()
        self.config = config
        self.title("SokoIur eRechnung")
        
        icon_path = get_resource_path("SokoIur.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except Exception: pass
                
        self.geometry(self.config.get("window_geometry", "950x850"))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.bind('<plus>', self.handle_plus_key)
        self.bind('<KP_Add>', self.handle_plus_key)
        self.bind('<Alt-l>', lambda e: self.load_manual_invoice(is_button_click=True))
        self.bind('<Alt-L>', lambda e: self.load_manual_invoice(is_button_click=True))
        self.bind('<Alt-t>', lambda e: self.open_texte_popup())
        self.bind('<Alt-T>', lambda e: self.open_texte_popup())
        self.bind('<Alt-s>', lambda e: self.save_manual_invoice())
        self.bind('<Alt-S>', lambda e: self.save_manual_invoice())
        self.bind('<Alt-p>', lambda e: self.save_generate_open_exit())
        self.bind('<Alt-P>', lambda e: self.save_generate_open_exit())
        
        self.positionen_liste = []
        self.zusatz_dict = {}
        
        self.kunden_liste = lade_kunden(self.config.get("kunden_csv", "kunden.csv"))
        self.produkte_liste = lade_produkte(self.config.get("produkte_csv", "produkte.csv"))
        
        self.header_text = ""
        self.einleitung_text = ""
        self.gruss_text = ""

        if not start_in_edit:
            if self.config.get("keep_header", True):
                self.header_text = lade_textdatei(self.config.get('header_csv', ''))
            else: speichere_textdatei(self.config.get('header_csv', ''), "")
                
            if self.config.get("keep_einleitung", True):
                self.einleitung_text = lade_textdatei(self.config.get('einleitung_csv', ''))
            else: speichere_textdatei(self.config.get('einleitung_csv', ''), "")
                
            if self.config.get("keep_gruss", True):
                self.gruss_text = lade_textdatei(self.config.get('gruss_csv', ''))
            else: speichere_textdatei(self.config.get('gruss_csv', ''), "")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=(20, 5), fill="both", expand=True)
        
        self.tab_gen = self.tabview.add("Generieren")
        self.tab_manuell = self.tabview.add("Manuelle Eingabe")
        self.tab_ausw = self.tabview.add("Auswertungen")
        self.tab_settings = self.tabview.add("Einstellungen")
        self.tab_hilfe = self.tabview.add("Hilfe & Doku")
        
        self.build_generieren_tab()
        self.build_manuell_tab()
        self.build_auswertungen_tab()
        self.build_settings_tab()
        self.build_hilfe_tab()

        self.tabview.set("Manuelle Eingabe")

        if start_in_edit:
            self.after(200, lambda: self.load_manual_invoice(is_button_click=False, silent=True))
            
        def open_website(event): webbrowser.open("https://sokolowski.org")
        lbl_footer = ctk.CTkLabel(self, text="(C) Joachim Sokolowski - https://sokolowski.org", text_color="#1f538d", cursor="hand2")
        lbl_footer.pack(side="bottom", pady=5)
        lbl_footer.bind("<Button-1>", open_website)

    def on_closing(self):
        self.config["window_geometry"] = self.geometry()
        speichere_config(self.config)
        try: os.remove(LOCK_FILE)
        except: pass
        self.destroy()

    def center_window(self, dialog, width, height):
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def handle_plus_key(self, event):
        if self.tabview.get() == "Manuelle Eingabe":
            widget = self.focus_get()
            if widget and widget.winfo_class() in ('Entry', 'Text'): return
            self.open_pos_popup()

    def create_button(self, parent, text, command, **kwargs):
        btn = ctk.CTkButton(parent, text=text, command=command, **kwargs)
        btn.bind('<Return>', lambda e: command())
        btn.bind('<space>', lambda e: command())
        return btn

    def create_input(self, parent, label_text, is_combo=False, combo_values=None, command=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
        
        if is_combo: 
            entry = ctk.CTkComboBox(frame, values=combo_values or [], command=command)
        else: 
            entry = ctk.CTkEntry(frame)
            
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        return entry
        
    def create_input_with_button(self, parent, label_text, btn_text, btn_cmd):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame)
        entry.pack(side="left", fill="x", expand=True, padx=(10, 5))
        btn = self.create_button(frame, text=btn_text, width=40, command=lambda: btn_cmd(entry))
        btn.pack(side="right")
        return entry

    # --- Tab 1: Generieren ---
    def build_generieren_tab(self):
        btn = self.create_button(self.tab_gen, text="PDFs aus CSV generieren", font=("Helvetica", 16, "bold"), height=50, command=self.btn_generieren_click)
        btn.pack(pady=30)
        
        self.log_box = ctk.CTkTextbox(self.tab_gen, width=600, height=300)
        self.log_box.pack(pady=10, padx=20, fill="both", expand=True)
        self.log_box.insert("0.0", "Bereit.\nLaufwerk-Pfade in den Einstellungen prüfen.\n")
        self.log_box.configure(state="disabled")

    def log_to_gui(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.update()

    def btn_generieren_click(self):
        self.log_to_gui("\n--- Starte Generierung ---")
        run_auto_generation(self.config, self.log_to_gui)

    def open_date_picker(self, entry_widget):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Leistungszeitraum wählen")
        self.center_window(dialog, 400, 250)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Datums- oder Zeitraumeingabe", font=("Helvetica", 14, "bold")).pack(pady=10)

        f_start = ctk.CTkFrame(dialog, fg_color="transparent")
        f_start.pack(pady=5)
        ctk.CTkLabel(f_start, text="Startdatum:", width=120).pack(side="left")
        e_start = ctk.CTkEntry(f_start, width=150)
        e_start.pack(side="left")

        f_end = ctk.CTkFrame(dialog, fg_color="transparent")
        f_end.pack(pady=5)
        ctk.CTkLabel(f_end, text="Enddatum (opt.):", width=120).pack(side="left")
        e_end = ctk.CTkEntry(f_end, width=150)
        e_end.pack(side="left")

        existing = entry_widget.get().strip()
        if "|" in existing:
            s, e = existing.split('|')
            e_start.insert(0, s)
            e_end.insert(0, e)
        else:
            e_start.insert(0, existing)

        def fill_today(widget):
            widget.delete(0, 'end')
            widget.insert(0, datetime.now().strftime("%Y-%m-%d"))

        f_btn = ctk.CTkFrame(dialog, fg_color="transparent")
        f_btn.pack(pady=10)
        self.create_button(f_btn, text="Start = Heute", width=110, command=lambda: fill_today(e_start)).pack(side="left", padx=5)
        self.create_button(f_btn, text="Ende = Heute", width=110, command=lambda: fill_today(e_end)).pack(side="left", padx=5)

        def save_date():
            s = parse_flexible_date(e_start.get())
            e = parse_flexible_date(e_end.get())
            try:
                if s: datetime.strptime(s, "%Y-%m-%d")
                if e: datetime.strptime(e, "%Y-%m-%d")
            except ValueError:
                return messagebox.showerror("Fehler", "Datumsformat nicht erkannt!", parent=dialog)
            res = ""
            if s and e: res = f"{s}|{e}"
            elif s: res = s
            elif e: res = e
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, res)
            dialog.destroy()

        self.create_button(dialog, text="Übernehmen", command=save_date).pack(pady=10)

    def choose_and_load_csv(self):
        pfad = filedialog.askopenfilename(
            title="Rechnungs-CSV wählen", 
            filetypes=[("CSV-Dateien", "*.csv*"), ("Alle Dateien", "*.*")]
        )
        if pfad:
            self.load_manual_invoice(is_button_click=True, custom_path=pfad)

    def open_kdnr_search(self, entry_widget):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Kundennummer suchen")
        self.center_window(dialog, 350, 400)
        dialog.transient(self)
        dialog.grab_set()
        
        def get_num(k):
            nr = k.get('KundeNr', '').strip()
            digits = re.sub(r'\D', '', nr)
            return int(digits) if digits else 0
            
        kunden_mit_nr = [k for k in self.kunden_liste if k.get('KundeNr', '').strip()]
        kunden_mit_nr.sort(key=get_num)
        
        if not kunden_mit_nr:
            ctk.CTkLabel(dialog, text="Keine Kunden mit gespeicherter Kundennummer vorhanden.", wraplength=300).pack(pady=20, padx=20)
            self.create_button(dialog, text="Schließen", command=dialog.destroy).pack(pady=10)
            return

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def select_kdnr(kunde):
            self.entry_k_name.set(kunde.get('Name', ''))
            self.entry_k_strasse.delete(0, 'end'); self.entry_k_strasse.insert(0, kunde.get('Strasse', ''))
            self.entry_k_plz_ort.delete(0, 'end'); self.entry_k_plz_ort.insert(0, kunde.get('PLZ_Ort', ''))
            self.entry_k_nr.delete(0, 'end'); self.entry_k_nr.insert(0, kunde.get('KundeNr', ''))
            self.entry_az.delete(0, 'end'); self.entry_az.insert(0, kunde.get('Aktenzeichen', ''))
            dialog.destroy()

        for k in kunden_mit_nr:
            btn_text = f"Nr: {k.get('KundeNr')} - {k.get('Name')}"
            btn = self.create_button(scroll, text=btn_text, anchor="w", command=lambda k_obj=k: select_kdnr(k_obj))
            btn.pack(fill="x", pady=2)

    def update_totals_ui(self):
        g_netto = 0.0
        g_steuer = 0.0
        steuern = {}
        for p in self.positionen_liste:
            m = safe_float(p.get('Menge', 1))
            pr = safe_float(p.get('EinzelpreisNetto', 0))
            st = safe_float(p.get('Steuersatz', 19))
            n = m * pr
            s = n * (st / 100.0)
            g_netto += n
            g_steuer += s
            if st > 0: steuern[st] = steuern.get(st, 0.0) + s
        
        t = f"Netto Gesamt: {f_curr(g_netto)}\n"
        for st, s_wert in sorted(steuern.items()):
            t += f"+ {f_num(st)}% MwSt: {f_curr(s_wert)}\n"
        t += f"Brutto Gesamt: {f_curr(g_netto + g_steuer)}"
        self.lbl_totals.configure(text=t)

    # --- Tab 2: Manuelle Eingabe ---
    def build_manuell_tab(self):
        left_frame = ctk.CTkFrame(self.tab_manuell, width=350)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        right_frame = ctk.CTkFrame(self.tab_manuell)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        btn_load = self.create_button(left_frame, text="📥 Letzte Rechnungs-CSV laden (Alt+L)", command=lambda: self.load_manual_invoice(is_button_click=True), fg_color="#444", hover_color="#666")
        btn_load.pack(pady=(10, 5), padx=10, fill="x")
        
        btn_load_other = self.create_button(left_frame, text="📁 Rechnungs-CSV wählen", command=self.choose_and_load_csv, fg_color="#444", hover_color="#666")
        btn_load_other.pack(pady=(0, 10), padx=10, fill="x")
        
        ctk.CTkLabel(left_frame, text="Kopfdaten", font=("Helvetica", 14, "bold")).pack(pady=5)
        
        self.entry_r_nr = self.create_input(left_frame, "Rechnungs-Nr.")
        self.entry_r_datum = self.create_input(left_frame, "Rechnungsdatum")
        self.entry_f_datum = self.create_input(left_frame, "Fälligkeit")
        
        self.chk_raten = ctk.CTkCheckBox(left_frame, text="Ratenzahlung zulassen")
        self.chk_raten.pack(pady=3, padx=10, anchor="w")
        if self.config.get("keep_raten", False): self.chk_raten.select()
        
        self.entry_k_nr = self.create_input_with_button(left_frame, "Kunden-Nr. (opt.)", "🔍", self.open_kdnr_search)
        self.entry_az = self.create_input(left_frame, "Aktenzeichen (opt.)")
        self.entry_lz_kopf = self.create_input_with_button(left_frame, "Lz. Kopf (opt.)", "📅", self.open_date_picker)
        
        kunden_namen = [k['Name'] for k in self.kunden_liste]
        def kunden_auswahl(wahl):
            for k in self.kunden_liste:
                if k['Name'] == wahl:
                    self.entry_k_strasse.delete(0, 'end'); self.entry_k_strasse.insert(0, k.get('Strasse', ''))
                    self.entry_k_plz_ort.delete(0, 'end'); self.entry_k_plz_ort.insert(0, k.get('PLZ_Ort', ''))
                    self.entry_k_nr.delete(0, 'end'); self.entry_k_nr.insert(0, k.get('KundeNr', ''))
                    self.entry_az.delete(0, 'end'); self.entry_az.insert(0, k.get('Aktenzeichen', ''))
                    break

        self.entry_k_name = self.create_input(left_frame, "Kunde Name", is_combo=True, combo_values=kunden_namen, command=kunden_auswahl)
        self.entry_k_name.set("")
        
        self.entry_k_strasse = self.create_input(left_frame, "Kunde Straße")
        self.entry_k_plz_ort = self.create_input(left_frame, "PLZ Ort")
        
        self.chk_kunde_speichern = ctk.CTkCheckBox(left_frame, text="Kunde speichern/updaten")
        self.chk_kunde_speichern.pack(pady=3, padx=10, anchor="w")
        if self.config.get("keep_kunde_speichern", False): self.chk_kunde_speichern.select()
        
        btn_texte = self.create_button(left_frame, text="📝 Texte bearbeiten (Alt+T)", command=self.open_texte_popup)
        btn_texte.pack(pady=15, padx=10, fill="x")
        
        ctk.CTkFrame(left_frame, height=2, fg_color="#555").pack(fill="x", pady=10, padx=10)
        self.lbl_totals = ctk.CTkLabel(left_frame, text="Netto Gesamt: 0,00 €\nBrutto Gesamt: 0,00 €", justify="left", font=("Helvetica", 14, "bold"))
        self.lbl_totals.pack(pady=5, padx=15, anchor="w")
        
        heute = datetime.now()
        try: tage = int(self.config.get("faelligkeit_tage", "29"))
        except ValueError: tage = 29
            
        self.entry_r_datum.insert(0, heute.strftime('%Y-%m-%d'))
        self.entry_f_datum.insert(0, (heute + timedelta(days=tage)).strftime('%Y-%m-%d'))
        self.entry_r_nr.insert(0, berechne_naechste_rechnungsnummer(self.config.get("letzte_rechnungsnummer", "")))
        
        ctk.CTkLabel(right_frame, text="Positionen", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        self.pos_scroll = ctk.CTkScrollableFrame(right_frame)
        self.pos_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_add = self.create_button(right_frame, text="+ Position hinzufügen (+)", command=self.open_pos_popup)
        btn_add.pack(pady=10)
        
        btn_save = self.create_button(right_frame, text="Nur Speichern [CSV] (Alt+S)", fg_color="green", hover_color="darkgreen", command=self.save_manual_invoice)
        btn_save.pack(pady=5, fill="x", padx=20)
        
        btn_gen = self.create_button(right_frame, text="Speichern, PDF erstellen & öffnen (Alt+P)", fg_color="#b85c00", hover_color="#8f4700", command=self.save_generate_open_exit)
        btn_gen.pack(pady=5, fill="x", padx=20)

    def load_manual_invoice(self, is_button_click=False, silent=False, custom_path=None):
        rech_pfad = custom_path if custom_path else self.config.get('rechnung_csv', '')
        if not os.path.exists(rech_pfad): 
            if not silent: messagebox.showwarning("Fehler", f"Datei {rech_pfad} nicht gefunden.")
            return
        
        try:
            with open(rech_pfad, mode='r', encoding='utf-8-sig') as f:
                reader = list(csv.DictReader(f, delimiter=';'))
                if not reader: 
                    if not silent: messagebox.showwarning("Fehler", "Die CSV-Datei ist leer.")
                    return
                
                kopf = reader[0]
                
                geladene_nr = kopf.get('Rechnungsnummer', '')
                ziel_nr = geladene_nr
                if is_button_click and geladene_nr:
                    antwort = messagebox.askyesno("Rechnungsnummer", f"Die Rechnungsnummer {geladene_nr} wurde aus der Datei geladen.\n\nSoll diese Nummer für eine neue Rechnung um eins erhöht werden (Ja)\noder exakt beibehalten werden (Nein)?")
                    if antwort: 
                        ziel_nr = berechne_naechste_rechnungsnummer(geladene_nr)
                        
                self.entry_r_nr.delete(0, 'end'); self.entry_r_nr.insert(0, ziel_nr)
                
                self.entry_r_datum.delete(0, 'end'); self.entry_r_datum.insert(0, kopf.get('Rechnungsdatum', ''))
                self.entry_f_datum.delete(0, 'end'); self.entry_f_datum.insert(0, kopf.get('Faelligkeitsdatum', ''))
                
                self.entry_k_name.set(kopf.get('KundeName', ''))
                self.entry_k_strasse.delete(0, 'end'); self.entry_k_strasse.insert(0, kopf.get('KundeStrasse', ''))
                
                if str(kopf.get('Ratenzahlung', '')).lower() in ['true', '1', 'ja', 'yes']: self.chk_raten.select()
                else: self.chk_raten.deselect()
                
                self.entry_k_nr.delete(0, 'end'); self.entry_k_nr.insert(0, kopf.get('KundeNr', ''))
                self.entry_az.delete(0, 'end'); self.entry_az.insert(0, kopf.get('Aktenzeichen', ''))
                self.entry_lz_kopf.delete(0, 'end'); self.entry_lz_kopf.insert(0, kopf.get('LeistungszeitraumKopf', ''))
                
                plz_ort = f"{kopf.get('KundePLZ', '')} {kopf.get('KundeOrt', '')}".strip()
                self.entry_k_plz_ort.delete(0, 'end'); self.entry_k_plz_ort.insert(0, plz_ort)
                
                self.positionen_liste = []
                for row in reader: self.positionen_liste.append(row)
            
            zusatz_pfad = self.config.get('zusatz_csv', '')
            self.zusatz_dict = {}
            if os.path.exists(zusatz_pfad):
                with open(zusatz_pfad, mode='r', encoding='utf-8-sig') as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        parts = line.split(';', 1)
                        if len(parts) == 2:
                            pos_keys = parts[0].strip().split(',')
                            text_val = parts[1].strip()
                            for pk in pos_keys: self.zusatz_dict[pk.strip()] = text_val
            
            self.header_text = lade_textdatei(self.config.get('header_csv', ''))
            self.einleitung_text = lade_textdatei(self.config.get('einleitung_csv', ''))
            self.gruss_text = lade_textdatei(self.config.get('gruss_csv', ''))
            
            self.refresh_pos_list()
        except Exception as e:
            if not silent: messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")

    def open_texte_popup(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Optionale Texte bearbeiten")
        self.center_window(dialog, 600, 600)
        dialog.transient(self)
        dialog.grab_set() 
        
        ctk.CTkLabel(dialog, text="Zentrierter Header (über der Rechnungs-Nummer):").pack(anchor="w", padx=20, pady=(10, 0))
        t_head = ctk.CTkTextbox(dialog, height=60)
        t_head.pack(fill="x", padx=20, pady=2)
        t_head.insert("0.0", self.header_text)
        chk_head = ctk.CTkCheckBox(dialog, text="Text für nächste neue Rechnung merken")
        chk_head.pack(anchor="w", padx=20, pady=(0, 10))
        if self.config.get("keep_header", True): chk_head.select()
        else: chk_head.deselect()
        
        ctk.CTkLabel(dialog, text="Einleitung (vor den Positionen):").pack(anchor="w", padx=20, pady=(5, 0))
        t_einl = ctk.CTkTextbox(dialog, height=80)
        t_einl.pack(fill="x", padx=20, pady=2)
        t_einl.insert("0.0", self.einleitung_text)
        chk_einl = ctk.CTkCheckBox(dialog, text="Text für nächste neue Rechnung merken")
        chk_einl.pack(anchor="w", padx=20, pady=(0, 10))
        if self.config.get("keep_einleitung", True): chk_einl.select()
        else: chk_einl.deselect()
        
        ctk.CTkLabel(dialog, text="Gruß (ganz unten):").pack(anchor="w", padx=20, pady=(5, 0))
        t_gruss = ctk.CTkTextbox(dialog, height=80)
        t_gruss.pack(fill="x", padx=20, pady=2)
        t_gruss.insert("0.0", self.gruss_text)
        chk_gruss = ctk.CTkCheckBox(dialog, text="Text für nächste neue Rechnung merken")
        chk_gruss.pack(anchor="w", padx=20, pady=(0, 10))
        if self.config.get("keep_gruss", True): chk_gruss.select()
        else: chk_gruss.deselect()
        
        def save_texte():
            self.header_text = t_head.get("0.0", "end").strip()
            self.einleitung_text = t_einl.get("0.0", "end").strip()
            self.gruss_text = t_gruss.get("0.0", "end").strip()
            
            self.config["keep_header"] = bool(chk_head.get())
            self.config["keep_einleitung"] = bool(chk_einl.get())
            self.config["keep_gruss"] = bool(chk_gruss.get())
            speichere_config(self.config)
            dialog.destroy()
            
        self.create_button(dialog, text="Übernehmen", command=save_texte).pack(pady=20)

    def open_pos_popup(self, edit_index=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Position bearbeiten" if edit_index is not None else "Neue Position (Enter zum Speichern)")
        self.center_window(dialog, 600, 390)
        dialog.transient(self)
        dialog.grab_set() 
        
        prod_namen = [p['Bezeichnung'] for p in self.produkte_liste]
        
        def prod_auswahl(wahl):
            for p in self.produkte_liste:
                if p['Bezeichnung'] == wahl:
                    e_menge.delete(0, 'end'); e_menge.insert(0, p.get('Menge', '1'))
                    e_preis.delete(0, 'end'); e_preis.insert(0, p.get('EinzelpreisNetto', '0'))
                    e_steuer.delete(0, 'end'); e_steuer.insert(0, p.get('Steuersatz', '19'))
                    
                    code = p.get('Einheit', 'C62')
                    lesbar = EINHEITEN_MAPPING.get(code, code)
                    for val in EINHEITEN_LISTE:
                        if code in val or lesbar in val:
                            e_einheit.set(val)
                            break
                    break

        e_bez = self.create_input(dialog, "Bezeichnung", is_combo=True, combo_values=prod_namen, command=prod_auswahl)
        e_menge = self.create_input(dialog, "Menge")
        e_einheit = self.create_input(dialog, "Einheit", is_combo=True, combo_values=EINHEITEN_LISTE)
        e_preis = self.create_input(dialog, "Einzelpreis (€)")
        e_steuer = self.create_input(dialog, "Steuer (%)")
        
        e_lz_pos = self.create_input_with_button(dialog, "Lz. Position (opt.)", "📅", self.open_date_picker)
        
        existing_notes = list(set([v.replace('~cr', '\\n') for k, v in self.zusatz_dict.items() if k != '0']))
        existing_notes.insert(0, "")
        e_anmerkung = self.create_input(dialog, "Anmerkung", is_combo=True, combo_values=existing_notes)
        
        if edit_index is None:
            e_menge.insert(0, "1")
            e_einheit.set(self.config.get("letzte_einheit", "Stück (C62)"))
            e_steuer.insert(0, "19")
            e_anmerkung.set("")
            e_bez.set("")
        else:
            p = self.positionen_liste[edit_index]
            e_bez.set(p.get('Bezeichnung', ''))
            e_menge.insert(0, f"{safe_float(p.get('Menge', 1)):g}")
            
            code = p.get('Einheit', 'C62')
            lesbar = EINHEITEN_MAPPING.get(code, code)
            for val in EINHEITEN_LISTE:
                if code in val or lesbar in val:
                    e_einheit.set(val)
                    break
                    
            e_preis.insert(0, p.get('EinzelpreisNetto', ''))
            e_steuer.insert(0, p.get('Steuersatz', '19'))
            e_lz_pos.insert(0, p.get('LeistungszeitraumPos', ''))
            
            pos_nr = p.get('PosNr')
            anm = self.zusatz_dict.get(pos_nr, "").replace('~cr', '\\n')
            e_anmerkung.set(anm)
            
        e_bez.focus_set()
        
        def save_it(event=None):
            if not e_bez.get(): return messagebox.showwarning("Fehler", "Bezeichnung fehlt!")
            
            try:
                float(e_menge.get().replace(',', '.') or "1")
                float(e_preis.get().replace(',', '.'))
                float(e_steuer.get().replace(',', '.') or "19")
            except ValueError:
                return messagebox.showwarning("Eingabefehler", "Menge, Einzelpreis und Steuer müssen gültige Zahlen sein!")
                
            lz_pos_val = parse_flexible_date_span(e_lz_pos.get())
            if lz_pos_val:
                try:
                    for part in lz_pos_val.split('|'):
                        if part: datetime.strptime(part, "%Y-%m-%d")
                except ValueError:
                    return messagebox.showwarning("Datums-Fehler", "Der Leistungszeitraum hat ein ungültiges Format!")
            
            einheit_val = e_einheit.get()
            match = re.search(r'\((.*?)\)', einheit_val)
            einheit_code = match.group(1).strip() if match else einheit_val.strip()
            
            self.config["letzte_einheit"] = einheit_val
            speichere_config(self.config)
            
            pos_nr = str(edit_index + 1) if edit_index is not None else str(len(self.positionen_liste) + 1)
            
            new_data = {
                'PosNr': pos_nr, 'Menge': e_menge.get() or "1", 'Einheit': einheit_code,
                'Bezeichnung': e_bez.get(), 'EinzelpreisNetto': e_preis.get().replace(',','.'),
                'Steuersatz': e_steuer.get() or "19",
                'LeistungszeitraumPos': lz_pos_val
            }
            
            if edit_index is not None: self.positionen_liste[edit_index] = new_data
            else: self.positionen_liste.append(new_data)
                
            anmerkung_text = e_anmerkung.get().strip()
            if anmerkung_text: self.zusatz_dict[pos_nr] = anmerkung_text.replace('\\n', '~cr')
            else:
                if pos_nr in self.zusatz_dict: del self.zusatz_dict[pos_nr]
                
            self.refresh_pos_list()
            dialog.destroy()
            
        btn_hinzu = self.create_button(dialog, text="Speichern", command=save_it)
        btn_hinzu.pack(pady=15)
        
        dialog.bind('<Return>', save_it)

    def delete_pos(self, index):
        if messagebox.askyesno("Löschen", "Möchten Sie die Position wirklich löschen?"):
            del self.positionen_liste[index]
            
            new_zusatz = {}
            if '0' in self.zusatz_dict: new_zusatz['0'] = self.zusatz_dict['0']
                
            for i, p in enumerate(self.positionen_liste):
                old_nr = p['PosNr']
                new_nr = str(i + 1)
                p['PosNr'] = new_nr
                if old_nr in self.zusatz_dict: new_zusatz[new_nr] = self.zusatz_dict[old_nr]
                    
            self.zusatz_dict = new_zusatz
            self.refresh_pos_list()

    def refresh_pos_list(self):
        for widget in self.pos_scroll.winfo_children(): widget.destroy()
        for idx, p in enumerate(self.positionen_liste):
            f = ctk.CTkFrame(self.pos_scroll)
            f.pack(fill="x", pady=2)
            
            btn_del = self.create_button(f, text="🗑", width=30, fg_color="#b30000", hover_color="#800000", command=lambda i=idx: self.delete_pos(i))
            btn_del.pack(side="right", padx=5, pady=5)
            
            btn_edit = self.create_button(f, text="✎", width=30, fg_color="#555", hover_color="#777", command=lambda i=idx: self.open_pos_popup(i))
            btn_edit.pack(side="right", padx=5, pady=5)
            
            code = p.get('Einheit', 'C62')
            lesbar = EINHEITEN_MAPPING.get(code, code)
            menge = safe_float(p.get('Menge', 1))
            bez = p.get('Bezeichnung', '')
            if len(bez) > 40: bez = bez[:37] + "..."
            
            lbl_text = f"[{p.get('PosNr', '')}] {bez} | {f_num(menge)} {lesbar} | {f_curr(safe_float(p.get('EinzelpreisNetto', 0)))}"
            ctk.CTkLabel(f, text=lbl_text, anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=5)
            
        self.update_totals_ui()

    def save_manual_invoice(self, silent=False):
        if not self.positionen_liste: 
            messagebox.showwarning("Fehler", "Bitte erfassen Sie zunächst Positionen!")
            return False
            
        r_datum = parse_flexible_date(self.entry_r_datum.get())
        f_datum = parse_flexible_date(self.entry_f_datum.get())
        lz_kopf = parse_flexible_date_span(self.entry_lz_kopf.get())
        
        try:
            datetime.strptime(r_datum, "%Y-%m-%d")
            datetime.strptime(f_datum, "%Y-%m-%d")
            if lz_kopf:
                for part in lz_kopf.split('|'):
                    if part: datetime.strptime(part, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Datums-Fehler", "Bitte überprüfen Sie die Datumsangaben in den Kopfdaten!")
            return False
            
        self.entry_r_datum.delete(0, 'end'); self.entry_r_datum.insert(0, r_datum)
        self.entry_f_datum.delete(0, 'end'); self.entry_f_datum.insert(0, f_datum)
        self.entry_lz_kopf.delete(0, 'end'); self.entry_lz_kopf.insert(0, lz_kopf)
        
        r_nr = self.entry_r_nr.get()
        plz_ort = self.entry_k_plz_ort.get().split(' ', 1)
        plz = plz_ort[0] if len(plz_ort) > 0 else ""
        ort = plz_ort[1] if len(plz_ort) > 1 else ""
        
        full_positions = []
        for p in self.positionen_liste:
            p_copy = p.copy()
            p_copy.update({
                'Rechnungsnummer': r_nr, 'Rechnungsdatum': r_datum,
                'Faelligkeitsdatum': f_datum, 'KundeName': self.entry_k_name.get(),
                'KundeStrasse': self.entry_k_strasse.get(), 'KundePLZ': plz, 'KundeOrt': ort,
                'KundeLand': 'DE', 'Zusatztext': '',
                'KundeNr': self.entry_k_nr.get().strip(),
                'Aktenzeichen': self.entry_az.get().strip(),
                'LeistungszeitraumKopf': lz_kopf,
                'Ratenzahlung': str(bool(self.chk_raten.get()))
            })
            full_positions.append(p_copy)
            
        fieldnames = ['Rechnungsnummer', 'Rechnungsdatum', 'Faelligkeitsdatum', 'KundeName', 
                      'KundeStrasse', 'KundePLZ', 'KundeOrt', 'KundeLand', 'KundeNr', 'Aktenzeichen', 
                      'LeistungszeitraumKopf', 'Ratenzahlung', 'PosNr', 'Menge', 'Einheit', 'Bezeichnung', 
                      'EinzelpreisNetto', 'Steuersatz', 'Zusatztext', 'LeistungszeitraumPos']
        try:
            with open(self.config['rechnung_csv'], 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                for p in full_positions: writer.writerow(p)
                
            with open(self.config['zusatz_csv'], 'w', encoding='utf-8-sig') as f:
                text_to_pos = {}
                for k, v in self.zusatz_dict.items():
                    if k == '0': continue
                    if v not in text_to_pos: text_to_pos[v] = []
                    text_to_pos[v].append(int(k))
                    
                if '0' in self.zusatz_dict: f.write(f"0;{self.zusatz_dict['0']}\n")
                    
                for text, pos_list in text_to_pos.items():
                    pos_list.sort()
                    pos_str = ",".join(map(str, pos_list))
                    f.write(f"{pos_str};{text}\n")
                    
            speichere_textdatei(self.config.get('header_csv'), self.header_text)
            speichere_textdatei(self.config.get('einleitung_csv'), self.einleitung_text)
            speichere_textdatei(self.config.get('gruss_csv'), self.gruss_text)
            
            if self.chk_kunde_speichern.get():
                k_daten = {
                    'Name': self.entry_k_name.get().strip(),
                    'Strasse': self.entry_k_strasse.get().strip(),
                    'PLZ_Ort': self.entry_k_plz_ort.get().strip(),
                    'Land': 'DE',
                    'KundeNr': self.entry_k_nr.get().strip(),
                    'Aktenzeichen': self.entry_az.get().strip()
                }
                if k_daten['Name']:
                    pfad_k = self.config.get("kunden_csv", "kunden.csv")
                    speichere_kunde(pfad_k, k_daten)
                    self.kunden_liste = lade_kunden(pfad_k)
                    self.entry_k_name.configure(values=[k['Name'] for k in self.kunden_liste])
                
            self.config['letzte_rechnungsnummer'] = r_nr
            # Config Zustand merken
            self.config['keep_raten'] = bool(self.chk_raten.get())
            self.config['keep_kunde_speichern'] = bool(self.chk_kunde_speichern.get())
            speichere_config(self.config)
            
            if not silent: messagebox.showinfo("Erfolg", "Ihre Daten wurden erfolgreich gespeichert!")
            return True
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
            return False

    def save_generate_open_exit(self):
        if not self.positionen_liste: 
            return messagebox.showwarning("Fehler", "Bitte erfassen Sie zunächst Positionen!")
            
        lz_kopf = self.entry_lz_kopf.get().strip()
        kopf_simuliert = {'LeistungszeitraumKopf': parse_flexible_date_span(lz_kopf)}
        
        pos_simuliert = []
        for p in self.positionen_liste:
            pos_simuliert.append({'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')})
            
        valid, lz_msg = check_lz_logic(kopf_simuliert, pos_simuliert)
        if not valid:
            return messagebox.showwarning("Prüfung fehlgeschlagen", lz_msg)
            
        erfolg = self.save_manual_invoice(silent=True)
        if not erfolg: return
        
        generierungs_fehler = []
        def catch_log(msg):
            if "❌" in msg: generierungs_fehler.append(msg)
            print(msg)
            
        run_auto_generation(self.config, logger_callback=catch_log)
        
        if generierungs_fehler:
            fehlertext = "\n".join(generierungs_fehler)
            if "Zugriff verweigert" in fehlertext or "PermissionError" in fehlertext:
                messagebox.showerror("Zugriff verweigert!", "Die PDF-Datei konnte nicht aktualisiert werden, da sie höchstwahrscheinlich in Ihrem Adobe Reader (oder einem anderen Programm) noch geöffnet ist.\n\nBitte schließen Sie die alte PDF-Datei und klicken Sie erneut auf Speichern/Generieren!")
            else:
                messagebox.showerror("Fehler bei der PDF-Erstellung", fehlertext)
            return 
        
        r_nr = self.entry_r_nr.get()
        pdf_pfad = os.path.join(self.config['ausgabe_ordner'], f"Rechnung_{r_nr}.pdf")
        
        if os.path.exists(pdf_pfad):
            try: os.startfile(pdf_pfad)
            except Exception as e: messagebox.showwarning("Hinweis", f"Das PDF wurde erstellt, konnte aber nicht automatisch geöffnet werden: {e}")
            self.on_closing()
        else:
            messagebox.showerror("Fehler", "Das PDF wurde aus unbekannten Gründen nicht erstellt.")

    # --- Tab Auswertungen ---
    def build_auswertungen_tab(self):
        f = ctk.CTkFrame(self.tab_ausw)
        f.pack(pady=30, padx=20, fill="x")
        
        ctk.CTkLabel(f, text="Auswertungen generieren (Journal)", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        f_input = ctk.CTkFrame(f, fg_color="transparent")
        f_input.pack(pady=10)
        
        ctk.CTkLabel(f_input, text="Monat (z.B. 11.2026) oder Jahr (2026):", width=250).pack(side="left")
        self.entry_ausw_zeit = ctk.CTkEntry(f_input, width=150)
        self.entry_ausw_zeit.pack(side="left", padx=10)
        self.entry_ausw_zeit.insert(0, datetime.now().strftime("%m.%Y"))
        
        self.create_button(f, text="Journal als PDF erzeugen & öffnen", command=self.generate_auswertung, fg_color="#b85c00", hover_color="#8f4700").pack(pady=20)

    def generate_auswertung(self):
        zeit_str = self.entry_ausw_zeit.get().strip()
        ordner = self.config.get("auswertungen_ordner", "Auswertungen")
        if not os.path.exists(ordner):
            return messagebox.showwarning("Fehler", "Der Auswertungs-Ordner existiert noch nicht.")
            
        such_muster = []
        if re.match(r'^\d{4}$', zeit_str):
            for m in range(1, 13):
                such_muster.append(f"re{zeit_str}{m:02d}.csv")
        elif re.match(r'^\d{2}\.\d{4}$', zeit_str):
            m, y = zeit_str.split('.')
            such_muster.append(f"re{y}{m}.csv")
        else:
            return messagebox.showwarning("Fehler", "Bitte Format MM.YYYY (z.B. 11.2026) oder YYYY eingeben.")
            
        gefundene_rechnungen = []
        for datei in such_muster:
            pfad = os.path.join(ordner, datei)
            if os.path.exists(pfad):
                with open(pfad, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        gefundene_rechnungen.append(row)
                        
        if not gefundene_rechnungen:
            return messagebox.showinfo("Info", f"Für {zeit_str} wurden keine Rechnungsdaten gefunden.")
            
        pdf_name = f"Journal_{zeit_str.replace('.','_')}.pdf"
        pdf_pfad = os.path.join(ordner, pdf_name)
        
        c = canvas.Canvas(pdf_pfad, pagesize=landscape(A4))
        breite, hoehe = landscape(A4)
        
        def neuer_kopf(c_obj):
            c_obj.setFont("Helvetica-Bold", 16)
            c_obj.drawString(40, hoehe - 50, f"Rechnungsjournal - {zeit_str}")
            c_obj.setFont("Helvetica-Bold", 10)
            c_obj.drawString(40, hoehe - 80, "Datum")
            c_obj.drawString(100, hoehe - 80, "Rechnungs-Nr.")
            c_obj.drawString(220, hoehe - 80, "Empfänger")
            c_obj.drawRightString(500, hoehe - 80, "Netto")
            c_obj.drawRightString(580, hoehe - 80, "MwSt 19%")
            c_obj.drawRightString(660, hoehe - 80, "MwSt 7%")
            c_obj.drawRightString(740, hoehe - 80, "MwSt 0%")
            c_obj.drawRightString(820, hoehe - 80, "Brutto")
            c_obj.line(40, hoehe - 85, 820, hoehe - 85)
            return hoehe - 105
            
        y = neuer_kopf(c)
        c.setFont("Helvetica", 10)
        
        sum_netto = sum_19 = sum_7 = sum_0 = sum_brutto = 0.0
        
        for r in gefundene_rechnungen:
            if y < 50:
                c.showPage()
                y = neuer_kopf(c)
                c.setFont("Helvetica", 10)
                
            n = safe_float(r.get('Netto', 0))
            m19 = safe_float(r.get('MwSt_19', 0))
            m7 = safe_float(r.get('MwSt_7', 0))
            m0 = safe_float(r.get('MwSt_0', 0))
            b = safe_float(r.get('Brutto', 0))
            
            sum_netto += n; sum_19 += m19; sum_7 += m7; sum_0 += m0; sum_brutto += b
            
            c.drawString(40, y, r.get('Datum', ''))
            c.drawString(100, y, r.get('Rechnungsnummer', ''))
            
            empf = r.get('Empfaenger', '')
            if len(empf) > 25: empf = empf[:22] + "..."
            c.drawString(220, y, empf)
            
            c.drawRightString(500, y, f_curr(n))
            c.drawRightString(580, y, f_curr(m19))
            c.drawRightString(660, y, f_curr(m7))
            c.drawRightString(740, y, f_curr(m0))
            c.drawRightString(820, y, f_curr(b))
            y -= 15
            
        c.line(40, y + 10, 820, y + 10)
        y -= 10
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "GESAMTSUMMEN:")
        c.drawRightString(500, y, f_curr(sum_netto))
        c.drawRightString(580, y, f_curr(sum_19))
        c.drawRightString(660, y, f_curr(sum_7))
        c.drawRightString(740, y, f_curr(sum_0))
        c.drawRightString(820, y, f_curr(sum_brutto))
        
        c.save()
        
        try: os.startfile(pdf_pfad)
        except: messagebox.showinfo("Fertig", f"Journal erstellt: {pdf_pfad}")

    # --- Tab 3: Einstellungen ---
    def build_settings_tab(self):
        self.path_vars = {}
        for key, val in self.config.items():
            if key in ["letzte_rechnungsnummer", "window_geometry", "letzte_einheit", "keep_header", "keep_einleitung", "keep_gruss", "terms_accepted", "keep_raten", "keep_kunde_speichern"]: continue
            f = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
            f.pack(fill="x", pady=2, padx=20)
            ctk.CTkLabel(f, text=key, width=150, anchor="w").pack(side="left")
            
            entry = ctk.CTkEntry(f, width=400)
            entry.insert(0, val)
            entry.pack(side="left", padx=10, fill="x", expand=True)
            self.path_vars[key] = entry
            
            if "csv" in key or "pdf" in key or "ordner" in key:
                self.create_button(f, text="📂", width=40, command=lambda k=key, e=entry: self.browse_path(k, e)).pack(side="left")
            
        self.create_button(self.tab_settings, text="Einstellungen Speichern", command=self.save_settings).pack(pady=10)
        
        f_stammdaten = ctk.CTkFrame(self.tab_settings)
        f_stammdaten.pack(fill="x", pady=15, padx=20)
        ctk.CTkLabel(f_stammdaten, text="Stammdaten verwalten", font=("Helvetica", 14, "bold")).pack(pady=5)
        
        f_btns = ctk.CTkFrame(f_stammdaten, fg_color="transparent")
        f_btns.pack(pady=10)
        self.create_button(f_btns, text="👥 Kundendaten verwalten", command=self.open_kunden_manager).pack(side="left", padx=10)
        self.create_button(f_btns, text="📦 Produktdaten verwalten", command=self.open_produkte_manager).pack(side="left", padx=10)

    def browse_path(self, key, entry_widget):
        path = filedialog.askdirectory() if "ordner" in key else filedialog.askopenfilename(filetypes=[("Datei", "*.pdf" if "pdf" in key else "*.csv")])
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    def save_settings(self):
        for key, entry in self.path_vars.items():
            if key == "faelligkeit_tage":
                try: int(entry.get())
                except ValueError: return messagebox.showerror("Fehler", "Die Fälligkeit (Tage) muss eine gültige Zahl sein!")
            self.config[key] = entry.get()
            
        speichere_config(self.config)
        messagebox.showinfo("Gespeichert", "Ihre Einstellungen wurden erfolgreich gespeichert!")

    # --- DATENBANK-MANAGER (KUNDEN) ---
    def open_kunden_manager(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Kundendaten verwalten")
        self.center_window(dialog, 700, 500)
        dialog.transient(self)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def refresh():
            for w in scroll.winfo_children(): w.destroy()
            for idx, k in enumerate(self.kunden_liste):
                f = ctk.CTkFrame(scroll)
                f.pack(fill="x", pady=2)
                btn_del = self.create_button(f, text="🗑", width=30, fg_color="#b30000", hover_color="#800000", command=lambda i=idx: delete_k(i))
                btn_del.pack(side="right", padx=5, pady=5)
                btn_edit = self.create_button(f, text="✎", width=30, fg_color="#555", hover_color="#777", command=lambda i=idx: edit_k(i))
                btn_edit.pack(side="right", padx=5, pady=5)
                lbl = ctk.CTkLabel(f, text=f"{k.get('Name','')} | {k.get('PLZ_Ort','')}", anchor="w")
                lbl.pack(side="left", padx=10, fill="x", expand=True)

        def delete_k(index):
            if messagebox.askyesno("Löschen", "Kunde wirklich löschen?", parent=dialog):
                del self.kunden_liste[index]
                speichere_alle_kunden(self.config.get("kunden_csv", "kunden.csv"), self.kunden_liste)
                self.entry_k_name.configure(values=[k['Name'] for k in self.kunden_liste])
                refresh()

        def edit_k(index=None):
            d_edit = ctk.CTkToplevel(dialog)
            d_edit.title("Kunde bearbeiten" if index is not None else "Neuer Kunde")
            self.center_window(d_edit, 500, 350)
            d_edit.transient(dialog)
            d_edit.grab_set()
            
            e_name = self.create_input(d_edit, "Name")
            e_str = self.create_input(d_edit, "Straße")
            e_plz = self.create_input(d_edit, "PLZ Ort")
            e_nr = self.create_input(d_edit, "Kunden-Nr.")
            e_az = self.create_input(d_edit, "Aktenzeichen")
            
            if index is not None:
                k = self.kunden_liste[index]
                e_name.insert(0, k.get('Name',''))
                e_str.insert(0, k.get('Strasse',''))
                e_plz.insert(0, k.get('PLZ_Ort',''))
                e_nr.insert(0, k.get('KundeNr',''))
                e_az.insert(0, k.get('Aktenzeichen',''))
                
            def save():
                if not e_name.get().strip(): return messagebox.showwarning("Fehler", "Name darf nicht leer sein!", parent=d_edit)
                neu = {
                    'Name': e_name.get().strip(), 'Strasse': e_str.get().strip(),
                    'PLZ_Ort': e_plz.get().strip(), 'Land': 'DE',
                    'KundeNr': e_nr.get().strip(), 'Aktenzeichen': e_az.get().strip()
                }
                if index is not None: self.kunden_liste[index] = neu
                else: self.kunden_liste.append(neu)
                    
                speichere_alle_kunden(self.config.get("kunden_csv", "kunden.csv"), self.kunden_liste)
                self.entry_k_name.configure(values=[k['Name'] for k in self.kunden_liste])
                refresh()
                d_edit.destroy()
                
            self.create_button(d_edit, text="Speichern", command=save).pack(pady=20)

        self.create_button(dialog, text="+ Neuen Kunden anlegen", command=lambda: edit_k()).pack(pady=10)
        refresh()

    # --- DATENBANK-MANAGER (PRODUKTE) ---
    def open_produkte_manager(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Produktdaten verwalten")
        self.center_window(dialog, 700, 500)
        dialog.transient(self)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def refresh():
            for w in scroll.winfo_children(): w.destroy()
            for idx, p in enumerate(self.produkte_liste):
                f = ctk.CTkFrame(scroll)
                f.pack(fill="x", pady=2)
                btn_del = self.create_button(f, text="🗑", width=30, fg_color="#b30000", hover_color="#800000", command=lambda i=idx: delete_p(i))
                btn_del.pack(side="right", padx=5, pady=5)
                btn_edit = self.create_button(f, text="✎", width=30, fg_color="#555", hover_color="#777", command=lambda i=idx: edit_p(i))
                btn_edit.pack(side="right", padx=5, pady=5)
                lbl = ctk.CTkLabel(f, text=f"{p.get('Bezeichnung','')} | {p.get('EinzelpreisNetto','0')}€ | {p.get('Steuersatz','19')}%", anchor="w")
                lbl.pack(side="left", padx=10, fill="x", expand=True)

        def delete_p(index):
            if messagebox.askyesno("Löschen", "Produkt wirklich löschen?", parent=dialog):
                del self.produkte_liste[index]
                speichere_alle_produkte(self.config.get("produkte_csv", "produkte.csv"), self.produkte_liste)
                refresh()

        def edit_p(index=None):
            d_edit = ctk.CTkToplevel(dialog)
            d_edit.title("Produkt bearbeiten" if index is not None else "Neues Produkt")
            self.center_window(d_edit, 500, 350)
            d_edit.transient(dialog)
            d_edit.grab_set()
            
            e_bez = self.create_input(d_edit, "Bezeichnung")
            e_menge = self.create_input(d_edit, "Standard-Menge")
            e_einheit = self.create_input(d_edit, "Einheit", is_combo=True, combo_values=EINHEITEN_LISTE)
            e_preis = self.create_input(d_edit, "Einzelpreis (€)")
            e_steuer = self.create_input(d_edit, "Steuer (%)")
            
            if index is not None:
                p = self.produkte_liste[index]
                e_bez.insert(0, p.get('Bezeichnung',''))
                e_menge.insert(0, f"{safe_float(p.get('Menge',1)):g}")
                e_preis.insert(0, p.get('EinzelpreisNetto',''))
                e_steuer.insert(0, p.get('Steuersatz','19'))
                code = p.get('Einheit', 'C62')
                lesbar = EINHEITEN_MAPPING.get(code, code)
                for val in EINHEITEN_LISTE:
                    if code in val or lesbar in val: e_einheit.set(val); break
            else:
                e_menge.insert(0, "1")
                e_einheit.set("Stück (C62)")
                e_steuer.insert(0, "19")
                
            def save():
                if not e_bez.get().strip(): return messagebox.showwarning("Fehler", "Bezeichnung darf nicht leer sein!", parent=d_edit)
                try:
                    float(e_menge.get().replace(',', '.') or "1")
                    float(e_preis.get().replace(',', '.'))
                    float(e_steuer.get().replace(',', '.') or "19")
                except ValueError:
                    return messagebox.showwarning("Eingabefehler", "Zahlenwerte fehlerhaft!", parent=d_edit)
                
                einheit_val = e_einheit.get()
                match = re.search(r'\((.*?)\)', einheit_val)
                einheit_code = match.group(1).strip() if match else einheit_val.strip()
                    
                neu = {
                    'Bezeichnung': e_bez.get().strip(),
                    'Menge': e_menge.get().replace(',','.'),
                    'Einheit': einheit_code,
                    'EinzelpreisNetto': e_preis.get().replace(',','.'),
                    'Steuersatz': e_steuer.get().replace(',','.')
                }
                if index is not None: self.produkte_liste[index] = neu
                else: self.produkte_liste.append(neu)
                    
                speichere_alle_produkte(self.config.get("produkte_csv", "produkte.csv"), self.produkte_liste)
                refresh()
                d_edit.destroy()
                
            self.create_button(d_edit, text="Speichern", command=save).pack(pady=20)

        self.create_button(dialog, text="+ Neues Produkt anlegen", command=lambda: edit_p()).pack(pady=10)
        refresh()

    # --- Tab 4: Hilfe & Doku ---
    def build_hilfe_tab(self):
        if getattr(sys, 'frozen', False):
            exe_zeit = os.path.getmtime(sys.executable)
            kompilierungs_datum = datetime.fromtimestamp(exe_zeit)
        else:
            kompilierungs_datum = datetime.now()
            
        build_nr = f"1.{kompilierungs_datum.strftime('%Y%m%d.%H%M')}"

        doku_text = f"""SokoIur eRechnung
Version: {build_nr}

===========================================
1. HAFTUNGSAUSSCHLUSS
===========================================
Das Programm "SokoIur eRechnung" wird Ihnen unentgeltlich (als Gefälligkeit / Schenkung) zur Verfügung gestellt. 
Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische Umsetzung der komplexen ZUGFeRD/XRechnung-Spezifikationen, wird hiermit ausdrücklich ausgeschlossen. 
Es wird ausdrücklich darauf hingewiesen, dass auch für das Anerkennen der erstellten Rechnungen durch die Adressaten oder die Finanzämter keinerlei Gewähr oder Haftung übernommen wird.
Die Haftung ist gemäß § 521 BGB auf Vorsatz und grobe Fahrlässigkeit beschränkt. Die Nutzung im geschäftlichen Verkehr erfolgt auf Ihre eigene Gefahr. Bitte prüfen Sie erzeugte Rechnungen stichprobenartig.

===========================================
2. PROGRAMMBESCHREIBUNG & AUFRUF (CLI / GUI)
===========================================
SokoIur eRechnung ist ein Rechnungstool zur Erstellung ZUGFeRD-konformer PDFs. 
Es kann entweder komplett über die grafische Oberfläche (GUI) gesteuert werden, oder 
es fungiert als "Druck-Engine" für externe Programme.

Aufruf über Kommandozeile (CLI):
erechnung_generator.exe --auto [Parameter]   -> Generiert direkt unsichtbar im Hintergrund
erechnung_generator.exe --edit [Parameter]   -> Öffnet die GUI (Manuelle Eingabe) mit den übergebenen Daten, ohne die Rechnungsnummer automatisch hochzuzählen. Ideal, um eine von außen übergebene Rechnung vor dem Druck nochmal zu sichten.

Verfügbare CLI-Parameter (überschreiben temporär die config.json):
  --firma          Pfad zur firma.csv
  --rechnung       Pfad zur rechnung.csv
  --briefbogen     Pfad zur briefbogen.pdf
  --zusatz         Pfad zur zusatz.csv
  --gruss          Pfad zur gruss.csv
  --header         Pfad zur header.csv
  --einleitung     Pfad zur einleitung.csv
  --ausgabe        Ordner, in dem die fertigen PDFs landen sollen.

===========================================
3. KUNDENDATENbank & PRODUKTDATENbank
===========================================
Kundenbank:
Unten links im Reiter "Manuelle Eingabe" finden Sie die Checkbox "Kunde speichern/updaten". 
Ist diese angehakt, wird der eingegebene Kunde (inkl. Kunden-Nr. und Aktenzeichen) dauerhaft gespeichert. Über das Dropdown "Kunde Name" oder den Suchbutton (🔍) neben der Kundennummer können Sie diese Kunden jederzeit wieder abrufen; alle zugehörigen Felder füllen sich automatisch.

Produktebank:
In der Positionserfassung (Klick auf "+ Position hinzufügen") ist das Feld "Bezeichnung" ein Dropdown. 
Wählen Sie ein Standardprodukt aus, werden Preis, Menge, Einheit und Steuer automatisch ausgefüllt.

Manager:
Im Reiter "Einstellungen" finden Sie unten die Buttons zur Verwaltung dieser Datenbanken. 
Dort können Sie Kunden und Produkte komfortabel in einer übersichtlichen Liste bearbeiten, neu anlegen oder löschen.

===========================================
4. RECHNUNGSPOSITIONEN & LEISTUNGSZEITRAUM
===========================================
Nach Vorgaben der Finanzämter muss ein Leistungszeitraum für die erbrachte Leistung vorliegen.
WICHTIG: Ist im Kopf UND in der Position ein Zeitraum angegeben, muss der Positionszeitraum ZWINGEND kalendarisch INNERHALB des Kopf-Zeitraums liegen. Das System überprüft dies vollautomatisch.

Negative Preise (Rabatte/Gutschriften): 
Dürfen Sie wie gewohnt mit z.B. "-100" erfassen. Die Norm (BR-27) verbietet eigentlich negative Preise. Das Programm rechnet das im Hintergrund automatisch konform um (Positiver Preis, Negative Menge).

===========================================
5. DATUMSEINGABEN
===========================================
Zulässige Formate: TTMMJJ, TT,MM,JJ, TT.MM.JJJJ, TT,MM,JJJJ oder JJJJ-MM-TT.

===========================================
6. TEXTFORMATIERUNGEN & TEXTE MERKEN
===========================================
Zeilenumbruch in der CSV: ~cr
Fett drucken:  ~f Ihr Text f~
Kursiv drucken:~k Ihr Text k~

Standard-Texte (Checkbox):
In der Text-Maske (📝 Texte) können Sie festlegen, ob ein Text (Einleitung, Gruß) für die nächste NEUE Rechnung im System gemerkt werden soll (Häkchen gesetzt). Fehlt das Häkchen, leert das Programm das Feld bei der nächsten neuen Rechnung.

===========================================
7. JOURNAL & AUSWERTUNGEN
===========================================
Das Programm erstellt bei jedem Speichervorgang im Hintergrund eine Monats-CSV (z.B. re202611.csv). 
Im Reiter "Auswertungen" können Sie für einen Monat oder ein ganzes Jahr mit einem Klick eine saubere, aufsummierte PDF-Tabelle mit der korrekten Trennung aller Steuerbeträge erzeugen.

===========================================
8. TASTATUR-STEUERUNG (SHORTCUTS)
===========================================
  + oder Numpad + : Neue Position hinzufügen
  Alt + L         : Aktuelle CSV laden
  Alt + T         : Texte bearbeiten
  Alt + S         : Nur Speichern (CSV)
  Alt + P         : Speichern, PDF erstellen und öffnen
  Tab / Shift+Tab : Zwischen Feldern wechseln
  Enter / Leer    : Fokussierten Button auslösen
"""
        hilfe_box = ctk.CTkTextbox(self.tab_hilfe, width=800, height=400, font=("Consolas", 13))
        hilfe_box.pack(pady=(10, 5), padx=10, fill="both", expand=True)
        hilfe_box.insert("0.0", doku_text)
        hilfe_box.configure(state="disabled")
        
        f_links = ctk.CTkFrame(self.tab_hilfe, fg_color="transparent")
        f_links.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(f_links, text="Open Source Lizenzen:", font=("Helvetica", 12, "bold")).pack(anchor="w")
        
        def open_psf(e): webbrowser.open("https://docs.python.org/3/license.html")
        def open_mit(e): webbrowser.open("https://opensource.org/licenses/MIT")
        def open_bsd(e): webbrowser.open("https://opensource.org/licenses/BSD-3-Clause")
        
        l1 = ctk.CTkLabel(f_links, text="Python (PSF License)", text_color="#1f538d", cursor="hand2")
        l1.pack(anchor="w"); l1.bind("<Button-1>", open_psf)
        
        l2 = ctk.CTkLabel(f_links, text="CustomTkinter (MIT License)", text_color="#1f538d", cursor="hand2")
        l2.pack(anchor="w"); l2.bind("<Button-1>", open_mit)
        
        l3 = ctk.CTkLabel(f_links, text="ReportLab & pypdf (BSD License)", text_color="#1f538d", cursor="hand2")
        l3.pack(anchor="w"); l3.bind("<Button-1>", open_bsd)


# ==========================================
# PROGRAMM START (Weiche für CLI / GUI)
# ==========================================

def main():
    if os.path.exists(LOCK_FILE):
        root = tk.Tk()
        root.withdraw()
        while os.path.exists(LOCK_FILE):
            res = messagebox.askyesnocancel("Programm läuft bereits", "Die Sperrdatei (erechnung.lock) wurde gefunden. Das Programm läuft eventuell bereits im Hintergrund.\n\nJa = Sperrung aufheben und trotzdem starten\nNein = Warten (prüft erneut)\nAbbrechen = Beenden", parent=root)
            if res is True: 
                try: os.remove(LOCK_FILE)
                except: pass
                break
            elif res is None: 
                root.destroy()
                sys.exit(0)
            else: 
                time.sleep(1)
        root.destroy()
        
    try:
        with open(LOCK_FILE, 'w') as f: f.write("LOCKED")
    except: pass

    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Ohne GUI generieren")
    parser.add_argument("--edit", action="store_true", help="Mit GUI in manueller Eingabe starten")
    parser.add_argument("--firma", type=str)
    parser.add_argument("--rechnung", type=str)
    parser.add_argument("--briefbogen", type=str)
    parser.add_argument("--zusatz", type=str)
    parser.add_argument("--gruss", type=str)
    parser.add_argument("--header", type=str)
    parser.add_argument("--einleitung", type=str)
    parser.add_argument("--ausgabe", type=str)
    args = parser.parse_args()

    config = init_config()
    
    if not config.get("terms_accepted", False):
        root = tk.Tk()
        root.withdraw()
        haftungs_text = (
            "HAFTUNGSAUSSCHLUSS UND NUTZUNGSBEDINGUNGEN\n\n"
            "Das Programm 'SokoIur eRechnung' wird Ihnen unentgeltlich (als Gefälligkeit / Schenkung) zur Verfügung gestellt.\n\n"
            "Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische "
            "Umsetzung der komplexen ZUGFeRD/XRechnung-Spezifikationen, wird hiermit ausdrücklich ausgeschlossen.\n\n"
            "Es wird ausdrücklich darauf hingewiesen, dass auch für das Anerkennen der erstellten Rechnungen durch die Adressaten "
            "oder die Finanzämter keinerlei Gewähr oder Haftung übernommen wird.\n\n"
            "Die Haftung ist gemäß § 521 BGB auf Vorsatz und grobe Fahrlässigkeit beschränkt. Die Nutzung im geschäftlichen Verkehr "
            "erfolgt auf Ihre eigene Gefahr. Bitte prüfen Sie erzeugte Rechnungen stichprobenartig.\n\n"
            "Akzeptieren Sie diese Nutzungsbedingungen, um das Programm zu starten?"
        )
        res = messagebox.askyesno("Nutzungsbedingungen akzeptieren", haftungs_text, parent=root)
        if res:
            config["terms_accepted"] = True
            speichere_config(config)
            root.destroy()
        else:
            root.destroy()
            try: os.remove(LOCK_FILE)
            except: pass
            sys.exit(0)

    if args.firma: config['firma_csv'] = args.firma
    if args.rechnung: config['rechnung_csv'] = args.rechnung
    if args.briefbogen: config['briefbogen_pdf'] = args.briefbogen
    if args.zusatz: config['zusatz_csv'] = args.zusatz
    if args.gruss: config['gruss_csv'] = args.gruss
    if args.header: config['header_csv'] = args.header
    if args.einleitung: config['einleitung_csv'] = args.einleitung
    if args.ausgabe: config['ausgabe_ordner'] = args.ausgabe

    if args.auto:
        run_auto_generation(config)
        try: os.remove(LOCK_FILE)
        except: pass
    else:
        app = App(config, start_in_edit=args.edit)
        app.mainloop()

if __name__ == "__main__":
    main()
