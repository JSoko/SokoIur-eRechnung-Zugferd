"""
main.py
-------
Haupteinstiegspunkt (Entry Point) der SokoIur eRechnung.
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

from config import init_config, speichere_config, LOCK_FILE, get_app_version
from crud import ensure_utf8_csv
from pdf_zugferd import run_auto_generation
from gui_app import App
from hilfe_texte import get_hilfe_html_path

v_string = get_app_version()


def main():
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
    parser.add_argument("--vor-gruss", type=str)
    parser.add_argument("--textvorlage", type=str, help="Lädt eine gespeicherte Textkombination (z.B. 'Vorschussrechnung')")
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

    config = init_config()
    
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
    if args.zahlungsbedingungen:
        config["cli_zahlungsbedingungen"] = args.zahlungsbedingungen
    if args.rechnungsvermerk:
        config["cli_rechnungsvermerk"] = args.rechnungsvermerk

    if args.profil:
        profil_gefunden = False
        for i, p in enumerate(config["profiles"]):
            if p["profil_name"].lower() == args.profil.lower():
                config["active_profile_index"] = i
                profil_gefunden = True
                break
                
        if not profil_gefunden:
            try:
                import pyi_splash
                pyi_splash.close()
            except ImportError:
                pass
            err_msg = f"Fehler: Das übergebene Firmenprofil '{args.profil}' wurde in der Datenbank nicht gefunden!"
            print(err_msg)
            
            if not args.auto:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Profil nicht gefunden", err_msg)
                root.destroy()
                
            sys.exit(1)
    
    if not config.get("terms_accepted", False):
        root = tk.Tk()
        root.withdraw()
        try:
            import pyi_splash
            pyi_splash.close()
        except ImportError:
            pass    
        haftungs_text = (
            "NUTZUNGSBEDINGUNGEN, TESTZEITRAUM & HAFTUNGSAUSSCHLUSS\n\n"
            "1. TESTZEITRAUM & LIZENZMODELL (B2B):\n"
            "Das Programm 'SokoIur eRechnung' kann 21 Tage lang mit allen Pro-Funktionen ohne Hinweisdialog "
            "getestet werden. Nach Ablauf der 21 Tage bleiben alle Funktionen nutzbar; bei jeder 10. Nutzung "
            "einer Pro-Funktion erscheint ein Hinweis zur Lizenzierung. Der Verkauf kostenpflichtiger Lizenzen "
            "erfolgt ausschließlich an in Deutschland ansässige Unternehmer und Freiberufler (B2B) gemäß unseren "
            "AGB unter https://erech.6078.de/agb.html.\n\n"
            "2. HAFTUNGSAUSSCHLUSS:\n"
            "Eine Gewährleistung für die inhaltliche, technische oder steuerliche Fehlerfreiheit, insbesondere "
            "für die Umsetzung der ZUGFeRD/XRechnung-Spezifikationen sowie für die Anerkennung durch Empfänger "
            "oder Finanzämter, wird nicht übernommen. Bitte prüfen Sie erzeugte Belege und Exporte eigenverantwortlich.\n\n"
            "3. DATENSCHUTZ / VERBINDUNGEN:\n"
            "Das Programm und die Lizenzprüfung arbeiten vollständig lokal. Eine Verbindung ins Internet "
            "erfolgt nicht automatisch, sondern nur, wenn Sie selbst aktiv die Updateprüfung anstoßen.\n\n"
            "Akzeptieren Sie diese Bedingungen, um das Programm zu starten?"
        )
        res = messagebox.askyesno("Nutzungsbedingungen akzeptieren", haftungs_text, parent=root)
        if res:
            config["terms_accepted"] = True
            speichere_config(config)
            root.destroy()
        else:
            root.destroy()
            sys.exit(0)
   
    idx = config["active_profile_index"]
    
    def apply_cli(key, val):
        if val:
            config["profiles"][idx][key] = val
            config[f"cli_override_{key}"] = val

    if args.firma: apply_cli('firma_csv', args.firma)
    if args.rechnung: 
        if config["profiles"][idx].get("auto_convert_utf8", True):
            ensure_utf8_csv(args.rechnung)
        apply_cli('rechnung_csv', args.rechnung)
        
    if args.briefbogen: apply_cli('briefbogen_pdf', args.briefbogen)
    if args.zusatz: apply_cli('zusatz_csv', args.zusatz)
    if args.gruss: apply_cli('gruss_csv', args.gruss)
    if args.header: apply_cli('header_csv', args.header)
    if args.einleitung: apply_cli('einleitung_csv', args.einleitung)
    if args.ausgabe: apply_cli('ausgabe_ordner', args.ausgabe)
    if args.auswertungen: apply_cli('auswertungen_ordner', args.auswertungen)
    if args.vor_gruss: apply_cli('vor_gruss_csv', args.vor_gruss)
    if args.textvorlage:
        vorlagen = config["profiles"][idx].get("text_vorlagen", {})
        if args.textvorlage in vorlagen:
            from crud import speichere_textdatei
            v = vorlagen[args.textvorlage]
            speichere_textdatei(config["profiles"][idx].get('header_csv'), v.get("header", ""))
            speichere_textdatei(config["profiles"][idx].get('einleitung_csv'), v.get("einleitung", ""))
            speichere_textdatei(config["profiles"][idx].get('vor_gruss_csv'), v.get("vor_gruss", ""))
            speichere_textdatei(config["profiles"][idx].get('gruss_csv'), v.get("gruss", ""))
            config["profiles"][idx]["zahlungsbedingungen_default"] = v.get("zahlungsbedingungen", "")
            config["profiles"][idx]["rechnungsvermerk_default"] = v.get("rechnungsvermerk", "")
            config["profiles"][idx]["aktive_text_vorlage"] = args.textvorlage
    
    if args.auto:
        lock_file = None
        base_path = config.get("base_data_path")

        # Pro-Nutzung fuer CLI (--auto) zaehlen (ohne GUI-Fenster im Hintergrundmodus)
        try:
            from license_manager import LicenseManager
            lm = LicenseManager(type("DummyApp", (), {"config": config})())
            status = lm.get_license_status()
            if not status["active_pro"]:
                lm.state["pro_uses"] = int(lm.state.get("pro_uses", 0) or 0) + 1
                lm._persist_state()
        except Exception:
            pass
        
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
            config["is_cli_auto"] = True
            run_auto_generation(config)
        finally:
            if lock_file and os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except Exception:
                    pass
                    
        try:
            import pyi_splash
            pyi_splash.close()
        except ImportError:
            pass
            
    else:
        app = App(config, start_in_edit=args.edit)
        if args.edit and hasattr(app, "license_mgr"):
            app.after(450, lambda: app.license_mgr.record_pro_feature_use("Kommandozeilen-Automatisierung (--edit)"))
        
        def close_splash():
            try:
                import pyi_splash
                pyi_splash.close()
            except ImportError:
                pass
                
        app.after(200, close_splash)
        app.mainloop()
        
if __name__ == "__main__":
    main()
