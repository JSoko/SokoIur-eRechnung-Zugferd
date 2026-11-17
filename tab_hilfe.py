"""
tab_hilfe.py
------------
Logik und Aufbau des Reiters "Info & Hilfe".
"""
import customtkinter as ctk
import tkinter.messagebox as messagebox
import os
import json
import re
import csv
from datetime import datetime
import hilfe_texte
from config import get_appdata_dir

class TabHilfeMixin:
    def build_hilfe_tab(self):
        f = ctk.CTkFrame(self.tab_hilfe, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=40, pady=20)
        
        ctk.CTkLabel(f, text="Handbuch & Dokumentation", font=("Helvetica", 20, "bold")).pack(pady=(0, 10))
        ctk.CTkLabel(f, text="Das Handbuch wurde als HTML-Datei erstellt und öffnet sich in Ihrem Standard-Webbrowser.\n(Die Dateien 'SokoIur_Hilfe.html' und 'html.txt' liegen im Programmordner).", justify="center").pack(pady=(0, 15))
        
        self.create_button(f, text="📖 Handbuch im Browser öffnen", width=250, height=35, command=self.open_html_help).pack(pady=(0, 10))
        self.create_button(f, text="📜 Changelog im Browser öffnen", width=250, height=35, command=self.open_changelog_html).pack(pady=(0, 15))
        
        f_stat = ctk.CTkFrame(f, fg_color="#2b2b2b" if ctk.get_appearance_mode()=="Dark" else "#e6e6e6", corner_radius=8)
        f_stat.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(f_stat, text="📊 Programm- & Beleg-Statistik (Aktive Firma)", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
        
        akt_jahr = str(datetime.now().year)
        starts, out_ges, out_jahr, in_ges, in_jahr = self.berechne_statistiken(akt_jahr)
        
        stat_text = (
            f"• Programstarts insgesamt: {starts}\n\n"
            f"• Ausgangsrechnungen insgesamt: {out_ges}  |  Im laufenden Jahr ({akt_jahr}): {out_jahr}\n"
            f"• Eingangsrechnungen insgesamt: {in_ges}  |  Im laufenden Jahr ({akt_jahr}): {in_jahr}"
        )
        ctk.CTkLabel(f_stat, text=stat_text, justify="left", font=("Helvetica", 12)).pack(pady=(0, 15), padx=20)

    def berechne_statistiken(self, akt_jahr):
        starts = 1
        base_path = self.config.get("base_data_path", "")
        if base_path and os.path.exists(base_path):
            stat_file = os.path.join(base_path, self.p_config["profil_name"].replace(" ", "_"), "stats.json")
            try:
                if os.path.exists(stat_file):
                    with open(stat_file, "r", encoding="utf-8") as sf:
                        data = json.load(sf)
                        starts = data.get("starts", 0) + 1
                with open(stat_file, "w", encoding="utf-8") as sf:
                    json.dump({"starts": starts}, sf)
            except: pass

        out_ges = 0
        out_jahr = 0
        ausw_ordner = self.p_config.get("auswertungen_ordner", "")
        if ausw_ordner and os.path.exists(ausw_ordner):
            for root, dirs, files in os.walk(ausw_ordner):
                for f in files:
                    if re.match(r'^re\d{6}\.csv$', f.lower()):
                        try:
                            with open(os.path.join(root, f), 'r', encoding='utf-8-sig') as csvfile:
                                reader = list(csv.reader(csvfile, delimiter=';'))
                                if len(reader) > 1:
                                    anzahl = len(reader) - 1
                                    out_ges += anzahl
                                    if str(akt_jahr) in f:
                                        out_jahr += anzahl
                        except: pass

        in_ges = 0
        in_jahr = 0
        eingang_ordner = self.p_config.get("eingangsrechnungen_ordner", "")
        if eingang_ordner and os.path.exists(eingang_ordner):
            for root, dirs, files in os.walk(eingang_ordner):
                for f in files:
                    if f.lower().endswith('_leseabschrift.pdf'): continue
                    if f.upper().startswith('ER'):
                        in_ges += 1
                        if os.path.basename(root) == str(akt_jahr):
                            in_jahr += 1

        return starts, out_ges, out_jahr, in_ges, in_jahr

    def open_html_help(self):
        import webbrowser
        try:
            app_dir = get_appdata_dir()
            hilfe_pfad = os.path.join(app_dir, "SokoIur_Hilfe.html")
            if not os.path.exists(hilfe_pfad):
                with open(hilfe_pfad, "w", encoding="utf-8") as f:
                    f.write(hilfe_texte.get_doku_html(getattr(self, 'current_version', '1.000')))
            
            if hasattr(os, 'startfile'):
                os.startfile(hilfe_pfad)
            else:
                hilfe_url = hilfe_pfad.replace("\\", "/")
                webbrowser.open(f"file:///{hilfe_url}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Die Hilfe-Datei konnte nicht geöffnet werden:\n\n{str(e)}", parent=self)

    def open_changelog_html(self):
        import webbrowser
        try:
            app_dir = get_appdata_dir()
            changelog_pfad = os.path.join(app_dir, "changelog.html")
            if not os.path.exists(changelog_pfad):
                with open(changelog_pfad, "w", encoding="utf-8") as f:
                    f.write(hilfe_texte.get_changelog_html(getattr(self, 'current_version', '1.000')))
            
            if hasattr(os, 'startfile'):
                os.startfile(changelog_pfad)
            else:
                hilfe_url = changelog_pfad.replace("\\", "/")
                webbrowser.open(f"file:///{hilfe_url}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Die Changelog-Datei konnte nicht geöffnet werden:\n\n{str(e)}", parent=self)