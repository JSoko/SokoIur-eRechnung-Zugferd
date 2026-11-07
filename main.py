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
import tkinter as tk
import tkinter.messagebox as messagebox

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
    parser.add_argument("--briefbogen", type=str)
    parser.add_argument("--zusatz", type=str)
    parser.add_argument("--gruss", type=str)
    parser.add_argument("--header", type=str)
    parser.add_argument("--einleitung", type=str)
    parser.add_argument("--ausgabe", type=str)
    parser.add_argument("--auswertungen", type=str)
    parser.add_argument("--jahr", type=str)
    # NEU: Parameter zum Unterdrücken des PDF-Öffnens
    parser.add_argument("--no-open", action="store_true", help="Verhindert das Öffnen der erstellten PDF")

    args = parser.parse_args()

    # 3. Datenbank / Konfiguration initialisieren
    config = init_config()
    config["cli_no_open"] = args.no_open

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

    # 7. Start-Weiche: GUI oder Auto-Generierung (CLI)
    if args.auto:
        run_auto_generation(config)

    else:
        app = App(config, start_in_edit=args.edit)
        app.mainloop()

if __name__ == "__main__":
    main()
