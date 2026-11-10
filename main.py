"""
main.py
-------
Haupteinstiegspunkt (Entry Point) der SokoIur eRechnung.
Dieses Modul verarbeitet Kommandozeilenparameter, schützt vor Mehrfachausführungen
(Lock-File), initialisiert die Konfiguration und Nutzungsbedingungen und startet 
schließlich entweder die grafische Oberfläche (GUI) oder die automatische 
PDF-Generierung im Hintergrund (CLI/Auto-Modus).
"""
import os
import sys
import time
import argparse
from datetime import datetime
import tkinter as tk
import tkinter.messagebox as messagebox
if getattr(sys, 'frozen', False):
    sys.path.append(sys._MEIPASS)
else:
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# Importieren der Funktionen aus unseren eigenen 3 Modulen
from datenbank import init_config, speichere_config, LOCK_FILE
from pdf_zugferd import run_auto_generation
from gui_app import App

def main():
    # 2. Kommandozeilenparameter definieren und auslesen
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Ohne GUI generieren")
    parser.add_argument("--edit", action="store_true", help="Mit GUI in manueller Eingabe starten")
    parser.add_argument("--profil", type=str, help="Name des aktiven Firmenprofils (z.B. 'Firma 1')")
    parser.add_argument("--firma", type=str)
    parser.add_argument("--rechnung", type=str)
    parser.add_argument("--renr", type=str, help="Überschreibt die Rechnungsnummer für die zu erstellende Rechnung")
    parser.add_argument("--kunde-az", type=str, help="Überschreibt das Aktenzeichen des Kunden (Ihr Zeichen)")
    parser.add_argument("--kopie", type=str, help="Verzeichnis, in dem eine zusätzliche Kopie der Rechnung abgelegt wird")
    parser.add_argument("--briefbogen", type=str)
    parser.add_argument("--zusatz", type=str)
    parser.add_argument("--gruss", type=str)
    parser.add_argument("--header", type=str)
    parser.add_argument("--einleitung", type=str)
    parser.add_argument("--ausgabe", type=str)
    parser.add_argument("--auswertungen", type=str)
    parser.add_argument("--jahr", type=str)
    parser.add_argument("--no-open", action="store_true", help="Verhindert das Öffnen der erstellten PDF")
    parser.add_argument("--zahlungsbedingungen", type=str, help="Zahlungsbedingungen (BT-20)")
    parser.add_argument("--rechnungsvermerk", type=str, help="Rechnungsvermerk / Dauerrechnungshinweis (BT-22)")
    parser.add_argument("--kontoinhaber", type=str, help="Überschreibt temporär den Kontoinhaber")
    parser.add_argument("--no-girocode", action="store_true", help="Girocode auf dem PDF deaktivieren")
    parser.add_argument("--force-girocode", action="store_true", help="Girocode auf dem PDF erzwingen")

    args = parser.parse_args()

    # 3. Datenbank / Konfiguration initialisieren
    config = init_config()
    
    # --- HTML-Hilfsdatei & Snippet beim Programmstart automatisch im AppData-Ordner aktualisieren ---
    try:
        from hilfe_texte import get_doku_html, get_doku_body_html, get_changelog_html, get_changelog_body_html
        from datenbank import get_appdata_dir
        
        app_dir = get_appdata_dir()
        
        hilfe_pfad = os.path.join(app_dir, "SokoIur_Hilfe.html")
        snippet_pfad = os.path.join(app_dir, "html.txt")
        changelog_pfad = os.path.join(app_dir, "changelog.html")
        clg_pfad = os.path.join(app_dir, "clg.txt")
        
        # Versionsstring aus der .exe ermitteln
        from datenbank import get_app_version
        v_string = get_app_version()
        
        with open(hilfe_pfad, "w", encoding="utf-8") as f_html:
            f_html.write(get_doku_html(v_string))
        with open(snippet_pfad, "w", encoding="utf-8") as f_snippet:
            f_snippet.write(get_doku_body_html(v_string))
            
        with open(changelog_pfad, "w", encoding="utf-8") as f_clg_html:
            f_clg_html.write(get_changelog_html(v_string))
        with open(clg_pfad, "w", encoding="utf-8") as f_clg_txt:
            f_clg_txt.write(get_changelog_body_html(v_string))
            
    except Exception as e:
        print(f"Konnte Hilfsdateien beim Start nicht erstellen: {e}")
    
    config["cli_no_open"] = args.no_open
    config["cli_no_girocode"] = args.no_girocode
    config["cli_force_girocode"] = args.force_girocode
    config["cli_kontoinhaber"] = args.kontoinhaber
    if args.renr: 
        config["cli_renr"] = args.renr
    if args.kunde_az:
        config["cli_kunde_az"] = args.kunde_az
    if args.kopie:
        config["cli_kopie"] = args.kopie

    # 4. Profil wechseln, falls per Kommandozeile gefordert
    if args.profil:
        for i, p in enumerate(config["profiles"]):
            if p["profil_name"].lower() == args.profil.lower():
                config["active_profile_index"] = i
                break
    
    # 5. Haftungsausschluss beim allerersten Start prüfen
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
            "DATENSCHUTZ / VERBINDUNGEN:\n"
            "Das Programm arbeitet komplett lokal. Ausschließlich zur Updateprüfung, die nicht automatisch durchgeführt sondern durch "
            "den entsprechenden Button vom Benutzer angestoßen wird, wird eine Datenverbindung zu GitHub benötigt und aufgebaut.\n\n"
            "Akzeptieren Sie diese Nutzungsbedingungen, um das Programm zu starten?"
        )
        res = messagebox.askyesno("Nutzungsbedingungen akzeptieren", haftungs_text, parent=root)
        if res:
            config["terms_accepted"] = True
            speichere_config(config)
            root.destroy()
        else:
            root.destroy()
            sys.exit(0)

    # 6. Etwaige Kommandozeilenpfade temporär in das aktive Profil überschreiben
    idx = config["active_profile_index"]
    if args.firma: config["profiles"][idx]['firma_csv'] = args.firma
    if args.rechnung: config["profiles"][idx]['rechnung_csv'] = args.rechnung
    if args.briefbogen: config["profiles"][idx]['briefbogen_pdf'] = args.briefbogen
    if args.zusatz: config["profiles"][idx]['zusatz_csv'] = args.zusatz
    if args.gruss: config["profiles"][idx]['gruss_csv'] = args.gruss
    if args.header: config["profiles"][idx]['header_csv'] = args.header
    if args.einleitung: config["profiles"][idx]['einleitung_csv'] = args.einleitung
    if args.ausgabe: config["profiles"][idx]['ausgabe_ordner'] = args.ausgabe
    if args.auswertungen: config["profiles"][idx]['auswertungen_ordner'] = args.auswertungen
    if args.jahr: config["profiles"][idx]['aktuelles_rechnungsjahr'] = args.jahr
    if args.zahlungsbedingungen: config["profiles"][idx]['zahlungsbedingungen_default'] = args.zahlungsbedingungen
    if args.rechnungsvermerk: config["profiles"][idx]['rechnungsvermerk_default'] = args.rechnungsvermerk
    
    # 7. Start-Weiche: GUI oder Auto-Generierung (CLI)
    if args.auto:
        lock_file = None
        base_path = config.get("base_data_path")
        
        # 7.1 Lock für Auto-Generierung setzen
        if base_path:
            idx = config["active_profile_index"]
            firm_dir = os.path.join(base_path, config["profiles"][idx]["profil_name"].replace(" ", "_"))
            os.makedirs(firm_dir, exist_ok=True)
            lock_file = os.path.join(firm_dir, "erechnung.lock")
            
            if os.path.exists(lock_file):
                print(f"⚠️ Warnung: Die Firma '{config['profiles'][idx]['profil_name']}' ist aktuell gesperrt (Lock existiert). Auto-Generierung könnte zu Konflikten führen.")
            
            try:
                with open(lock_file, "w") as f:
                    f.write(str(os.getpid()))
            except Exception as e:
                print(f"Fehler beim Setzen des Locks: {e}")
        
        try:
            # 7.2 Generierung durchführen
            run_auto_generation(config)
        finally:
            # 7.3 Lock nach Generierung (auch bei Fehlern) immer wieder entfernen
            if lock_file and os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except Exception:
                    pass

    else:
        app = App(config, start_in_edit=args.edit)
        app.mainloop()
    
if __name__ == "__main__":
    main()

