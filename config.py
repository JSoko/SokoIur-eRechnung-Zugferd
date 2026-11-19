"""
config.py
------------
Datenverwaltung, Konfiguration und Hilfsfunktionen.
Dieses Modul ist für das Einlesen, Validieren und Speichern aller lokalen Daten
verantwortlich. Dazu gehören die Konfigurationsdatei (config.json), Firmenprofile, 
Kunden- und Produktdatenbanken sowie die temporären Rechnungs-CSVs. Zudem enthält
es globale Logik für Datumsberechnungen und Nummernkreise.
"""
import os
import sys
import json
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
CONFIG_DATEI = "config.json"
LOCK_FILE = "erechnung.lock"
LOCAL_CONFIG = os.path.join(APP_DIR, "local_config.json")

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_default_profile(suffix=""):
    s = f"_{suffix}" if suffix else ""
    return {
        "profil_name": "Hauptfirma" if not suffix else f"Firma {suffix}",
        "firma_csv": f"firma{s}.csv",
        "rechnung_csv": f"rechnung{s}.csv",
        "briefbogen_pdf": f"briefbogen{s}.pdf",
        "zusatz_csv": f"zusatz{s}.csv",
        "gruss_csv": f"gruss{s}.csv",
        "vor_gruss_csv": f"vor_gruss{s}.csv",
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
        "text_vorlagen": {},
        "aktive_text_vorlage": "Standard",
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
        "datev_kreditor": "70000",
        "audit_reason_required": False,
        "email_versand_methode": "Keine",  # Optionen: "Keine", "Outlook", "Thunderbird"
        "thunderbird_pfad": r"C:\Program Files\Mozilla Thunderbird\thunderbird.exe"
    }
    

def init_config():
    config = {"window_geometry": "950x850", "terms_accepted": False, "base_data_path": "", "active_profile_index": 0}
    if os.path.exists(LOCAL_CONFIG):
        try:
            with open(LOCAL_CONFIG, 'r', encoding='utf-8') as f:
                local_data = json.load(f)
                config.update(local_data)
        except: pass

    config["profiles"] = []
    if config.get("base_data_path") and os.path.exists(config["base_data_path"]):
        shared_config_path = os.path.join(config["base_data_path"], "shared_firms.json")
        if os.path.exists(shared_config_path):
            try:
                with open(shared_config_path, 'r', encoding='utf-8') as f:
                    config["profiles"] = json.load(f)
            except: pass

    if not config["profiles"]:
        config["profiles"] = [get_default_profile("")]

    return config

def speichere_config(config):
    local_data = {
        "window_geometry": config.get("window_geometry", "950x700"),
        "window_state": config.get("window_state", "normal"),
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
        
    if config.get("base_data_path") and os.path.exists(config["base_data_path"]):
        shared_config_path = os.path.join(config["base_data_path"], "shared_firms.json")
        with open(shared_config_path, 'w', encoding='utf-8') as f:
            json.dump(config["profiles"], f, indent=4)