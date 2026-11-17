"""
tab_manuell.py
--------------
Logik und Aufbau des Reiters "Erstellen" (Manuelle Rechnungseingabe).
"""
import os
import re
import csv
from datetime import datetime, timedelta
import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import filedialog

from config import *
from utils import *
from crud import *
from audit import write_audit_log
from gui_utils import create_tooltip
from pdf_zugferd import run_auto_generation

class TabManuellMixin:
    def on_main_text_vorlage_change(self, wahl):
        vorlagen = self.p_config.get("text_vorlagen", {})
        if wahl in vorlagen:
            v = vorlagen[wahl]
            self.header_text = v.get("header", "")
            self.einleitung_text = v.get("einleitung", "")
            self.vor_gruss_text = v.get("vor_gruss", "")
            self.gruss_text = v.get("gruss", "")
            self.p_config["zahlungsbedingungen_default"] = v.get("zahlungsbedingungen", "")
            self.p_config["rechnungsvermerk_default"] = v.get("rechnungsvermerk", "")
            self.p_config["aktive_text_vorlage"] = wahl
            self.aktive_text_vorlage = wahl
            
            speichere_textdatei(self.p_config.get('header_csv'), self.header_text)
            speichere_textdatei(self.p_config.get('einleitung_csv'), self.einleitung_text)
            speichere_textdatei(self.p_config.get('vor_gruss_csv'), getattr(self, 'vor_gruss_text', ''))
            speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)            
            speichere_config(self.config)
    def open_date_picker(self, entry_widget):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Leistungszeitraum wählen")
        self.center_window(dialog, 400, 250)
        dialog.transient(self); dialog.grab_set()

        ctk.CTkLabel(dialog, text="Datums- oder Zeitraumeingabe", font=("Helvetica", 14, "bold")).pack(pady=10)
        f_start = ctk.CTkFrame(dialog, fg_color="transparent"); f_start.pack(pady=5)
        ctk.CTkLabel(f_start, text="Startdatum:", width=120).pack(side="left")
        e_start = ctk.CTkEntry(f_start, width=150); e_start.pack(side="left")

        f_end = ctk.CTkFrame(dialog, fg_color="transparent"); f_end.pack(pady=5)
        ctk.CTkLabel(f_end, text="Enddatum (opt.):", width=120).pack(side="left")
        e_end = ctk.CTkEntry(f_end, width=150); e_end.pack(side="left")

        existing = entry_widget.get().strip()
        if "|" in existing:
            s, e = existing.split('|')
            e_start.insert(0, s); e_end.insert(0, e)
        else: e_start.insert(0, existing)

        def fill_today(widget):
            widget.delete(0, 'end'); widget.insert(0, datetime.now().strftime("%Y-%m-%d"))

        f_btn = ctk.CTkFrame(dialog, fg_color="transparent"); f_btn.pack(pady=10)
        self.create_button(f_btn, text="Start = Heute", width=110, command=lambda: fill_today(e_start)).pack(side="left", padx=5)
        self.create_button(f_btn, text="Ende = Heute", width=110, command=lambda: fill_today(e_end)).pack(side="left", padx=5)

        def save_date():
            s = parse_flexible_date(e_start.get()); e = parse_flexible_date(e_end.get())
            try:
                if s: datetime.strptime(s, "%Y-%m-%d")
                if e: datetime.strptime(e, "%Y-%m-%d")
            except ValueError:
                return messagebox.showerror("Fehler", "Datumsformat nicht erkannt!", parent=dialog)
            res = f"{s}|{e}" if (s and e) else (s or e)
            entry_widget.delete(0, 'end'); entry_widget.insert(0, res)
            dialog.destroy()

        self.create_button(dialog, text="Übernehmen", command=save_date).pack(pady=10)

    def choose_and_load_csv(self):
        # Den arecsv-Ordner des aktuellen Jahres der aktiven Firma ermitteln
        akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        are_dir = self.p_config.get("ausgabe_ordner", "")
        
        if are_dir:
            start_dir = os.path.join(os.path.dirname(are_dir), "arecsv", akt_jahr)
        else:
            start_dir = os.path.dirname(self.p_config.get('rechnung_csv', ''))
            
        if not os.path.exists(start_dir):
            # Falls das Jahresverzeichnis noch nicht existiert, falle aufs Firmen-Root zurück
            start_dir = os.path.dirname(self.p_config.get('rechnung_csv', ''))
            if not os.path.exists(start_dir):
                start_dir = os.getcwd()
        
        pfad = filedialog.askopenfilename(
            title="Rechnungs-CSV wählen", 
            initialdir=start_dir, 
            filetypes=[("CSV-Dateien", "*.csv*"), ("Alle Dateien", "*.*")]
        )
        if pfad: 
            ensure_utf8_csv(pfad)  # <--- HIER: Konvertierung durchführen, falls nötig
            self.load_manual_invoice(is_button_click=True, custom_path=pfad)        
        


    def open_kunde_search(self, entry_widget=None, mode="name"):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Kunde suchen" if mode == "name" else "Nach Kundennummer suchen")
        self.center_window(dialog, 500, 500)
        dialog.transient(self)
        dialog.grab_set()

        f_search = ctk.CTkFrame(dialog, fg_color="transparent")
        f_search.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(f_search, text="Suchbegriff:").pack(side="left")
        e_search = ctk.CTkEntry(f_search, placeholder_text="Name, Nr. oder Ort...")
        e_search.pack(side="left", fill="x", expand=True, padx=10)
        
        # Vorhandenen Text übernehmen
        if entry_widget:
            bisheriger_text = entry_widget.get().strip()
            if bisheriger_text:
                e_search.insert(0, bisheriger_text)
                
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
            
        def select_kunde(k):
            self.entry_k_name.set(k.get('Name', ''))
            self.entry_k_strasse.delete(0, 'end'); self.entry_k_strasse.insert(0, k.get('Strasse', ''))
            self.entry_k_plz_ort.delete(0, 'end'); self.entry_k_plz_ort.insert(0, k.get('PLZ_Ort', ''))
            self.entry_k_nr.delete(0, 'end'); self.entry_k_nr.insert(0, k.get('KundeNr', ''))
            self.entry_az.delete(0, 'end'); self.entry_az.insert(0, k.get('Aktenzeichen', ''))
            self.entry_k_endpoint.delete(0, 'end'); self.entry_k_endpoint.insert(0, k.get('Endpoint', k.get('Email', '')))
            self.entry_k_endpoint_scheme.delete(0, 'end'); self.entry_k_endpoint_scheme.insert(0, k.get('EndpointScheme', ''))
            dialog.destroy()

        current_results = []

        def update_list(event=None):
            # Ignoriere reine Navigations-Tasten beim Tippen
            if event and event.keysym in ['Up', 'Down', 'Return', 'Escape']:
                return
                
            term = e_search.get().lower().strip()
            for w in scroll.winfo_children(): w.destroy()
            
            results = []
            for k in self.kunden_liste:
                if not term:
                    if mode == "nr" and not k.get('KundeNr', '').strip(): continue
                    results.append(k)
                else:
                    if (term in k.get('Name', '').lower() or 
                        term in k.get('KundeNr', '').lower() or 
                        term in k.get('PLZ_Ort', '').lower()):
                        results.append(k)
            
            nonlocal current_results
            current_results = results[:100]
            btn_list = []
            
            for k in current_results:
                lbl = f"[{k.get('KundeNr', '-')}] {k.get('Name', '')} | {k.get('PLZ_Ort', '')}"
                btn = ctk.CTkButton(scroll, text=lbl, anchor="w", fg_color="#444", hover_color="#666", command=lambda k_obj=k: select_kunde(k_obj))
                btn.pack(fill="x", pady=2)
                btn_list.append(btn)
                
            if len(results) > 100:
                ctk.CTkLabel(scroll, text=f"... und {len(results)-100} weitere. Bitte Suchbegriff verfeinern.", text_color="gray").pack(pady=5)
                
            # --- Tastensteuerung für die Treffer-Buttons ---
            for i, b in enumerate(btn_list):
                # Pfeil Runter springt zum nächsten Button
                if i < len(btn_list) - 1:
                    b.bind('<Down>', lambda e, next_b=btn_list[i+1]: next_b.focus_set())
                # Pfeil Hoch springt nach oben, beim ersten Button geht es zurück ins Suchfeld
                if i > 0:
                    b.bind('<Up>', lambda e, prev_b=btn_list[i-1]: prev_b.focus_set())
                else:
                    b.bind('<Up>', lambda e: e_search.focus_set())
                # Enter übernimmt den fokussierten Button
                b.bind('<Return>', lambda e, k_obj=current_results[i]: select_kunde(k_obj))

        # Live-Suche bei jedem Tastendruck
        e_search.bind('<KeyRelease>', update_list)
        
        # --- Globale Tastensteuerung ---
        # ESC schließt das Fenster immer sofort ohne Übernahme
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
        # Pfeil Runter im Suchfeld springt sofort zum ersten Treffer in der Liste
        def focus_first_result(event):
            children = scroll.winfo_children()
            for w in children:
                if isinstance(w, ctk.CTkButton):
                    w.focus_set()
                    break
        e_search.bind('<Down>', focus_first_result)
        
        # Enter: Wenn es exakt 1 Treffer gibt, wird dieser sofort übernommen!
        def on_enter_search(event):
            if len(current_results) == 1:
                select_kunde(current_results[0])
                
        e_search.bind('<Return>', on_enter_search)
        dialog.bind('<Return>', on_enter_search)  # NEU: Funktioniert jetzt auch, wenn das Fenster selbst den Fokus hat

        # Initiale Liste laden
        update_list()
        
        # NEU: 50 Millisekunden warten, bis das Fenster gezeichnet ist, dann erst Fokus setzen
        dialog.after(50, e_search.focus_set)
        
    def update_totals_ui(self):
        g_netto = g_steuer = 0.0
        steuern = {}
        for p in self.positionen_liste:
            m = safe_float(p.get('Menge', 1)); pr = safe_float(p.get('EinzelpreisNetto', 0)); st = safe_float(p.get('Steuersatz', 19))
            n = m * pr; s = n * (st / 100.0)
            g_netto += n; g_steuer += s
            if st > 0: steuern[st] = steuern.get(st, 0.0) + s
        
        t = f"Netto Gesamt: {f_curr(g_netto)}\n"
        for st, s_wert in sorted(steuern.items()): t += f"+ {f_num(st)}% MwSt: {f_curr(s_wert)}\n"
        t += f"Brutto Gesamt: {f_curr(g_netto + g_steuer)}"
        self.lbl_totals.configure(text=t)

    def build_manuell_tab(self):
        left_frame = ctk.CTkScrollableFrame(self.tab_manuell, width=350); left_frame.pack(side="left", fill="y", padx=10, pady=10)
        right_frame = ctk.CTkFrame(self.tab_manuell); right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        btn_load = self.create_button(left_frame, text="📥 Letzte Rechnungs-CSV laden (Alt+L)", command=lambda: self.load_manual_invoice(is_button_click=True), fg_color="#444", hover_color="#666")
        btn_load.pack(pady=(10, 5), padx=10, fill="x")
        create_tooltip(btn_load, "Lädt den zuletzt bearbeiteten Rechnungsentwurf der aktuellen Firma.")
        
        btn_choose = self.create_button(left_frame, text="📁 Rechnungs-CSV wählen", command=self.choose_and_load_csv, fg_color="#444", hover_color="#666")
        btn_choose.pack(pady=(0, 10), padx=10, fill="x")
        create_tooltip(btn_choose, "Lädt eine alte Rechnung oder einen Entwurf aus einer CSV-Datei.")
        
        ctk.CTkLabel(left_frame, text="Kopfdaten", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.entry_r_nr = self.create_input(left_frame, "Rechnungs-Nr.")
        self.entry_r_datum = self.create_input(left_frame, "Rechnungsdatum")
        self.entry_f_datum = self.create_input(left_frame, "Fälligkeit")
        
        self.chk_raten = ctk.CTkCheckBox(left_frame, text="Ratenzahlung zulassen"); self.chk_raten.pack(pady=3, padx=10, anchor="w")
        if self.p_config.get("keep_raten", False): self.chk_raten.select()
        
        self.entry_k_nr = self.create_input_with_button(left_frame, "Kunden-Nr. (opt.)", "🔍", lambda e: self.open_kunde_search(e, mode="nr"))
        self.entry_k_nr.bind('<Return>', lambda e: self.open_kunde_search(self.entry_k_nr, mode="nr"))
        self.entry_az = self.create_input(left_frame, "Unser Zeichen (opt.)")
        self.entry_k_az = self.create_input(left_frame, "Ihr Zeichen (opt.)")
        self.entry_lz_kopf = self.create_input_with_button(left_frame, "Lz. Kopf (opt.)", "📅", self.open_date_picker)
        self.entry_k_name = self.create_input_with_button(left_frame, "Kunde Name", "🔍", lambda e: self.open_kunde_search(e, mode="name"))
        self.entry_k_name.bind('<Return>', lambda e: self.open_kunde_search(self.entry_k_name, mode="name"))
        self.entry_k_strasse = self.create_input(left_frame, "Kunde Straße")
        self.entry_k_plz_ort = self.create_input(left_frame, "PLZ Ort")
        self.entry_k_endpoint = self.create_input(left_frame, "E-Mail / Leitweg-ID")
        self.entry_k_endpoint_scheme = self.create_input(left_frame, "Endpoint-Schema (z. B. 0204)")
        
        self.chk_kunde_speichern = ctk.CTkCheckBox(left_frame, text="Kunde speichern/updaten"); self.chk_kunde_speichern.pack(pady=3, padx=10, anchor="w")
        if self.p_config.get("keep_kunde_speichern", False): self.chk_kunde_speichern.select()
        
        # --- NEU: Vorlagen-Schnellauswahl & Texte-Button ---
        f_txt_vorlage = ctk.CTkFrame(left_frame, fg_color="transparent")
        f_txt_vorlage.pack(fill="x", padx=10, pady=(10, 2))
        ctk.CTkLabel(f_txt_vorlage, text="Textvorlage:", width=120, anchor="w").pack(side="left")
        vorlagen_namen = list(self.p_config.get("text_vorlagen", {"Standard": {}}).keys())
        self.combo_text_vorlage_main = ctk.CTkComboBox(f_txt_vorlage, values=vorlagen_namen, command=self.on_main_text_vorlage_change)
        self.combo_text_vorlage_main.set(self.p_config.get("aktive_text_vorlage", "Standard"))
        self.combo_text_vorlage_main.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.create_button(left_frame, text="📝 Texte & Vorlagen bearbeiten (Alt+T)", command=self.open_texte_popup).pack(pady=(5, 12), padx=10, fill="x")
        ctk.CTkFrame(left_frame, height=2, fg_color="#555").pack(fill="x", pady=10, padx=10)
        self.lbl_totals = ctk.CTkLabel(left_frame, text="Netto Gesamt: 0,00 €\nBrutto Gesamt: 0,00 €", justify="left", font=("Helvetica", 14, "bold"))
        self.lbl_totals.pack(pady=5, padx=15, anchor="w")
        
        ctk.CTkLabel(right_frame, text="Positionen", font=("Helvetica", 14, "bold")).pack(pady=10)
        self.pos_scroll = ctk.CTkScrollableFrame(right_frame); self.pos_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_button(right_frame, text="+ Position hinzufügen (+)", command=self.open_pos_popup).pack(pady=10)
        # Frame für geteilte Buttons (Test, Papier & XRechnung) ---
        f_split_btns = ctk.CTkFrame(right_frame, fg_color="transparent")
        f_split_btns.pack(pady=5, fill="x", padx=20)
        
        btn_test = self.create_button(f_split_btns, text="Testrechnung", fg_color="#6c757d", hover_color="#5a6268", command=self.generate_testrechnung)
        btn_test.pack(side="left", fill="x", expand=True, padx=(0, 5))
        create_tooltip(btn_test, "Erstellt eine Vorschau (PDF) im Temp-Ordner.\nVergibt keine Rechnungsnummer, erzeugt kein Journal und schließt das Programm nicht.")
        
        btn_papier = self.create_button(f_split_btns, text="Papier-PDF", fg_color="#FFF2A8", text_color="#3D3200", hover_color="#E6D77A", command=self.save_generate_papierrechnung_exit)
        btn_papier.pack(side="left", fill="x", expand=True, padx=(5, 5))
        create_tooltip(btn_papier, "Erstellt ein reines Sicht-PDF ohne elektronische XML-Daten.\n(Nur als Übergangslösung empfohlen)")
        
        btn_xrech = self.create_button(f_split_btns, text="XRechnung", fg_color="#cccccc", hover_color="#14375d", command=self.save_generate_xrechnung_exit)
        btn_xrech.pack(side="left", fill="x", expand=True, padx=(5, 0))
        create_tooltip(btn_xrech, "Erzeugt eine XML-Datei für Behördenportale (Leitweg-ID erforderlich)\nund zusätzlich eine lesbare Leseabschrift (PDF) für Ihre Akten.")
        
        btn_zugferd = self.create_button(right_frame, text="Zugpferdrechnung erstellen & öffnen (Alt+P)", fg_color="#289102", hover_color="#5dc21c", command=self.save_generate_open_exit)
        btn_zugferd.pack(pady=5, fill="x", padx=20)
        create_tooltip(btn_zugferd, "Erzeugt eine ZUGFeRD Hybrid-PDF (PDF inkl. unsichtbarem XML).\nIdeal für Geschäftskunden (B2B) per E-Mail.")

    def load_manual_invoice(self, is_button_click=False, silent=False, custom_path=None):
        rech_pfad = custom_path if custom_path else self.p_config.get('rechnung_csv', '')
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

                # Überschreibt die Nummer aus der CSV mit dem CLI-Parameter (--renr), falls vorhanden
                if not is_button_click and self.config.get("cli_renr"):
                    geladene_nr = self.config.get("cli_renr")

                ziel_nr = geladene_nr
                
                
                if is_button_click and geladene_nr:
                    if messagebox.askyesno("Rechnungsnummer", f"Die Rechnungsnummer {geladene_nr} wurde geladen.\nUm eins erhöhen (Ja) oder beibehalten (Nein)?"):
                        ziel_nr = berechne_naechste_rechnungsnummer(geladene_nr)
                        
                self.entry_r_nr.delete(0, 'end'); self.entry_r_nr.insert(0, ziel_nr)
                self.entry_r_datum.delete(0, 'end'); self.entry_r_datum.insert(0, kopf.get('Rechnungsdatum', ''))
                self.entry_f_datum.delete(0, 'end'); self.entry_f_datum.insert(0, kopf.get('Faelligkeitsdatum', ''))
                self.entry_k_name.set(kopf.get('KundeName', ''))
                self.entry_k_strasse.delete(0, 'end'); self.entry_k_strasse.insert(0, kopf.get('KundeStrasse', ''))
                if str(kopf.get('Ratenzahlung', '')).lower() in ['true', '1', 'ja', 'yes']: self.chk_raten.select()
                else: self.chk_raten.deselect()
                self.entry_k_nr.delete(0, 'end'); 
                self.entry_k_nr.insert(0, kopf.get('KundeNr', ''))
                self.entry_az.delete(0, 'end'); self.entry_az.insert(0, kopf.get('Aktenzeichen', ''))
                self.entry_k_az.delete(0, 'end'); self.entry_k_az.insert(0, self.config.get("cli_kunde_az", kopf.get('KundeAktenzeichen', '')))
                self.entry_lz_kopf.delete(0, 'end'); self.entry_lz_kopf.insert(0, kopf.get('LeistungszeitraumKopf', ''))
                self.entry_k_plz_ort.delete(0, 'end'); self.entry_k_plz_ort.insert(0, f"{kopf.get('KundePLZ', '')} {kopf.get('KundeOrt', '')}".strip())
                self.entry_k_endpoint.delete(0, 'end'); self.entry_k_endpoint.insert(0, kopf.get('KundeEndpoint', kopf.get('KundeEmail', '')))
                self.entry_k_endpoint_scheme.delete(0, 'end'); self.entry_k_endpoint_scheme.insert(0, kopf.get('KundeEndpointScheme', ''))
                
                self.positionen_liste = reader
            
            self.zusatz_dict = {}
            
            # NEU: Anmerkungen nur laden, wenn die reguläre Firmen-Rechnung geladen wird
            # ODER wenn das Fremdprogramm explizit eine Zusatzdatei per CLI übergeben hat.
            # Bei --edit mit einer temporären Rechnung (custom_path) bleiben die alten Anmerkungen leer.
            load_zusatz = True
            if custom_path and not self.config.get("cli_override_zusatz_csv"):
                load_zusatz = False
                
            if load_zusatz and os.path.exists(self.p_config.get('zusatz_csv', '')):
                with open(self.p_config.get('zusatz_csv', ''), mode='r', encoding='utf-8-sig') as f:
                    for line in f:
                        line = line.strip()
                        if line and len(line.split(';', 1)) == 2:
                            pk, txt = line.split(';', 1)
                            for p in pk.strip().split(','): self.zusatz_dict[p.strip()] = txt.strip()
            
            self.header_text = lade_textdatei(self.p_config.get('header_csv', ''))
            self.einleitung_text = lade_textdatei(self.p_config.get('einleitung_csv', ''))
            self.vor_gruss_text = lade_textdatei(self.p_config.get('vor_gruss_csv', ''))
            self.gruss_text = lade_textdatei(self.p_config.get('gruss_csv', ''))
            self.refresh_pos_list()
        except Exception as e:
            if not silent: messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")

    def open_texte_popup(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Texte & Textvorlagen bearbeiten")
        self.center_window(dialog, 680, 720)
        dialog.transient(self)
        dialog.grab_set() 
        
        if "text_vorlagen" not in self.p_config or not isinstance(self.p_config["text_vorlagen"], dict):
            self.p_config["text_vorlagen"] = {}
        if "Standard" not in self.p_config["text_vorlagen"]:
            self.p_config["text_vorlagen"]["Standard"] = {
                "header": self.header_text,
                "einleitung": self.einleitung_text,
                "vor_gruss": getattr(self, "vor_gruss_text", ""),
                "gruss": self.gruss_text,
                "zahlungsbedingungen": self.p_config.get("zahlungsbedingungen_default", ""),
                "rechnungsvermerk": self.p_config.get("rechnungsvermerk_default", "")
            }

        # 1. Kopfbereich für die Vorlagenverwaltung (Dropdown + Buttons)
        f_top = ctk.CTkFrame(dialog, corner_radius=8)
        f_top.pack(side="top", fill="x", padx=15, pady=(12, 5))
        
        f_vorlage_row1 = ctk.CTkFrame(f_top, fg_color="transparent")
        f_vorlage_row1.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(f_vorlage_row1, text="Textkombination / Vorlage:", font=("Helvetica", 13, "bold")).pack(side="left")
        
        def get_vorlagen_liste():
            keys = list(self.p_config["text_vorlagen"].keys())
            if "Standard" in keys:
                keys.remove("Standard")
                keys.insert(0, "Standard")
            return keys

        def load_vorlage_into_fields(name):
            v = self.p_config["text_vorlagen"].get(name)
            if not v:
                return
            t_head.delete("0.0", "end"); t_head.insert("0.0", v.get("header", ""))
            t_einl.delete("0.0", "end"); t_einl.insert("0.0", v.get("einleitung", ""))
            t_vor_gruss.delete("0.0", "end"); t_vor_gruss.insert("0.0", v.get("vor_gruss", ""))
            t_gruss.delete("0.0", "end"); t_gruss.insert("0.0", v.get("gruss", ""))
            t_zahl.delete("0.0", "end"); t_zahl.insert("0.0", v.get("zahlungsbedingungen", ""))
            t_verm.delete("0.0", "end"); t_verm.insert("0.0", v.get("rechnungsvermerk", ""))
            self.p_config["aktive_text_vorlage"] = name
            self.aktive_text_vorlage = name

        combo_vorlage = ctk.CTkComboBox(f_vorlage_row1, values=get_vorlagen_liste(), width=260, command=load_vorlage_into_fields)
        akt_v = self.p_config.get("aktive_text_vorlage", "Standard")
        combo_vorlage.set(akt_v if akt_v in self.p_config["text_vorlagen"] else "Standard")
        combo_vorlage.pack(side="left", padx=10, fill="x", expand=True)

        f_vorlage_row2 = ctk.CTkFrame(f_top, fg_color="transparent")
        f_vorlage_row2.pack(fill="x", padx=10, pady=(4, 8))

        def get_current_fields_dict():
            return {
                "header": t_head.get("0.0", "end").strip(),
                "einleitung": t_einl.get("0.0", "end").strip(),
                "vor_gruss": t_vor_gruss.get("0.0", "end").strip(),
                "gruss": t_gruss.get("0.0", "end").strip(),
                "zahlungsbedingungen": t_zahl.get("0.0", "end").strip(),
                "rechnungsvermerk": t_verm.get("0.0", "end").strip()
            }

        def save_current_vorlage():
            name = combo_vorlage.get().strip() or "Standard"
            self.p_config["text_vorlagen"][name] = get_current_fields_dict()
            self.p_config["aktive_text_vorlage"] = name
            speichere_config(self.config)
            if hasattr(self, "combo_text_vorlage_main"):
                self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                self.combo_text_vorlage_main.set(name)
            messagebox.showinfo("Vorlage gespeichert", f"Die Textkombination wurde in der Vorlage '{name}' dauerhaft gespeichert.", parent=dialog)

        def save_as_standard():
            self.p_config["text_vorlagen"]["Standard"] = get_current_fields_dict()
            self.p_config["aktive_text_vorlage"] = "Standard"
            combo_vorlage.configure(values=get_vorlagen_liste())
            combo_vorlage.set("Standard")
            speichere_config(self.config)
            if hasattr(self, "combo_text_vorlage_main"):
                self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                self.combo_text_vorlage_main.set("Standard")
            messagebox.showinfo("Standard gespeichert", "Die aktuellen Texte wurden als 'Standard' gespeichert.", parent=dialog)

        def save_new_vorlage():
            inp = ctk.CTkInputDialog(
                text="Name der neuen Textkombination\n(z. B. Vorschussrechnung, Kostenfestsetzungsantrag):",
                title="Neue Textvorlage speichern"
            )
            new_name = inp.get_input()
            if new_name and new_name.strip():
                new_name = new_name.strip()
                self.p_config["text_vorlagen"][new_name] = get_current_fields_dict()
                self.p_config["aktive_text_vorlage"] = new_name
                combo_vorlage.configure(values=get_vorlagen_liste())
                combo_vorlage.set(new_name)
                speichere_config(self.config)
                if hasattr(self, "combo_text_vorlage_main"):
                    self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                    self.combo_text_vorlage_main.set(new_name)
                messagebox.showinfo("Vorlage angelegt", f"Die Vorlage '{new_name}' wurde gespeichert und ausgewählt.", parent=dialog)

        def delete_vorlage():
            name = combo_vorlage.get().strip()
            if name == "Standard":
                return messagebox.showwarning("Nicht möglich", "Die Vorlage 'Standard' kann nicht gelöscht werden.", parent=dialog)
            if name in self.p_config["text_vorlagen"]:
                if messagebox.askyesno("Vorlage löschen", f"Möchten Sie die Vorlage '{name}' wirklich löschen?", parent=dialog):
                    del self.p_config["text_vorlagen"][name]
                    combo_vorlage.configure(values=get_vorlagen_liste())
                    combo_vorlage.set("Standard")
                    load_vorlage_into_fields("Standard")
                    speichere_config(self.config)
                    if hasattr(self, "combo_text_vorlage_main"):
                        self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                        self.combo_text_vorlage_main.set("Standard")

        self.create_button(f_vorlage_row2, text="💾 Vorlage aktualisieren", width=150, command=save_current_vorlage).pack(side="left", padx=(0, 5))
        self.create_button(f_vorlage_row2, text="⭐ Als Standard speichern", width=165, fg_color="#1f538d", hover_color="#14375d", command=save_as_standard).pack(side="left", padx=5)
        self.create_button(f_vorlage_row2, text="➕ Als neue Vorlage...", width=155, fg_color="#289102", hover_color="#1e6e01", command=save_new_vorlage).pack(side="left", padx=5)
        self.create_button(f_vorlage_row2, text="🗑 Löschen", width=90, fg_color="#b30000", hover_color="#800000", command=delete_vorlage).pack(side="right", padx=(5, 0))

        # 2. Feststehender Bereich unten für den Übernehmen-Button
        f_btn = ctk.CTkFrame(dialog, fg_color="transparent")
        f_btn.pack(side="bottom", fill="x", pady=10)
        
        # 3. Scrollbarer Bereich für die Textfelder (ohne "Merken"-Checkboxen)
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=15, pady=5)
        
        ctk.CTkLabel(scroll, text="Zentrierter Header (über Rechnungs-Nr.):").pack(anchor="w", padx=20, pady=(8, 0))
        t_head = ctk.CTkTextbox(scroll, height=55); t_head.pack(fill="x", padx=20, pady=(2, 8)); t_head.insert("0.0", self.header_text)
        
        ctk.CTkLabel(scroll, text="Einleitung (vor Positionen):").pack(anchor="w", padx=20, pady=(4, 0))
        t_einl = ctk.CTkTextbox(scroll, height=70); t_einl.pack(fill="x", padx=20, pady=(2, 8)); t_einl.insert("0.0", self.einleitung_text)

        ctk.CTkLabel(scroll, text="Vor Gruß (nach Zahlungshinweis / vor Gruß):").pack(anchor="w", padx=20, pady=(4, 0))
        t_vor_gruss = ctk.CTkTextbox(scroll, height=70); t_vor_gruss.pack(fill="x", padx=20, pady=(2, 8)); t_vor_gruss.insert("0.0", getattr(self, "vor_gruss_text", ""))
        
        ctk.CTkLabel(scroll, text="Gruß (unten):").pack(anchor="w", padx=20, pady=(4, 0))
        t_gruss = ctk.CTkTextbox(scroll, height=70); t_gruss.pack(fill="x", padx=20, pady=(2, 8)); t_gruss.insert("0.0", self.gruss_text)
        
        ctk.CTkLabel(scroll, text="ℹ️ Offizielle Hinweise zur Nutzung von BT-20 und BT-22 nach EN 16931 finden Sie im Handbuch (Kapitel 9).", text_color="#1f538d", font=("Helvetica", 11, "italic")).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(scroll, text="Zahlungsbedingungen (BT-20 - Fälligkeitshinweis):").pack(anchor="w", padx=20, pady=(4, 0))
        t_zahl = ctk.CTkTextbox(scroll, height=45); t_zahl.pack(fill="x", padx=20, pady=(2, 8))
        t_zahl.insert("0.0", self.p_config.get("zahlungsbedingungen_default", ""))

        ctk.CTkLabel(scroll, text="Rechnungsvermerk / Dauerrechnung (BT-22):").pack(anchor="w", padx=20, pady=(4, 0))
        t_verm = ctk.CTkTextbox(scroll, height=45); t_verm.pack(fill="x", padx=20, pady=(2, 8))
        t_verm.insert("0.0", self.p_config.get("rechnungsvermerk_default", ""))

        def save_texte():
            self.header_text = t_head.get("0.0", "end").strip()
            self.einleitung_text = t_einl.get("0.0", "end").strip()
            self.vor_gruss_text = t_vor_gruss.get("0.0", "end").strip()
            self.gruss_text = t_gruss.get("0.0", "end").strip()
            
            self.p_config["zahlungsbedingungen_default"] = t_zahl.get("0.0", "end").strip()
            self.p_config["rechnungsvermerk_default"] = t_verm.get("0.0", "end").strip()
            
            akt_name = combo_vorlage.get().strip() or "Standard"
            self.p_config["aktive_text_vorlage"] = akt_name
            self.aktive_text_vorlage = akt_name

            # Arbeitsdateien für die aktuelle PDF-Erstellung schreiben
            speichere_textdatei(self.p_config.get('header_csv'), self.header_text)
            speichere_textdatei(self.p_config.get('einleitung_csv'), self.einleitung_text)
            speichere_textdatei(self.p_config.get('vor_gruss_csv'), self.vor_gruss_text)
            speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)
            
            if hasattr(self, "combo_text_vorlage_main"):
                self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                self.combo_text_vorlage_main.set(akt_name)

            speichere_config(self.config)
            dialog.destroy()
                    
        self.create_button(f_btn, text="Übernehmen & Schließen", width=220, command=save_texte).pack(pady=5)
    
    def open_pos_popup(self, edit_index=None):
        briefbogen_pfad = self.p_config.get('briefbogen_pdf', '')
        
        if not os.path.exists(briefbogen_pfad):
            messagebox.showwarning(
                "Briefbogen fehlt",
                f"Ohne briefbogen.pdf macht eine Rechnungserstellung wenig Sinn!\n\n"
                f"Bitte speichern Sie den Briefbogen unter folgendem Pfad ab:\n"
                f"{briefbogen_pfad}\n\n"
                f"Weitere Hinweise und Formatierungsanforderungen finden Sie im Handbuch unter 'Infos'."
            )
            return  # Bricht das Öffnen des Positions-Popups ab
        dialog = ctk.CTkToplevel(self); dialog.title("Position bearbeiten" if edit_index is not None else "Neue Position")
        self.center_window(dialog, 600, 390); dialog.transient(self); dialog.grab_set() 
        
        prod_namen = [p['Bezeichnung'] for p in self.produkte_liste]
        def prod_auswahl(wahl):
            for p in self.produkte_liste:
                if p['Bezeichnung'] == wahl:
                    e_menge.delete(0, 'end'); e_menge.insert(0, p.get('Menge', '1'))
                    e_preis.delete(0, 'end'); e_preis.insert(0, p.get('EinzelpreisNetto', '0'))
                    e_steuer.delete(0, 'end'); e_steuer.insert(0, p.get('Steuersatz', '19'))
                    c = p.get('Einheit', 'C62')
                    for val in EINHEITEN_LISTE:
                        if c in val or EINHEITEN_MAPPING.get(c, c) in val: e_einheit.set(val); break
                    break

        e_bez = self.create_input(dialog, "Bezeichnung", is_combo=True, combo_values=prod_namen, command=prod_auswahl)
        e_menge = self.create_input(dialog, "Menge")
        e_einheit = self.create_input(dialog, "Einheit", is_combo=True, combo_values=EINHEITEN_LISTE)
        e_preis = self.create_input(dialog, "Einzelpreis (€)")
        e_steuer = self.create_input(dialog, "Steuer (%)")
        e_lz_pos = self.create_input_with_button(dialog, "Lz. Position", "📅", self.open_date_picker)
        
        ex_notes = list(set([v.replace('~cr', '\\n') for k, v in self.zusatz_dict.items() if k != '0']))
        ex_notes.insert(0, "")
        e_anmerkung = self.create_input(dialog, "Anmerkung", is_combo=True, combo_values=ex_notes)
        
        if edit_index is None:
            e_menge.insert(0, "1"); e_einheit.set(self.p_config.get("letzte_einheit", "Stück (C62)"))
            e_steuer.insert(0, "19"); e_anmerkung.set(""); e_bez.set("")
        else:
            p = self.positionen_liste[edit_index]
            e_bez.set(p.get('Bezeichnung', '')); e_menge.insert(0, f"{safe_float(p.get('Menge', 1)):g}")
            e_preis.insert(0, p.get('EinzelpreisNetto', '')); e_steuer.insert(0, p.get('Steuersatz', '19'))
            e_lz_pos.insert(0, p.get('LeistungszeitraumPos', ''))
            e_anmerkung.set(self.zusatz_dict.get(p.get('PosNr'), "").replace('~cr', '\\n'))
            c = p.get('Einheit', 'C62')
            for val in EINHEITEN_LISTE:
                if c in val or EINHEITEN_MAPPING.get(c, c) in val: e_einheit.set(val); break
            
        e_bez.focus_set()
        def save_it(event=None):
            if not e_bez.get().strip(): return messagebox.showwarning("Fehler", "Bezeichnung fehlt!", parent=dialog)
            try:
                float(e_menge.get().replace(',', '.') or "1"); float(e_preis.get().replace(',', '.') or "0.0"); float(e_steuer.get().replace(',', '.') or "19")
            except ValueError: return messagebox.showwarning("Fehler", "Eingaben müssen Zahlen sein!", parent=dialog)
                
            lz_pos_val = parse_flexible_date_span(e_lz_pos.get())
            einheit_code = re.search(r'\((.*?)\)', e_einheit.get()).group(1).strip() if re.search(r'\((.*?)\)', e_einheit.get()) else e_einheit.get().strip()
            
            self.p_config["letzte_einheit"] = e_einheit.get(); speichere_config(self.config)
            
            pos_nr = str(edit_index + 1) if edit_index is not None else str(len(self.positionen_liste) + 1)
            new_data = {
                'PosNr': pos_nr, 'Menge': e_menge.get() or "1", 'Einheit': einheit_code,
                'Bezeichnung': e_bez.get(), 'EinzelpreisNetto': e_preis.get().replace(',','.'),
                'Steuersatz': e_steuer.get() or "19", 'LeistungszeitraumPos': lz_pos_val
            }
            if edit_index is not None: self.positionen_liste[edit_index] = new_data
            else: self.positionen_liste.append(new_data)
                
            anm_txt = e_anmerkung.get().strip()
            if anm_txt: self.zusatz_dict[pos_nr] = anm_txt.replace('\\n', '~cr')
            else: self.zusatz_dict.pop(pos_nr, None)
                
            self.refresh_pos_list(); dialog.destroy()
            
        self.create_button(dialog, text="Speichern", command=save_it).pack(pady=15)
        dialog.bind('<Return>', save_it)

    def delete_pos(self, index):
        if messagebox.askyesno("Löschen", "Position wirklich löschen?"):
            del self.positionen_liste[index]
            new_zusatz = {'0': self.zusatz_dict['0']} if '0' in self.zusatz_dict else {}
            for i, p in enumerate(self.positionen_liste):
                old_nr = p['PosNr']; new_nr = str(i + 1); p['PosNr'] = new_nr
                if old_nr in self.zusatz_dict: new_zusatz[new_nr] = self.zusatz_dict[old_nr]
            self.zusatz_dict = new_zusatz
            self.refresh_pos_list()

    def refresh_pos_list(self):
        for widget in self.pos_scroll.winfo_children(): widget.destroy()
        for idx, p in enumerate(self.positionen_liste):
            f = ctk.CTkFrame(self.pos_scroll); f.pack(fill="x", pady=2)
            self.create_button(f, text="🗑", width=30, fg_color="#b30000", hover_color="#800000", command=lambda i=idx: self.delete_pos(i)).pack(side="right", padx=5, pady=5)
            self.create_button(f, text="✎", width=30, fg_color="#555", hover_color="#777", command=lambda i=idx: self.open_pos_popup(i)).pack(side="right", padx=5, pady=5)
            code = p.get('Einheit', 'C62'); bez = p.get('Bezeichnung', '')
            if len(bez) > 40: bez = bez[:37] + "..."
            lbl_text = f"[{p.get('PosNr', '')}] {bez} | {f_num(safe_float(p.get('Menge', 1)))} {EINHEITEN_MAPPING.get(code, code)} | {f_curr(safe_float(p.get('EinzelpreisNetto', 0)))}"
            ctk.CTkLabel(f, text=lbl_text, anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=5)
        self.update_totals_ui()

    def save_manual_invoice(self, silent=False, require_buyer_endpoint=False):
        # Vor dem Speichern sicherstellen, dass der Lock aktiv ist
        if hasattr(self, 'check_and_handle_lock') and not self.check_and_handle_lock("📝 ERSTELLEN"):
            return False
        self.set_firm_lock()
        if not self.positionen_liste: 
            messagebox.showwarning("Fehler", "Bitte erfassen Sie zunächst Positionen!")
            return False
            
        r_datum = parse_flexible_date(self.entry_r_datum.get())
        f_datum = parse_flexible_date(self.entry_f_datum.get())
        lz_kopf = parse_flexible_date_span(self.entry_lz_kopf.get())
        try:
            datetime.strptime(r_datum, "%Y-%m-%d")
            datetime.strptime(f_datum, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Fehler", "Datumsangaben fehlerhaft!")
            return False
            
        self.entry_r_datum.delete(0, 'end'); self.entry_r_datum.insert(0, r_datum)
        self.entry_f_datum.delete(0, 'end'); self.entry_f_datum.insert(0, f_datum)
        self.entry_lz_kopf.delete(0, 'end'); self.entry_lz_kopf.insert(0, lz_kopf)
        r_nr = self.entry_r_nr.get().strip()
        
        # --- PRÜFUNG AUF BEREITS EXISTIERENDE RECHNUNGSNUMMER ---
        rechnungs_csv_pfad = self.p_config.get('rechnung_csv', 'rechnung.csv')
        existierende_rechnungen = lade_rechnungen(rechnungs_csv_pfad)
        
        if r_nr in existierende_rechnungen:
            alle_r_nummern = list(existierende_rechnungen.keys())
            ist_letzte_rechnung = (r_nr == alle_r_nummern[-1]) if alle_r_nummern else False
            
            warn_text = (
                f"⚠️ Die Rechnungsnummer '{r_nr}' wurde bereits verwendet!\n\n"
                f"Die Änderung einer bereits erstellten Rechnung kann problematisch sein.\n"
            )
            
            if not ist_letzte_rechnung:
                warn_text += (
                    "HINWEIS: Da es sich NICHT um die allerletzte erstellte Rechnung handelt, "
                    "wird diese Änderung im Journal erfasst, was zu einer Unstimmigkeit des Journals führt!\n\n"
                )
            
            warn_text += (
                "Es ist grundsätzlich besser, eine Stornorechnung zu erfassen und die Rechnung "
                "dann neu zu erstellen.\n\n"
                "Möchten Sie die Rechnungsnummer dennoch erneut erstellen / überschreiben?"
            )
            
            if not messagebox.askyesno("Rechnungsnummer bereits vergeben", warn_text, default="no"):
                return False
                
            if not ist_letzte_rechnung:
                messagebox.showerror(
                    "Überschreiben nicht zulässig", 
                    "Da es sich nicht um die letzte erstellte Rechnung handelt, kann die Zeile aus Sicherheitsgründen nicht überschrieben werden."
                )
                return False
            
            # Audit-Log Begründung abfragen
            audit_bemerkung = ""
            if self.p_config.get("audit_reason_required", False):
                d_audit = ctk.CTkInputDialog(text=f"Bitte geben Sie den Grund für die Änderung der Rechnung '{r_nr}' an (Audit-Log):", title="GoBD: Begründung erforderlich")
                audit_bemerkung = d_audit.get_input()
                if not audit_bemerkung:
                    messagebox.showwarning("Abbruch", "Ohne Begründung darf die Rechnung nicht geändert werden.")
                    return False
            audit_aktion = "Geändert"
        else:
            audit_bemerkung = ""
            audit_aktion = "Erstellt"

        plz_ort = self.entry_k_plz_ort.get().split(' ', 1)
        plz = plz_ort[0] if len(plz_ort) > 0 else ""
        ort = plz_ort[1] if len(plz_ort) > 1 else ""
    
        
        buyer_endpoint = self.entry_k_endpoint.get().strip()
        buyer_scheme = self.entry_k_endpoint_scheme.get().strip()
        if buyer_endpoint and not buyer_scheme and '@' in buyer_endpoint:
            buyer_scheme = 'EM'
        if require_buyer_endpoint and buyer_endpoint and not buyer_scheme:
            messagebox.showwarning("Fehler", "Für eine Leitweg-ID muss das Endpoint-Schema angegeben werden (regelmäßig 0204).")
            return False
        if require_buyer_endpoint and not buyer_endpoint:
            messagebox.showwarning("Fehler", "Für XRechnung/ZUGFeRD ist eine elektronische Käuferadresse erforderlich: E-Mail-Adresse oder Leitweg-ID eintragen.")
            return False

        full_positions = []
        for p in self.positionen_liste:
            p_copy = p.copy()
            p_copy.update({
                'Rechnungsnummer': r_nr,
                'Rechnungsdatum': r_datum,
                'Faelligkeitsdatum': f_datum,
                'KundeName': self.entry_k_name.get(),
                'KundeStrasse': self.entry_k_strasse.get(),
                'KundePLZ': plz,                
                'KundeOrt': ort,
                'KundeLand': 'DE',
                # Optional: elektronische Empfängeradresse (E-Mail oder Leitweg-ID).
                'KundeEmail': buyer_endpoint if '@' in buyer_endpoint else '', 'KundeEndpoint': buyer_endpoint, 'KundeEndpointScheme': buyer_scheme,
                'Zusatztext': '',
                'KundeNr': self.entry_k_nr.get().strip(),
                'Aktenzeichen': self.entry_az.get().strip(),
                'KundeAktenzeichen': self.entry_k_az.get().strip(),
                'LeistungszeitraumKopf': lz_kopf,
                'Ratenzahlung': str(bool(self.chk_raten.get())),
#                'Zahlungsbedingungen': self.p_config.get("zahlungsbedingungen_default", ""),
#                'Rechnungsvermerk': self.p_config.get("rechnungsvermerk_default", "")
                })
            full_positions.append(p_copy)
            
        fieldnames = ['Rechnungsnummer', 'Rechnungsdatum', 'Faelligkeitsdatum', 'KundeName', 'KundeStrasse', 'KundePLZ', 'KundeOrt', 'KundeLand', 'KundeEmail', 'KundeEndpoint', 'KundeEndpointScheme', 'KundeNr', 'Aktenzeichen', 'KundeAktenzeichen', 'LeistungszeitraumKopf', 'Ratenzahlung', 'PosNr', 'Menge', 'Einheit', 'Bezeichnung', 'EinzelpreisNetto', 'Steuersatz', 'Zusatztext', 'LeistungszeitraumPos']
        
        try:
            with open(self.p_config['rechnung_csv'], 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';'); writer.writeheader(); writer.writerows(full_positions)
                
            # --- NEU: Rechnung separat als CSV in arecsv/Jahr abspeichern ---
            akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
            are_dir = self.p_config.get("ausgabe_ordner", "")
            if are_dir:
                # Sucht den Firmen-Basisordner und hängt arecsv/Jahr an
                arecsv_dir = os.path.join(os.path.dirname(are_dir), "arecsv", akt_jahr)
                os.makedirs(arecsv_dir, exist_ok=True)
                csv_archiv_pfad = os.path.join(arecsv_dir, f"Rechnung_{r_nr}.csv")
                with open(csv_archiv_pfad, 'w', newline='', encoding='utf-8-sig') as f_csv:
                    writer_csv = csv.DictWriter(f_csv, fieldnames=fieldnames, delimiter=';')
                    writer_csv.writeheader()
                    writer_csv.writerows(full_positions)

            with open(self.p_config['zusatz_csv'], 'w', encoding='utf-8-sig') as f:
                text_to_pos = {}
                for k, v in self.zusatz_dict.items():
                    if k == '0': continue
                    if v not in text_to_pos: text_to_pos[v] = []
                    text_to_pos[v].append(int(k))
                if '0' in self.zusatz_dict: f.write(f"0;{self.zusatz_dict['0']}\n")
                for text, pos_list in text_to_pos.items():
                    f.write(f"{','.join(map(str, sorted(pos_list)))};{text}\n")

            speichere_textdatei(self.p_config.get('header_csv'), self.header_text)
            speichere_textdatei(self.p_config.get('einleitung_csv'), self.einleitung_text)
            speichere_textdatei(self.p_config.get('vor_gruss_csv'), getattr(self, 'vor_gruss_text', ''))
            speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)
            
            if self.chk_kunde_speichern.get() and self.entry_k_name.get().strip():
                speichere_kunde(self.p_config.get("kunden_csv", "kunden.csv"), {'Name': self.entry_k_name.get().strip(), 'Strasse': self.entry_k_strasse.get().strip(), 'PLZ_Ort': self.entry_k_plz_ort.get().strip(), 'Land': 'DE', 'KundeNr': self.entry_k_nr.get().strip(), 'Aktenzeichen': self.entry_az.get().strip(), 'KundeAktenzeichen': self.entry_k_az.get().strip(), 'Endpoint': buyer_endpoint, 'EndpointScheme': buyer_scheme})
                self.kunden_liste = lade_kunden(self.p_config.get("kunden_csv", "kunden.csv"))
                
            self.p_config['letzte_rechnungsnummer'] = r_nr
            self.p_config['keep_raten'] = bool(self.chk_raten.get()); self.p_config['keep_kunde_speichern'] = bool(self.chk_kunde_speichern.get())
            speichere_config(self.config)
            # Audit-Log schreiben
            base_data_path = self.config.get("base_data_path", "")
            if base_data_path:
                firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_"))
                modus = "CLI (--edit)" if self.start_in_edit else "GUI"
                write_audit_log(firm_dir, "Ausgang", audit_aktion, r_nr, audit_bemerkung, modus)
            if not silent: messagebox.showinfo("Erfolg", "Ihre Daten wurden erfolgreich gespeichert!")
            return True
        except Exception as e:
            messagebox.showerror("Fehler", str(e)); return False

    def generate_testrechnung(self):
        if not self.positionen_liste:
            return messagebox.showwarning("Fehler", "Bitte erfassen Sie Positionen!")
        
        valid, lz_msg = check_lz_logic(
            {'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())},
            [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste]
        )
        if not valid:
            return messagebox.showwarning("Prüfung fehlgeschlagen", lz_msg)

        r_datum = parse_flexible_date(self.entry_r_datum.get())
        f_datum = parse_flexible_date(self.entry_f_datum.get())
        lz_kopf = parse_flexible_date_span(self.entry_lz_kopf.get())
        plz_ort = self.entry_k_plz_ort.get().split(' ', 1)
        plz = plz_ort[0] if len(plz_ort) > 0 else ""
        ort = plz_ort[1] if len(plz_ort) > 1 else ""

        # Dummy-Kopfdaten für die Testrechnung bauen (ohne echtes Speichern der Nummer)
        kopf = {
            'Rechnungsnummer': '',
            'Rechnungsdatum': r_datum,
            'Faelligkeitsdatum': f_datum,
            'KundeName': self.entry_k_name.get(),
            'KundeStrasse': self.entry_k_strasse.get(),
            'KundePLZ': plz,
            'KundeOrt': ort,
            'KundeLand': 'DE',
            'KundeEmail': self.entry_k_endpoint.get() if '@' in self.entry_k_endpoint.get() else '',
            'KundeEndpoint': self.entry_k_endpoint.get(),
            'KundeEndpointScheme': self.entry_k_endpoint_scheme.get(),
            'Zusatztext': '',
            'KundeNr': self.entry_k_nr.get().strip(),
            'Aktenzeichen': self.entry_az.get().strip(),
            'KundeAktenzeichen': self.entry_k_az.get().strip(),
            'LeistungszeitraumKopf': lz_kopf,
            'Ratenzahlung': str(bool(self.chk_raten.get()))
        }
        rechnung_daten = {'kopf': kopf, 'positionen': self.positionen_liste}
        
        # Zusatztexte aus dem Dictionary für den PDF-Generator als Liste aufbereiten
        zusatztexte = [{'pos': k, 'text': v.replace('~cr', '\n')} for k, v in self.zusatz_dict.items()]

        from pdf_zugferd import erstelle_testrechnung
        act_prof = self.p_config
        firma = lade_firma(act_prof['firma_csv'])

        try:
            pdf_pfad = erstelle_testrechnung(
                firma, rechnung_daten, act_prof['briefbogen_pdf'],
                zusatztexte, self.gruss_text, self.header_text, self.einleitung_text,
                getattr(self, 'vor_gruss_text', '')
            )
            import os
            os.startfile(pdf_pfad) # Öffnet die PDF, schließt das Programm aber NICHT.
        except Exception as e:
            messagebox.showerror("Fehler bei der Testrechnung", str(e))

    def save_generate_papierrechnung_exit(self):
        """Erstellt eine reine Sicht-PDF als vorübergehende Übergangsfunktion."""
        if not self.positionen_liste:
            return messagebox.showwarning("Fehler", "Bitte erfassen Sie Positionen!")
        valid, lz_msg = check_lz_logic(
            {'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())},
            [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste]
        )
        if not valid:
            messagebox.showwarning("Prüfung fehlgeschlagen", lz_msg)
            return
        # Die Papier-PDF benötigt keinen elektronischen Käufer-Endpoint.
        if not self.save_manual_invoice(silent=True, require_buyer_endpoint=False):
            return
        from pdf_zugferd import erstelle_papierrechnung
        act_prof = self.p_config
        firma = lade_firma(act_prof['firma_csv'])
        rechnungen = lade_rechnungen(act_prof['rechnung_csv'])
        r_nr = self.entry_r_nr.get().strip()
        daten = rechnungen.get(r_nr)
        if not daten:
            messagebox.showerror("Papierrechnung konnte nicht erstellt werden", f"Die gespeicherte Rechnung '{r_nr}' wurde nicht gefunden.")
            return
        try:
            pdf_pfad = erstelle_papierrechnung(
                firma, daten, act_prof['briefbogen_pdf'],
                lade_zusatz_csv(act_prof['zusatz_csv']), self.gruss_text,
                self.header_text, self.einleitung_text,
                act_prof['ausgabe_ordner'], act_prof['auswertungen_ordner'],
                act_prof.get("aktuelles_rechnungsjahr", str(datetime.now().year)),
                getattr(self, 'vor_gruss_text', '')
            )
            
        except Exception as e:
            messagebox.showerror("Papierrechnung konnte nicht erstellt werden", str(e))
            return
        if not os.path.isfile(pdf_pfad):
            messagebox.showerror("Papierrechnung konnte nicht erstellt werden", "Die PDF-Datei wurde nicht angelegt.")
            return
        kopie_dir = self.config.get("cli_kopie")
        if kopie_dir:
            try:
                os.makedirs(kopie_dir, exist_ok=True)
                shutil.copy2(pdf_pfad, os.path.join(kopie_dir, os.path.basename(pdf_pfad)))
            except Exception as e:
                print(f"Fehler beim Kopieren: {e}")
        if not self.config.get("cli_no_open", False):
            try:
                os.startfile(pdf_pfad)
            except Exception:
                pass
        self.on_closing(skip_warning=True)

    def save_generate_xrechnung_exit(self):
        if not self.positionen_liste: return messagebox.showwarning("Fehler", "Bitte erfassen Sie Positionen!")
        valid, lz_msg = check_lz_logic({'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())}, [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste])
        if not valid:
            # HIER DIE FEHLERMELDUNG ERGÄNZEN:
            messagebox.showwarning("Prüfung fehlgeschlagen", lz_msg)
            return
            
        if not self.save_manual_invoice(silent=True, require_buyer_endpoint=True): return
        
        from pdf_zugferd import erstelle_xrechnung
        act_prof = self.p_config
        firma = lade_firma(act_prof['firma_csv'])
        rechnungen = lade_rechnungen(act_prof['rechnung_csv'])
        zusatztexte = lade_zusatz_csv(act_prof['zusatz_csv'])
        gruss = lade_textdatei(act_prof['gruss_csv'])
        header = lade_textdatei(act_prof['header_csv'])
        einleitung = lade_textdatei(act_prof['einleitung_csv'])
        akt_jahr = act_prof.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        
        r_nr = self.entry_r_nr.get().strip()
        daten = rechnungen.get(r_nr)
        if not daten:
            messagebox.showerror("XRechnung konnte nicht erstellt werden", f"Die gespeicherte Rechnung '{r_nr}' wurde nicht gefunden.")
            return
        try:
            xml_p, pdf_p = erstelle_xrechnung(
                firma, daten, act_prof['briefbogen_pdf'],
                zusatztexte, self.gruss_text, self.header_text, self.einleitung_text,
                act_prof['ausgabe_ordner'], act_prof['auswertungen_ordner'], akt_jahr,
                getattr(self, 'vor_gruss_text', '')
            )
        except Exception as e:
            messagebox.showerror("XRechnung konnte nicht erstellt werden", str(e))
            return
        if not (os.path.isfile(xml_p) and os.path.isfile(pdf_p)):
            messagebox.showerror("XRechnung konnte nicht erstellt werden", "XML oder Begleit-PDF wurde nicht angelegt.")
            return
        kopie_dir = self.config.get("cli_kopie")
        if kopie_dir:
            try:
                os.makedirs(kopie_dir, exist_ok=True)
                if os.path.isfile(xml_p): shutil.copy2(xml_p, os.path.join(kopie_dir, os.path.basename(xml_p)))
                if os.path.isfile(pdf_p): shutil.copy2(pdf_p, os.path.join(kopie_dir, os.path.basename(pdf_p)))
            except Exception as e:
                print(f"Fehler beim Kopieren: {e}")

        # Nach erfolgreicher Erstellung Zielordner öffnen und Anwendung ohne Meldung beenden.
        ziel_ordner = os.path.dirname(pdf_p)
        if os.path.exists(ziel_ordner):
            try:
                import subprocess
                subprocess.Popen(['explorer', ziel_ordner])
            except Exception:
                try:
                    os.startfile(ziel_ordner)
                except Exception:
                    pass
        self.on_closing(skip_warning=True)

    def save_generate_open_exit(self):
        if not self.positionen_liste: return messagebox.showwarning("Fehler", "Bitte erfassen Sie Positionen!")
        
        valid, lz_msg = check_lz_logic({'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())}, [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste])
        if not valid:
            # HIER DIE FEHLERMELDUNG ERGÄNZEN:
            messagebox.showwarning("Prüfung fehlgeschlagen", lz_msg)
            return
            
        if not self.save_manual_invoice(silent=True, require_buyer_endpoint=True): return
        
        run_auto_generation(self.config)
        
        r_nr = self.entry_r_nr.get(); akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        pdf_pfad = os.path.join(self.p_config['ausgabe_ordner'], akt_jahr, f"Rechnung_{r_nr}.pdf")
        kopie_dir = self.config.get("cli_kopie")
        if kopie_dir and os.path.exists(pdf_pfad):
            try:
                os.makedirs(kopie_dir, exist_ok=True)
                shutil.copy2(pdf_pfad, os.path.join(kopie_dir, os.path.basename(pdf_pfad)))
            except Exception as e:
                print(f"Fehler beim Kopieren: {e}")
        if os.path.exists(pdf_pfad):
            # PDF nur öffnen, wenn --no-open nicht übergeben wurde
            if not self.config.get("cli_no_open", False):
                try: os.startfile(pdf_pfad)
                except: pass
            self.on_closing(skip_warning=True)  # <--- NEU: Hier übergeben wir den Freifahrtschein!

