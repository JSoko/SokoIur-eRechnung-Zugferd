"""
datenbank.py
------------
Datenverwaltung, Konfiguration und Hilfsfunktionen.
Dieses Modul ist für das Einlesen, Validieren und Speichern aller lokalen Daten
verantwortlich. Dazu gehören die Konfigurationsdatei (config.json), Firmenprofile, 
Kunden- und Produktdatenbanken sowie die temporären Rechnungs-CSVs. Zudem enthält
es globale Logik für Datumsberechnungen und Nummernkreise.
"""
import csv
import os
import sys
import json
import re
import ctypes
from datetime import datetime

def get_appdata_dir():
    appdata = os.environ.get('LOCALAPPDATA')
    if not appdata:
        appdata = os.path.expanduser('~')
    app_dir = os.path.join(appdata, "SokoIur_eRechnung")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def get_app_version():
    """Liest die Produktversion aus den Dateiinformationen der kompilierten .exe aus."""
    v_string = "1.000000"  # Standard-Fallback
    if getattr(sys, 'frozen', False):
        try:
            size = ctypes.windll.version.GetFileVersionInfoSizeW(sys.executable, None)
            if size > 0:
                res = ctypes.create_string_buffer(size)
                ctypes.windll.version.GetFileVersionInfoW(sys.executable, None, size, res)
                
                r_length = ctypes.c_uint()
                r_address = ctypes.c_void_p()
                # Zuerst die Sprache und Codepage (Translation) ermitteln
                ctypes.windll.version.VerQueryValueW(res, "\\VarFileInfo\\Translation", ctypes.byref(r_address), ctypes.byref(r_length))
                
                if r_length.value >= 4:
                    lang_codepage = ctypes.cast(r_address, ctypes.POINTER(ctypes.c_uint32)).contents.value
                    lang = lang_codepage & 0xFFFF
                    codepage = lang_codepage >> 16
                    
                    # Pfad zur Produktversion zusammensetzen
                    sub_block = f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\ProductVersion"
                    ctypes.windll.version.VerQueryValueW(res, sub_block, ctypes.byref(r_address), ctypes.byref(r_length))
                    
                    if r_length.value > 0:
                        v_string = ctypes.cast(r_address, ctypes.c_wchar_p).value
        except Exception:
            pass
    else:
        v_string = "Entwickler-Version"
    return v_string

APP_DIR = get_appdata_dir()
# ... ab hier geht der restliche Code weiter (CONFIG_DATEI = ...) ...
CONFIG_DATEI = "config.json"
LOCK_FILE = "erechnung.lock"
LOCAL_CONFIG = os.path.join(APP_DIR, "local_config.json")

EINHEITEN_LISTE = [
    "Stück (C62)", "Pauschale (LS)", "Stunde(n) (HUR)", 
    "Monat(e) (MON)", "Tag(e) (DAY)", "km (KMT)", "Satz (SET)"
]

EINHEITEN_MAPPING = {
    "C62": "Stück", "LS": "Pauschale", "HUR": "Stunde(n)",
    "MON": "Monat(e)", "DAY": "Tag(e)", "KMT": "km", "SET": "Satz"
}

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_csv_if_missing(filename, header_str):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8-sig') as f:
            if header_str: f.write(header_str + "\n")

def get_default_profile(suffix=""):
    s = f"_{suffix}" if suffix else ""
    return {
        "profil_name": "Hauptfirma" if not suffix else f"Firma {suffix}",
        "firma_csv": f"firma{s}.csv",
        "rechnung_csv": f"rechnung{s}.csv",
        "briefbogen_pdf": f"briefbogen{s}.pdf",
        "zusatz_csv": f"zusatz{s}.csv",
        "gruss_csv": f"gruss{s}.csv",
        "header_csv": f"header{s}.csv",
        "einleitung_csv": f"einleitung{s}.csv",
        "ausgabe_ordner": f"Rechnungen_PDF{s}",
        "kunden_csv": f"kunden{s}.csv",
        "produkte_csv": f"produkte{s}.csv",
        "auswertungen_ordner": f"aausw{s}",
        "faelligkeit_tage": "29",
        "letzte_rechnungsnummer": "",
        "aktuelles_rechnungsjahr": str(datetime.now().year),
        "letzte_einheit": "Stück (C62)",
        "keep_header": True,
        "keep_einleitung": True,
        "keep_gruss": True,
        "keep_raten": False,
        "keep_kunde_speichern": False,
        "zahlungsbedingungen_default": "",
        "rechnungsvermerk_default": "",
        "letzte_eingangsrechnungsnummer": "",
        "xrechnung_leseabschrift": True,
        "eingang_loesch_warteliste": [],
        "eingangsordner": f"reneu{s}",
        "bearbeitete_eingangsrechnungen_ordner": f"rebearb{s}",
        "eingangsrechnungen_ordner": f"rchn{s}",
        "eingangsjournal_ordner": f"eausw{s}",
        # DATEV FELDER ---
        "datev_kontenrahmen": "SKR03",
        "datev_erloese_19": "8400",
        "datev_erloese_7": "8300",
        "datev_erloese_0": "8200",
        "datev_debitor": "10000",
        "datev_aufwand_19": "3400",
        "datev_aufwand_7": "3300",
        "datev_aufwand_0": "3200",
        "datev_kreditor": "70000"
    }

def init_config():
    # 1. Lokale Config laden (für Startpfad und Geometrie)
    config = {"window_geometry": "950x850", "terms_accepted": False, "base_data_path": "", "active_profile_index": 0}
    if os.path.exists(LOCAL_CONFIG):
        try:
            with open(LOCAL_CONFIG, 'r', encoding='utf-8') as f:
                local_data = json.load(f)
                config.update(local_data)
        except: pass

    # 2. Globale Config aus dem Netzwerk laden (falls base_data_path existiert)
    config["profiles"] = []
    if config.get("base_data_path") and os.path.exists(config["base_data_path"]):
        shared_config_path = os.path.join(config["base_data_path"], "shared_firms.json")
        if os.path.exists(shared_config_path):
            try:
                with open(shared_config_path, 'r', encoding='utf-8') as f:
                    config["profiles"] = json.load(f)
            except: pass

    # Fallback, falls noch keine Firmen existieren
    if not config["profiles"]:
        config["profiles"] = [get_default_profile("")]

    return config

def speichere_config(config):
    # 1. Lokale Config speichern (Programmordner)
    local_data = {
        "window_geometry": config.get("window_geometry", "950x850"),
        "terms_accepted": config.get("terms_accepted", False),
        "base_data_path": config.get("base_data_path", ""),
        "active_profile_index": config.get("active_profile_index", 0),
        "cli_open_pdf": config.get("cli_open_pdf", False),
        "cli_keep_open": config.get("cli_keep_open", False),
        "cli_no_open": config.get("cli_no_open", False),
        "last_run_version": config.get("last_run_version", "")
    }
    with open(LOCAL_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(local_data, f, indent=4)

    # 2. Globale Profile im Netzwerk speichern (Firmenübergreifend)
    if config.get("base_data_path") and os.path.exists(config["base_data_path"]):
        shared_config_path = os.path.join(config["base_data_path"], "shared_firms.json")
        with open(shared_config_path, 'w', encoding='utf-8') as f:
            json.dump(config["profiles"], f, indent=4)

def ensure_utf8_csv(pfad):
    """Prüft ob eine CSV UTF-8 ist, falls nicht (z.B. ANSI/Excel), wird sie konvertiert."""
    if not pfad or not os.path.exists(pfad):
        return
    try:
        # Testweise als UTF-8 lesen
        with open(pfad, 'r', encoding='utf-8-sig') as f:
            f.read()
    except UnicodeDecodeError:
        # Wenn es knallt, als Windows-1252 (Standard Excel/ANSI) lesen und überschreiben
        with open(pfad, 'r', encoding='windows-1252') as f:
            inhalt = f.read()
        with open(pfad, 'w', encoding='utf-8-sig') as f:
            f.write(inhalt)

def berechne_naechste_rechnungsnummer(letzte_nr):
    if not letzte_nr: return f"RE-{datetime.now().year}-001"
    match = re.search(r'(\d+)$', letzte_nr)
    if match:
        zahl_str = match.group(1)
        naechste_zahl = str(int(zahl_str) + 1).zfill(len(zahl_str))
        return letzte_nr[:match.start()] + naechste_zahl
    return letzte_nr + "-1"

def lade_firma(pfad):
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            reader = list(csv.DictReader(f, delimiter=';'))
            if reader: return reader[0]
    except: pass
    return {'FirmaName': 'Bitte Firmendaten konfigurieren', 'Strasse': '', 'PLZ': '', 'Ort': '', 'Land': 'DE', 'UStId': '', 'Steuernummer': '', 'BankName': '', 'IBAN': '', 'BIC': '', 'Kontoinhaber': '', 'Girocode': '1'}

def speichere_firma(pfad, daten):
    fieldnames = ['FirmaName', 'Strasse', 'PLZ', 'Ort', 'Land', 'UStId', 'Steuernummer', 'BankName', 'IBAN', 'BIC', 'Kontoinhaber', 'Girocode', 'Falzmarken', 'Email', 'Telefon']
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerow(daten)

def lade_rechnungen(pfad):
    rechnungen = {}
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f, delimiter=';'):
                r_nr = row['Rechnungsnummer']
                if r_nr not in rechnungen: rechnungen[r_nr] = {'kopf': row, 'positionen': []}
                rechnungen[r_nr]['positionen'].append(row)
    except: pass
    return rechnungen

def lade_zusatz_csv(pfad):
    texte = []
    if not os.path.exists(pfad): return texte
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.split(';', 1)
                if len(parts) == 2:
                    texte.append({'pos': parts[0].strip(), 'text': parts[1].strip().replace('~cr', '\n')})
    except: pass
    return texte

def lade_textdatei(pfad):
    if not os.path.exists(pfad): return ""
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            return f.read().strip().replace('~cr', '\n')
    except: return ""

def speichere_textdatei(pfad, text):
    if not pfad: return
    try:
        with open(pfad, 'w', encoding='utf-8-sig') as f:
            f.write(text.replace('\n', '~cr').strip())
    except: pass

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
    fieldnames = ['Name', 'Strasse', 'PLZ_Ort', 'Land', 'KundeNr', 'Aktenzeichen', 'KundeAktenzeichen', 'Endpoint', 'EndpointScheme']
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