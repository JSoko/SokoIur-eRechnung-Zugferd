"""
gui_module.py
-------------
Mixin-Klassen für die Reiter (Tabs) der Benutzeroberfläche.
Dieses Modul lagert die Logik der verschiedenen GUI-Bereiche (Manuelle Eingabe, 
Auswertungen/Journal, Einstellungen, Hilfe & Doku, Updater) in separate Klassen aus.
"""
import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog
import os
import shutil
from decimal import Decimal
import sys
import csv
import re
import time
import threading
import subprocess
import urllib.request
import urllib.error
import json
from datetime import datetime, timedelta
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

from datenbank import *
from pdf_zugferd import check_lz_logic, run_auto_generation
import hilfe_texte

class TabManuellMixin:
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
        if pfad: self.load_manual_invoice(is_button_click=True, custom_path=pfad)


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
        dialog.after(50, e_search.focus_set)# Enter: Wenn es exakt 1 Treffer gibt, wird dieser sofort übernommen!
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
        left_frame = ctk.CTkFrame(self.tab_manuell, width=350); left_frame.pack(side="left", fill="y", padx=10, pady=10)
        right_frame = ctk.CTkFrame(self.tab_manuell); right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.create_button(left_frame, text="📥 Letzte Rechnungs-CSV laden (Alt+L)", command=lambda: self.load_manual_invoice(is_button_click=True), fg_color="#444", hover_color="#666").pack(pady=(10, 5), padx=10, fill="x")
        self.create_button(left_frame, text="📁 Rechnungs-CSV wählen", command=self.choose_and_load_csv, fg_color="#444", hover_color="#666").pack(pady=(0, 10), padx=10, fill="x")
        
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
        
        self.create_button(left_frame, text="📝 Texte bearbeiten (Alt+T)", command=self.open_texte_popup).pack(pady=15, padx=10, fill="x")
        ctk.CTkFrame(left_frame, height=2, fg_color="#555").pack(fill="x", pady=10, padx=10)
        self.lbl_totals = ctk.CTkLabel(left_frame, text="Netto Gesamt: 0,00 €\nBrutto Gesamt: 0,00 €", justify="left", font=("Helvetica", 14, "bold"))
        self.lbl_totals.pack(pady=5, padx=15, anchor="w")
        
        ctk.CTkLabel(right_frame, text="Positionen", font=("Helvetica", 14, "bold")).pack(pady=10)
        self.pos_scroll = ctk.CTkScrollableFrame(right_frame); self.pos_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_button(right_frame, text="+ Position hinzufügen (+)", command=self.open_pos_popup).pack(pady=10)
        # Frame für geteilte Buttons (Papier & XRechnung) ---
        f_split_btns = ctk.CTkFrame(right_frame, fg_color="transparent")
        f_split_btns.pack(pady=5, fill="x", padx=20)
        self.create_button(f_split_btns, text="Papierrechnung erstellen", fg_color="#FFF2A8", text_color="#3D3200", hover_color="#E6D77A", command=self.save_generate_papierrechnung_exit).pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.create_button(f_split_btns, text="XRechnung & Begleit-PDF erstellen", fg_color="#cccccc", hover_color="#14375d", command=self.save_generate_xrechnung_exit).pack(side="left", fill="x", expand=True, padx=(5, 0))
        # ------------------------------------------------------------
        
        self.create_button(right_frame, text="Zugpferdrechnung erstellen & öffnen (Alt+P)", fg_color="#289102", hover_color="#5dc21c", command=self.save_generate_open_exit).pack(pady=5, fill="x", padx=20)        

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
            if os.path.exists(self.p_config.get('zusatz_csv', '')):
                with open(self.p_config.get('zusatz_csv', ''), mode='r', encoding='utf-8-sig') as f:
                    for line in f:
                        line = line.strip()
                        if line and len(line.split(';', 1)) == 2:
                            pk, txt = line.split(';', 1)
                            for p in pk.strip().split(','): self.zusatz_dict[p.strip()] = txt.strip()
            
            self.header_text = lade_textdatei(self.p_config.get('header_csv', ''))
            self.einleitung_text = lade_textdatei(self.p_config.get('einleitung_csv', ''))
            self.gruss_text = lade_textdatei(self.p_config.get('gruss_csv', ''))
            self.refresh_pos_list()
        except Exception as e:
            if not silent: messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")

    def open_texte_popup(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Texte bearbeiten")
        # Fenster etwas höher machen (700 statt 600)
        self.center_window(dialog, 600, 700)
        dialog.transient(self)
        dialog.grab_set() 
        
        # 1. Feststehender Bereich unten für den Button
        f_btn = ctk.CTkFrame(dialog, fg_color="transparent")
        f_btn.pack(side="bottom", fill="x", pady=10)
        
        # 2. Scrollbarer Bereich für die Inhalte
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Alle Textfelder werden nun in 'scroll' statt 'dialog' gepackt
        ctk.CTkLabel(scroll, text="Zentrierter Header (über Rechnungs-Nr.):").pack(anchor="w", padx=20, pady=(10, 0))
        t_head = ctk.CTkTextbox(scroll, height=60); t_head.pack(fill="x", padx=20, pady=2); t_head.insert("0.0", self.header_text)
        chk_head = ctk.CTkCheckBox(scroll, text="Merken"); chk_head.pack(anchor="w", padx=20, pady=(0, 10))
        if self.p_config.get("keep_header", True): chk_head.select()
        
        ctk.CTkLabel(scroll, text="Einleitung (vor Positionen):").pack(anchor="w", padx=20, pady=(5, 0))
        t_einl = ctk.CTkTextbox(scroll, height=80); t_einl.pack(fill="x", padx=20, pady=2); t_einl.insert("0.0", self.einleitung_text)
        chk_einl = ctk.CTkCheckBox(scroll, text="Merken"); chk_einl.pack(anchor="w", padx=20, pady=(0, 10))
        if self.p_config.get("keep_einleitung", True): chk_einl.select()
        
        ctk.CTkLabel(scroll, text="Gruß (unten):").pack(anchor="w", padx=20, pady=(5, 0))
        t_gruss = ctk.CTkTextbox(scroll, height=80); t_gruss.pack(fill="x", padx=20, pady=2); t_gruss.insert("0.0", self.gruss_text)
        chk_gruss = ctk.CTkCheckBox(scroll, text="Merken"); chk_gruss.pack(anchor="w", padx=20, pady=(0, 10))
        if self.p_config.get("keep_gruss", True): chk_gruss.select()
        
        ctk.CTkLabel(scroll, text="ℹ️ Offizielle Hinweise zur Nutzung von BT-20 und BT-22 nach EN 16931 finden Sie im Handbuch (Kapitel 9).", text_color="#1f538d", font=("Helvetica", 11, "italic")).pack(anchor="w", padx=20, pady=(15, 0))

        ctk.CTkLabel(scroll, text="Zahlungsbedingungen (BT-20 - Fälligkeitshinweis):").pack(anchor="w", padx=20, pady=(5, 0))
        t_zahl = ctk.CTkTextbox(scroll, height=50); t_zahl.pack(fill="x", padx=20, pady=2)
        t_zahl.insert("0.0", self.p_config.get("zahlungsbedingungen_default", ""))

        ctk.CTkLabel(scroll, text="Rechnungsvermerk / Dauerrechnung (BT-22):").pack(anchor="w", padx=20, pady=(10, 0))
        t_verm = ctk.CTkTextbox(scroll, height=50); t_verm.pack(fill="x", padx=20, pady=2)
        t_verm.insert("0.0", self.p_config.get("rechnungsvermerk_default", ""))

        def save_texte():
            self.header_text, self.einleitung_text, self.gruss_text = t_head.get("0.0", "end").strip(), t_einl.get("0.0", "end").strip(), t_gruss.get("0.0", "end").strip()
            self.p_config["keep_header"], self.p_config["keep_einleitung"], self.p_config["keep_gruss"] = bool(chk_head.get()), bool(chk_einl.get()), bool(chk_gruss.get())
            self.p_config["zahlungsbedingungen_default"] = t_zahl.get("0.0", "end").strip()
            self.p_config["rechnungsvermerk_default"] = t_verm.get("0.0", "end").strip()
            if self.p_config["keep_header"]: speichere_textdatei(self.p_config.get('header_csv'), self.header_text)
            if self.p_config["keep_einleitung"]: speichere_textdatei(self.p_config.get('einleitung_csv'), self.einleitung_text)
            if self.p_config["keep_gruss"]: speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)
            
            speichere_config(self.config)
            dialog.destroy()
                    
        # Button wird in den festen Rahmen (f_btn) unten gepackt
        self.create_button(f_btn, text="Übernehmen", command=save_texte).pack(pady=10)
    
    def open_pos_popup(self, edit_index=None):
        rechnung_pfad = self.p_config.get('rechnung_csv', '')
        firmen_ordner = os.path.dirname(rechnung_pfad) if rechnung_pfad else os.getcwd()
        briefbogen_pfad = os.path.join(firmen_ordner, "briefbogen.pdf")
        
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

            if self.p_config.get("keep_header", True): speichere_textdatei(self.p_config.get('header_csv'), self.header_text)
            if self.p_config.get("keep_einleitung", True): speichere_textdatei(self.p_config.get('einleitung_csv'), self.einleitung_text)
            if self.p_config.get("keep_gruss", True): speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)
            
            if self.chk_kunde_speichern.get() and self.entry_k_name.get().strip():
                speichere_kunde(self.p_config.get("kunden_csv", "kunden.csv"), {'Name': self.entry_k_name.get().strip(), 'Strasse': self.entry_k_strasse.get().strip(), 'PLZ_Ort': self.entry_k_plz_ort.get().strip(), 'Land': 'DE', 'KundeNr': self.entry_k_nr.get().strip(), 'Aktenzeichen': self.entry_az.get().strip(), 'KundeAktenzeichen': self.entry_k_az.get().strip(), 'Endpoint': buyer_endpoint, 'EndpointScheme': buyer_scheme})
                self.kunden_liste = lade_kunden(self.p_config.get("kunden_csv", "kunden.csv"))
                
            self.p_config['letzte_rechnungsnummer'] = r_nr
            self.p_config['keep_raten'] = bool(self.chk_raten.get()); self.p_config['keep_kunde_speichern'] = bool(self.chk_kunde_speichern.get())
            speichere_config(self.config)
            if not silent: messagebox.showinfo("Erfolg", "Ihre Daten wurden erfolgreich gespeichert!")
            return True
        except Exception as e:
            messagebox.showerror("Fehler", str(e)); return False

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
                lade_zusatz_csv(act_prof['zusatz_csv']), lade_textdatei(act_prof['gruss_csv']),
                lade_textdatei(act_prof['header_csv']), lade_textdatei(act_prof['einleitung_csv']),
                act_prof['ausgabe_ordner'], act_prof['auswertungen_ordner'],
                act_prof.get("aktuelles_rechnungsjahr", str(datetime.now().year))
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
            xml_p, pdf_p = erstelle_xrechnung(firma, daten, act_prof['briefbogen_pdf'], zusatztexte, gruss, header, einleitung, act_prof['ausgabe_ordner'], act_prof['auswertungen_ordner'], akt_jahr)
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

class TabAuswertungenMixin:
    def build_ausgang_tab(self):
        f = ctk.CTkFrame(self.tab_ausgang)
        f.pack(pady=30, padx=20, fill="x")
        
        ctk.CTkLabel(f, text="Ausgangsrechnungen (Journal)", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        f_ord = ctk.CTkFrame(f, fg_color="transparent")
        f_ord.pack(pady=(10, 5), fill="x", padx=10)
        ctk.CTkLabel(f_ord, text="Journal-Ordner:", width=150).pack(side="left")
        
        self.entry_ausw_ordner = ctk.CTkEntry(f_ord, width=300)
        self.entry_ausw_ordner.pack(side="left", padx=10, expand=True, fill="x")
        self.entry_ausw_ordner.insert(0, self.p_config.get("auswertungen_ordner", "Auswertungen"))
        
        self.create_button(f_ord, text="📂", width=40, command=lambda: self.browse_path_for_entry(self.entry_ausw_ordner, is_dir=True, on_change=self.update_ausw_jahre)).pack(side="left")
        self.entry_ausw_ordner.bind('<FocusOut>', lambda e: self.update_ausw_jahre())
        
        f_zeit = ctk.CTkFrame(f, fg_color="transparent")
        f_zeit.pack(pady=5, fill="x", padx=10)
        ctk.CTkLabel(f_zeit, text="Zeitraum (Monat / Jahr):", width=150).pack(side="left")
        
        self.combo_ausw_monat = ctk.CTkComboBox(f_zeit, values=["Alle Monate"] + [f"{i:02d}" for i in range(1,13)], width=120)
        self.combo_ausw_monat.pack(side="left", padx=(10, 5))
        self.combo_ausw_monat.set(datetime.now().strftime("%m"))
        
        self.combo_ausw_jahr = ctk.CTkComboBox(f_zeit, values=[], width=120)
        self.combo_ausw_jahr.pack(side="left", padx=5)
        
        self.create_button(f, text="Journal als PDF erzeugen & öffnen", command=self.generate_auswertung, fg_color="#b85c00", hover_color="#8f4700").pack(pady=20)
        self.update_ausw_jahre()

    def build_eingang_tab(self):
        f = ctk.CTkFrame(self.tab_eingang)
        f.pack(pady=(15, 8), padx=20, fill="x")
        ctk.CTkLabel(f, text="Eingangsrechnungen (Journal & Verwaltung)", font=("Helvetica", 16, "bold")).pack(pady=(10, 4))
        path = self.p_config.get("eingangsjournal_ordner", "")
        ctk.CTkLabel(f, text=f"Journal-Ordner: {path}", wraplength=750).pack(padx=15, pady=2)

        z = ctk.CTkFrame(f, fg_color="transparent")
        z.pack(pady=8)
        ctk.CTkLabel(z, text="Zeitraum (Monat / Jahr):").pack(side="left")
        self.combo_eingang_monat = ctk.CTkComboBox(
            z, values=["Alle Monate"] + [f"{i:02d}" for i in range(1, 13)], width=120,
            command=lambda _: self.refresh_eingang_journal_ui()
        )
        self.combo_eingang_monat.set(datetime.now().strftime("%m"))
        self.combo_eingang_monat.pack(side="left", padx=8)

        years = []
        if os.path.isdir(path):
            years = sorted([x for x in os.listdir(path) if re.fullmatch(r"\d{4}", x)], reverse=True)
        if not years:
            years = [str(datetime.now().year)]
        self.combo_eingang_jahr = ctk.CTkComboBox(
            z, values=years, width=120,
            command=lambda _: self.refresh_eingang_journal_ui()
        )
        self.combo_eingang_jahr.set(years[0])
        self.combo_eingang_jahr.pack(side="left", padx=8)

        self.create_button(
            z, text="📄 Eingangsjournal als PDF erzeugen & öffnen",
            command=self.generate_eingang_auswertung, fg_color="#b85c00", hover_color="#8f4700"
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            f,
            text="Die Position „Datei öffnen“ im erzeugten PDF ist mit der archivierten Originalrechnung verlinkt. Die Funktion hängt vom verwendeten PDF-Viewer ab.",
            wraplength=720, justify="center", text_color="gray", font=("Helvetica", 11)
        ).pack(padx=15, pady=(0, 8))

        # --- Such- und Storno-/Löschbereich für bereits erfasste Eingangsrechnungen ---
        f_list = ctk.CTkFrame(self.tab_eingang)
        f_list.pack(pady=(5, 15), padx=20, fill="both", expand=True)

        f_search = ctk.CTkFrame(f_list, fg_color="transparent")
        f_search.pack(fill="x", padx=12, pady=(10, 5))
        ctk.CTkLabel(f_search, text="🔍 Journal durchsuchen:", font=("Helvetica", 13, "bold")).pack(side="left")
        self.entry_eingang_search = ctk.CTkEntry(
            f_search, placeholder_text="ER-Nr., Lieferant, externe RE-Nr., Datum oder Betrag..."
        )
        self.entry_eingang_search.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_eingang_search.bind("<KeyRelease>", lambda e: self.refresh_eingang_journal_ui())

        self.chk_eingang_alle_zeitr = ctk.CTkCheckBox(
            f_search, text="Alle Jahre/Monate durchsuchen", command=self.refresh_eingang_journal_ui
        )
        self.chk_eingang_alle_zeitr.pack(side="left", padx=6)

        self.create_button(
            f_search, text="🔄 Aktualisieren", width=110, fg_color="#444", hover_color="#666",
            command=self.refresh_eingang_journal_ui
        ).pack(side="right")

        self.eingang_journal_scroll = ctk.CTkScrollableFrame(f_list)
        self.eingang_journal_scroll.pack(fill="both", expand=True, padx=12, pady=(4, 10))
        self.refresh_eingang_journal_ui()

    def refresh_eingang_journal_ui(self):
        if not hasattr(self, "eingang_journal_scroll"):
            return
        from eingangsrechnung import load_all_journal_entries

        for w in self.eingang_journal_scroll.winfo_children():
            w.destroy()

        folder = self.p_config.get("eingangsjournal_ordner", "")
        entries = load_all_journal_entries(folder)

        term = self.entry_eingang_search.get().strip().lower() if hasattr(self, "entry_eingang_search") else ""
        all_periods = bool(self.chk_eingang_alle_zeitr.get()) if hasattr(self, "chk_eingang_alle_zeitr") else False
        sel_year = self.combo_eingang_jahr.get() if hasattr(self, "combo_eingang_jahr") else str(datetime.now().year)
        sel_month = self.combo_eingang_monat.get() if hasattr(self, "combo_eingang_monat") else "Alle Monate"

        filtered = []
        for r in entries:
            r_dat = r.get("Rechnungsdatum", "")
            if not all_periods and not term:
                if len(r_dat) == 10 and r_dat[6:10] != sel_year:
                    continue
                if sel_month != "Alle Monate" and len(r_dat) == 10 and r_dat[3:5] != sel_month:
                    continue
            if term:
                haystack = " ".join([
                    r.get("Interne ER-Nr.", ""),
                    r.get("Lieferant", ""),
                    r.get("Externe Rechnungsnummer", ""),
                    r.get("Rechnungsdatum", ""),
                    r.get("Brutto", ""),
                    r.get("Netto", ""),
                    r.get("Quelldatei", ""),
                ]).lower()
                if term not in haystack:
                    continue
            filtered.append(r)

        if not filtered:
            ctk.CTkLabel(
                self.eingang_journal_scroll,
                text="Keine erfassten Eingangsrechnungen für diese Auswahl / Suche gefunden.",
                text_color="gray"
            ).pack(pady=20)
            return

        for rec in filtered[:150]:
            row = ctk.CTkFrame(self.eingang_journal_scroll)
            row.pack(fill="x", pady=2, padx=4)
            er_nr = rec.get("Interne ER-Nr.", "")
            r_dat = rec.get("Rechnungsdatum", "")
            lief = rec.get("Lieferant", "")
            ext_nr = rec.get("Externe Rechnungsnummer", "")
            brutto = rec.get("Brutto", "0,00")
            fmt = rec.get("Format", "")
            arch = rec.get("Archivdatei", "")

            txt = f"[{er_nr}] {r_dat} | {lief[:30]} | RE: {ext_nr} | Brutto: {brutto} € ({fmt})"
            ctk.CTkLabel(row, text=txt, anchor="w").pack(side="left", padx=8, pady=4, fill="x", expand=True)

            self.create_button(
                row, text="🗑 Storno / Löschen", width=130, fg_color="#b30000", hover_color="#800000",
                command=lambda r_obj=rec: self.delete_incoming_entry_ui(r_obj)
            ).pack(side="right", padx=4, pady=4)

            if arch and os.path.isfile(arch):
                self.create_button(
                    row, text="👁 Beleg", width=80, fg_color="#555", hover_color="#777",
                    command=lambda p=arch: self._open_file_external(p) if hasattr(self, "_open_file_external") else os.startfile(p)
                ).pack(side="right", padx=4, pady=4)

    def delete_incoming_entry_ui(self, rec):
        from eingangsrechnung import delete_journal_entry

        er_nr = rec.get("Interne ER-Nr.", "")
        lief = rec.get("Lieferant", "")
        ext_nr = rec.get("Externe Rechnungsnummer", "")
        brutto = rec.get("Brutto", "0,00")

        msg = (
            f"Möchten Sie die erfasste Eingangsrechnung {er_nr} wirklich stornieren / aus dem Journal löschen?\n\n"
            f"Lieferant: {lief}\n"
            f"Externe RE-Nr.: {ext_nr}\n"
            f"Bruttobetrag: {brutto} €\n\n"
            f"Dabei werden auch die zugehörigen Archivkopien in 'rchn' und 'rebearb' entfernt, "
            f"sodass der Beleg bei Bedarf neu erfasst werden kann."
        )
        if not messagebox.askyesno("Eingangsrechnung stornieren / löschen", msg, default="no"):
            return

        ok, res_msg = delete_journal_entry(
            self.p_config.get("eingangsjournal_ordner", ""),
            er_nr,
            delete_archive_files=True,
            rebearb_base_folder=self.p_config.get("bearbeitete_eingangsrechnungen_ordner", ""),
        )
        if ok:
            # Falls es die allerletzte vergebene Nummer war, Zähler um 1 zurücksetzen, damit keine Lücke entsteht
            last_nr = self.p_config.get("letzte_eingangsrechnungsnummer", "").strip().upper()
            if last_nr == er_nr.strip().upper():
                m = re.match(r"^(ER\d{2})(\d{4})$", last_nr)
                if m:
                    num = int(m.group(2))
                    prev_nr = f"{m.group(1)}{num-1:04d}" if num > 1 else ""
                    self.p_config["letzte_eingangsrechnungsnummer"] = prev_nr
                    speichere_config(self.config)
                    if hasattr(self, "lbl_letzte_er_nr"):
                        self.lbl_letzte_er_nr.configure(text=prev_nr or "Noch keine")

            self.refresh_eingang_journal_ui()
            if hasattr(self, "refresh_incoming_list"):
                self.refresh_incoming_list()
            messagebox.showinfo("Gelöscht", res_msg)
        else:
            messagebox.showerror("Fehler", res_msg)

    def generate_eingang_auswertung(self):
        from eingangsrechnung import create_journal_pdf
        folder = self.p_config.get("eingangsjournal_ordner", "")
        year = self.combo_eingang_jahr.get()
        month = self.combo_eingang_monat.get()
        out = create_journal_pdf(folder, year, month, lade_firma(self.p_config.get("firma_csv", "")).get("FirmaName", ""))
        if not out:
            return messagebox.showinfo("Info", f"Für {year if month == 'Alle Monate' else month + '.' + year} wurden keine Eingangsrechnungen gefunden.")
        try:
            os.startfile(out)
        except Exception:
            messagebox.showinfo("Fertig", f"Eingangsjournal erstellt: {out}")

    def update_ausw_jahre(self):
        if not hasattr(self, 'entry_ausw_ordner'): return
        ordner = self.entry_ausw_ordner.get().strip(); jahre = set()
        if os.path.exists(ordner):
            for d in os.listdir(ordner):
                if os.path.isdir(os.path.join(ordner, d)) and re.match(r'^\d{4}$', d): jahre.add(d)
            for f in os.listdir(ordner):
                m = re.match(r'^re(\d{4})\d{2}\.csv$', f.lower())
                if m: jahre.add(m.group(1))
        jahre_liste = sorted(list(jahre), reverse=True) if jahre else [datetime.now().strftime("%Y")]
        self.combo_ausw_jahr.configure(values=jahre_liste)
        if self.combo_ausw_jahr.get() not in jahre_liste: self.combo_ausw_jahr.set(jahre_liste[0])

    def browse_path_for_entry(self, entry_widget, is_dir=False, on_change=None):
        path = filedialog.askdirectory() if is_dir else filedialog.askopenfilename()
        if path:
            entry_widget.delete(0, "end"); entry_widget.insert(0, path)
            if on_change: on_change()

    def generate_auswertung(self):
        ordner = self.entry_ausw_ordner.get().strip(); jahr = self.combo_ausw_jahr.get(); monat = self.combo_ausw_monat.get()
        if not os.path.exists(ordner): return messagebox.showwarning("Fehler", "Der Auswertungs-Ordner existiert nicht.")
            
        such_muster = [f"re{jahr}{m:02d}.csv" for m in range(1, 13)] if monat == "Alle Monate" else [f"re{jahr}{monat}.csv"]
        zeit_str = f"{jahr}" if monat == "Alle Monate" else f"{monat}.{jahr}"
            
        gefundene = []
        for datei in such_muster:
            pfad = os.path.join(ordner, jahr, datei) if os.path.exists(os.path.join(ordner, jahr, datei)) else os.path.join(ordner, datei)
            if os.path.exists(pfad):
                with open(pfad, 'r', encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f, delimiter=';'): gefundene.append(row)
                        
        if not gefundene: return messagebox.showinfo("Info", f"Für {zeit_str} wurden keine Daten gefunden.")
        
        firma_name = lade_firma(self.p_config.get('firma_csv', 'firma.csv')).get('FirmaName', 'Unbekannte Firma')
        jahr_ordner = os.path.join(ordner, jahr); os.makedirs(jahr_ordner, exist_ok=True)
        pdf_pfad = os.path.join(jahr_ordner, f"Journal_{zeit_str.replace('.','_')}.pdf")
        
        c_dummy = canvas.Canvas(BytesIO(), pagesize=landscape(A4)); breite, hoehe = landscape(A4)
        
        def render_journal(c_obj, is_final=False, total_pages=1):
            page_num = 1
            def draw_header():
                c_obj.setFont("Helvetica-Bold", 16); c_obj.drawString(40, hoehe - 50, f"Rechnungsjournal - {zeit_str} - {firma_name}")
                c_obj.setFont("Helvetica-Bold", 10)
                c_obj.drawString(40, hoehe - 80, "Datum"); c_obj.drawString(100, hoehe - 80, "Rechnungs-Nr."); c_obj.drawString(220, hoehe - 80, "Empfänger")
                c_obj.drawRightString(500, hoehe - 80, "Netto"); c_obj.drawRightString(580, hoehe - 80, "19% USt."); c_obj.drawRightString(660, hoehe - 80, "7% USt.")
                c_obj.drawRightString(740, hoehe - 80, "0% USt."); c_obj.drawRightString(820, hoehe - 80, "Brutto")
                c_obj.line(40, hoehe - 85, 820, hoehe - 85); return hoehe - 105
            
            def draw_footer():
                c_obj.setFont("Helvetica", 9); c_obj.drawString(40, 20, f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr")
                if total_pages > 1: c_obj.drawRightString(820, 20, f"Seite {page_num} / {total_pages}")
            
            y = draw_header()
            if is_final: draw_footer()
            c_obj.setFont("Helvetica", 10)
            
            sum_n = sum_19 = sum_7 = sum_0 = sum_b = 0.0
            for r in gefundene:
                if y < 60:
                    c_obj.showPage(); page_num += 1; y = draw_header()
                    if is_final: draw_footer()
                    c_obj.setFont("Helvetica", 10)
                    
                n = safe_float(r.get('Netto', 0)); m19 = safe_float(r.get('MwSt_19', 0)); m7 = safe_float(r.get('MwSt_7', 0)); m0 = safe_float(r.get('MwSt_0', 0)); b = safe_float(r.get('Brutto', 0))
                sum_n += n; sum_19 += m19; sum_7 += m7; sum_0 += m0; sum_b += b
                
                c_obj.drawString(40, y, r.get('Datum', '')); c_obj.drawString(100, y, r.get('Rechnungsnummer', ''))
                empf = r.get('Empfaenger', '')
                c_obj.drawString(220, y, empf[:22] + "..." if len(empf) > 25 else empf)
                c_obj.drawRightString(500, y, f_curr(n)); c_obj.drawRightString(580, y, f_curr(m19)); c_obj.drawRightString(660, y, f_curr(m7))
                c_obj.drawRightString(740, y, f_curr(m0)); c_obj.drawRightString(820, y, f_curr(b))
                y -= 15
                
            c_obj.line(40, y + 10, 820, y + 10); y -= 10
            c_obj.setFont("Helvetica-Bold", 10); c_obj.drawString(40, y, "GESAMTSUMMEN:")
            c_obj.drawRightString(500, y, f_curr(sum_n)); c_obj.drawRightString(580, y, f_curr(sum_19)); c_obj.drawRightString(660, y, f_curr(sum_7))
            c_obj.drawRightString(740, y, f_curr(sum_0)); c_obj.drawRightString(820, y, f_curr(sum_b))
            return page_num
        
        t_pages = render_journal(c_dummy)
        c = canvas.Canvas(pdf_pfad, pagesize=landscape(A4)); render_journal(c, is_final=True, total_pages=t_pages); c.save()
        try: os.startfile(pdf_pfad)
        except: messagebox.showinfo("Fertig", f"Journal erstellt: {pdf_pfad}")


class TabEinstellungenMixin:
    def get_available_years(self):
        ausg_ordner = self.p_config.get("ausgabe_ordner", "Rechnungen_PDF"); jahre = set()
        if os.path.exists(ausg_ordner):
            for d in os.listdir(ausg_ordner):
                if os.path.isdir(os.path.join(ausg_ordner, d)) and re.match(r'^\d{4}$', d): jahre.add(d)
        curr = datetime.now().year
        jahre.add(str(curr)); jahre.add(str(curr + 1))
        return sorted(list(jahre), reverse=True)
        
    def on_settings_jahr_change(self, wahl):
        ausg_ordner = self.p_config.get("ausgabe_ordner", "Rechnungen_PDF")
        ausw_ordner = self.p_config.get("auswertungen_ordner", "Auswertungen")
        jahr_ausg = os.path.join(ausg_ordner, wahl); jahr_ausw = os.path.join(ausw_ordner, wahl)
        
        if not os.path.exists(jahr_ausg) or not os.path.exists(jahr_ausw):
            if messagebox.askyesno("Ordner anlegen", f"Die Ordner für das Jahr {wahl} existieren noch nicht.\nSollen sie jetzt angelegt werden?"):
                os.makedirs(jahr_ausg, exist_ok=True); os.makedirs(jahr_ausw, exist_ok=True)
                self.p_config["aktuelles_rechnungsjahr"] = wahl; speichere_config(self.config)
                messagebox.showinfo("Erfolg", f"Ordner für {wahl} angelegt.")
            else:
                self.combo_jahr.set(self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year)))
        else:
            self.p_config["aktuelles_rechnungsjahr"] = wahl; speichere_config(self.config)

    def edit_letzte_nr(self):
        d = ctk.CTkInputDialog(text="Neue Rechnungsnummer eingeben:", title="Rechnungsnummer korrigieren")
        val = d.get_input()
        if val and val.strip():
            self.p_config["letzte_rechnungsnummer"] = val.strip(); speichere_config(self.config)
            self.lbl_letzte_nr.configure(text=val.strip())
            self.entry_r_nr.delete(0, 'end'); self.entry_r_nr.insert(0, berechne_naechste_rechnungsnummer(val.strip()))

    def edit_letzte_eingangs_nr(self):
        d=ctk.CTkInputDialog(text="Neue letzte Eingangsrechnungsnummer eingeben (z. B. ER260001):", title="Eingangsrechnungsnummer korrigieren")
        val=d.get_input()
        if val and val.strip():
            self.p_config["letzte_eingangsrechnungsnummer"]=val.strip();speichere_config(self.config)
            if hasattr(self,"lbl_letzte_er_nr"):self.lbl_letzte_er_nr.configure(text=val.strip())
    def choose_briefbogen(self):
        import shutil
        import os
        from tkinter import filedialog
        import tkinter.messagebox as messagebox
        
        # Den Zielpfad aus der Konfiguration der aktiven Firma holen
        target_path = self.p_config.get("briefbogen_pdf", "")
        
        # Prüfen, ob der Zielordner existiert
        if not target_path or not os.path.exists(os.path.dirname(target_path)):
            return messagebox.showwarning(
                "Fehler", 
                "Der Zielordner für diese Firma existiert noch nicht.\n\nBitte klicken Sie unten erst auf 'Struktur anlegen & Pfade speichern'."
            )
            
        # Datei-Auswahldialog öffnen
        source_path = filedialog.askopenfilename(
            title="Briefbogen (PDF) auswählen",
            filetypes=[("PDF-Dateien", "*.pdf")]
        )
        
        if source_path:
            try:
                # Datei an den Zielort kopieren und ggf. überschreiben
                shutil.copy2(source_path, target_path)
                messagebox.showinfo(
                    "Erfolg", 
                    f"Der Briefbogen wurde erfolgreich kopiert und für die aktive Firma hinterlegt unter:\n\n{target_path}"
                )
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Kopieren des Briefbogens:\n{str(e)}")
    def build_settings_tab(self):
        # --- NEU: Haupt-Scrollbereich für den gesamten Reiter anlegen ---
        scroll_main = ctk.CTkScrollableFrame(self.tab_settings)
        scroll_main.pack(fill="both", expand=True)

        f_stammdaten = ctk.CTkFrame(scroll_main)
        f_stammdaten.pack(fill="x", pady=(10, 10), padx=20)
        ctk.CTkLabel(f_stammdaten, text="Stammdaten der aktiven Firma verwalten", font=("Helvetica", 14, "bold")).pack(pady=5)

        f_prof = ctk.CTkFrame(scroll_main)
        f_prof.pack(fill="x", pady=(10, 10), padx=20)
        ctk.CTkLabel(f_prof, text="Aktive Firma / Profil verwalten", font=("Helvetica", 14, "bold")).pack(pady=5)
        
        f_prof_btns = ctk.CTkFrame(f_prof, fg_color="transparent"); f_prof_btns.pack(pady=10)
        self.create_button(f_prof_btns, text="+ Neu", width=100, command=self.add_profile).pack(side="left", padx=5)
        self.create_button(f_prof_btns, text="✎ Umbenennen", width=100, command=self.rename_profile).pack(side="left", padx=5)
        if len(self.config["profiles"]) > 1:
            self.create_button(f_prof_btns, text="🗑 Löschen", width=100, fg_color="#b30000", hover_color="#800000", command=self.delete_profile).pack(side="left", padx=5)
        
        f_btns = ctk.CTkFrame(f_stammdaten, fg_color="transparent"); f_btns.pack(pady=10)
        self.create_button(f_btns, text="🏢 Firmendaten bearbeiten", command=self.open_firma_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=10)
        self.create_button(f_btns, text="👥 Kundendaten verwalten", command=self.open_kunden_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=10)
        self.create_button(f_btns, text="📦 Produktdaten verwalten", command=self.open_produkte_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=10)
        self.create_button(f_btns, text="📄 Briefbogen hinterlegen", command=self.choose_briefbogen, fg_color="#1f538d", hover_color="#14375d").pack(side="left", padx=10)
        
        f_num_jahr = ctk.CTkFrame(scroll_main); f_num_jahr.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(f_num_jahr, text="Nummernkreise & Rechnungsjahr", font=("Helvetica", 14, "bold")).pack(pady=5)
        
        f_jahr = ctk.CTkFrame(f_num_jahr, fg_color="transparent"); f_jahr.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(f_jahr, text="Aktuelles Rechnungsjahr:", width=200, anchor="w").pack(side="left")
        
        self.combo_jahr = ctk.CTkComboBox(f_jahr, values=self.get_available_years(), command=self.on_settings_jahr_change)
        self.combo_jahr.set(self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))); self.combo_jahr.pack(side="left", padx=10)
        
        f_nr = ctk.CTkFrame(f_num_jahr, fg_color="transparent"); f_nr.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(f_nr, text="Letzte Rechnungs-Nr.:", width=200, anchor="w").pack(side="left")
        self.lbl_letzte_nr = ctk.CTkLabel(f_nr, text=self.p_config.get("letzte_rechnungsnummer", "Noch keine"), width=150, anchor="w")
        self.lbl_letzte_nr.pack(side="left", padx=10)
        self.create_button(f_nr, text="✏️ Korrigieren", width=80, command=self.edit_letzte_nr).pack(side="left")
        
        f_er=ctk.CTkFrame(f_num_jahr,fg_color="transparent");f_er.pack(fill="x",pady=5,padx=10)
        ctk.CTkLabel(f_er,text="Letzte Eingangsrechnungs-Nr.:",width=200,anchor="w").pack(side="left")
        self.lbl_letzte_er_nr=ctk.CTkLabel(f_er,text=self.p_config.get("letzte_eingangsrechnungsnummer","") or "Noch keine",width=150,anchor="w");self.lbl_letzte_er_nr.pack(side="left",padx=10)
        self.create_button(f_er,text="✏️ Korrigieren",width=80,command=self.edit_letzte_eingangs_nr).pack(side="left")
        
        self.chk_xrechnung_leseabschrift=ctk.CTkCheckBox(f_num_jahr,text="Bei XRechnungen standardmäßig eine PDF-Leseabschrift erzeugen")
        self.chk_xrechnung_leseabschrift.pack(anchor="w",padx=220,pady=(2,8))
        if self.p_config.get("xrechnung_leseabschrift",True):self.chk_xrechnung_leseabschrift.select()

        ctk.CTkLabel(scroll_main, text="Speicherorte & Ordnerstruktur:", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        start_pfad = os.path.abspath(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__))
        f_start = ctk.CTkFrame(scroll_main, fg_color="transparent"); f_start.pack(fill="x", pady=2, padx=20)
        ctk.CTkLabel(f_start, text="Programm-Startpfad:", width=150, anchor="w").pack(side="left")
        e_start = ctk.CTkEntry(f_start, width=400); e_start.insert(0, start_pfad); e_start.configure(state="readonly")
        e_start.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkLabel(scroll_main, text="Hinweis: Bei Installation im Netzwerk sollte der Daten-Grundpfad auf einem Netzwerklaufwerk liegen.", text_color="orange", font=("Helvetica", 11)).pack(anchor="w", padx=20, pady=2)

        f_base = ctk.CTkFrame(scroll_main, fg_color="transparent"); f_base.pack(fill="x", pady=2, padx=20)
        ctk.CTkLabel(f_base, text="Daten-Grundpfad:", width=150, anchor="w").pack(side="left")
        self.entry_base_path = ctk.CTkEntry(f_base, width=400)
        self.entry_base_path.insert(0, self.config.get("base_data_path", start_pfad))
        self.entry_base_path.pack(side="left", padx=10, fill="x", expand=True)
        self.create_button(f_base, text="📂", width=40, command=lambda: self.browse_path_for_entry(self.entry_base_path, is_dir=True)).pack(side="left")
            
        # --- NEU: Button hierhin verschoben und umbenannt ---
        self.create_button(scroll_main, text="Pfade speichern", command=self.save_settings).pack(pady=(10, 0))
        
        ctk.CTkLabel(scroll_main, text="Aktive Pfade der aktuellen Firma (schreibgeschützt):", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=20, pady=(15, 0))
        
        f_pfade = ctk.CTkScrollableFrame(scroll_main, height=130)
        f_pfade.pack(fill="x", padx=20, pady=5)
        
        # --- NEU: Lokale Programmdaten (App-Data) als erster Eintrag ---
        from datenbank import get_appdata_dir
        row_app = ctk.CTkFrame(f_pfade, fg_color="transparent")
        row_app.pack(fill="x", pady=2)
        ctk.CTkLabel(row_app, text="Lokale Programmdaten (App-Data):", width=220, anchor="w").pack(side="left")
        e_app = ctk.CTkEntry(row_app)
        e_app.insert(0, get_appdata_dir())
        e_app.configure(state="readonly")
        e_app.pack(side="left", fill="x", expand=True, padx=(5, 0))
        # ---------------------------------------------------------------

        pfade_liste = [
            ("Ausgangsrechnungen (PDF)", "ausgabe_ordner"),
            ("Ausgangsjournale (CSV)", "auswertungen_ordner"),
            ("Posteingang Neu (reneu)", "eingangsordner"),
            ("Eingangsarchiv Belege (rchn)", "eingangsrechnungen_ordner"),
            ("Eingangsarchiv Originale (rebearb)", "bearbeitete_eingangsrechnungen_ordner"),
            ("Eingangsjournale (einj)", "eingangsjournal_ordner"),
            ("Rechnungs-Datenbank", "rechnung_csv"),
            ("Kunden-Datenbank", "kunden_csv"),
            ("Produkte-Datenbank", "produkte_csv"),
            ("Briefbogen (PDF)", "briefbogen_pdf"),
            ("Firmen-Stammdaten", "firma_csv")
        ]
        
        for label_text, key in pfade_liste:
            row = ctk.CTkFrame(f_pfade, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label_text + ":", width=220, anchor="w").pack(side="left")
            e_pfad = ctk.CTkEntry(row)
            e_pfad.insert(0, self.p_config.get(key, "Nicht gesetzt"))
            e_pfad.configure(state="readonly")
            e_pfad.pack(side="left", fill="x", expand=True, padx=(5, 0))
            
       
        f_cli = ctk.CTkFrame(scroll_main)
        f_cli.pack(fill="x", pady=(20, 10), padx=20)
        ctk.CTkLabel(f_cli, text="Beispielaufruf für Kommandozeile (CLI) / Fremdprogramme", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
        
        prof_name = self.p_config.get("profil_name", "")
        letzte_nr = self.p_config.get("letzte_rechnungsnummer", "RE-1000")
        naechste_nr = berechne_naechste_rechnungsnummer(letzte_nr)
        
        cmd = f'SokoIur_eRechnung.exe --auto --profil "{prof_name}" --renr "{naechste_nr}" --rechnung "%TEMP%\\rechnung.csv" --kopie "%USERPROFILE%\\Documents"'
        
        t_cli = ctk.CTkTextbox(f_cli, height=60)
        t_cli.pack(fill="x", padx=15, pady=(5, 15))
        t_cli.insert("0.0", cmd)
        t_cli.configure(state="disabled")  # Read-only
    
    def save_settings(self):
        base_path = self.entry_base_path.get().strip()
        if not base_path:
            return messagebox.showwarning("Fehler", "Bitte einen Grundpfad angeben.")
            
        # GEÄNDERT: Legt den Pfad in der globalen Konfiguration ab
        self.config["base_data_path"] = base_path
        
        firm_folder = self.p_config["profil_name"].replace(" ", "_")
        firm_dir = os.path.join(base_path, firm_folder)
        ausw_dir = os.path.join(firm_dir, "ausw")
        are_dir = os.path.join(firm_dir, "are")
        arecsv_dir = os.path.join(firm_dir, "arecsv")  # NEU
        
        os.makedirs(ausw_dir, exist_ok=True)
        os.makedirs(are_dir, exist_ok=True)
        os.makedirs(arecsv_dir, exist_ok=True)  # NEU
        reneu_dir=os.path.join(firm_dir,"reneu"); rebearb_dir=os.path.join(firm_dir,"rebearb"); rchn_dir=os.path.join(firm_dir,"rchn"); einj_dir=os.path.join(firm_dir,"einj")
        for incoming_dir in (reneu_dir,rebearb_dir,rchn_dir,einj_dir): os.makedirs(incoming_dir,exist_ok=True)
        
        self.p_config["auswertungen_ordner"] = ausw_dir
        self.p_config["ausgabe_ordner"] = are_dir
        self.p_config["eingangsordner"]=reneu_dir; self.p_config["bearbeitete_eingangsrechnungen_ordner"]=rebearb_dir
        self.p_config["eingangsrechnungen_ordner"]=rchn_dir; self.p_config["eingangsjournal_ordner"]=einj_dir
        self.p_config["xrechnung_leseabschrift"]=bool(self.chk_xrechnung_leseabschrift.get())
        
        dateien = ["firma.csv", "rechnung.csv", "briefbogen.pdf", "zusatz.csv", "gruss.csv", "header.csv", "einleitung.csv", "kunden.csv", "produkte.csv"]
        for datei in dateien:
            key_name = datei.replace(".", "_")
            self.p_config[key_name] = os.path.join(firm_dir, datei)
            
        speichere_config(self.config)
        messagebox.showinfo("Gespeichert", f"Die Ordnerstruktur wurde in\n{firm_dir}\nangelegt und gespeichert!")
       
        def save():
            name, plz, ort, iban = e_name.get().strip(), e_plz.get().strip(), e_ort.get().strip(), e_iban.get().strip()
            ustid, stnr = e_ustid.get().strip(), e_stnr.get().strip()
            if not name or not plz or not ort or not iban or (not ustid and not stnr):
                return messagebox.showwarning("Fehler", "Zwingend: Name, PLZ, Ort, IBAN, USt-Id ODER Steuernummer", parent=d_edit)
            speichere_firma(pfad_firma, {'FirmaName': name, 'Strasse': e_str.get().strip(), 'PLZ': plz, 'Ort': ort, 'Land': e_land.get().strip(), 'UStId': ustid, 'Steuernummer': stnr, 'BankName': e_bank.get().strip(), 'IBAN': iban, 'BIC': e_bic.get().strip(), 'Kontoinhaber': e_inhaber.get().strip(), 'Email': e_mail.get().strip(), 'Telefon': e_tel.get().strip()})
            messagebox.showinfo("Gespeichert", "Firmendaten wurden aktualisiert!", parent=d_edit); d_edit.destroy()
    
    
    def open_firma_manager(self):
        d_edit = ctk.CTkToplevel(self); d_edit.title("Firmendaten bearbeiten")
        self.center_window(d_edit, 500, 550); d_edit.transient(self); d_edit.grab_set()
        
        pfad_firma = self.p_config.get("firma_csv", "firma.csv"); f_daten = lade_firma(pfad_firma)
            
        e_name = self.create_input(d_edit, "Firma Name"); e_name.insert(0, f_daten.get('FirmaName', ''))
        e_str = self.create_input(d_edit, "Straße"); e_str.insert(0, f_daten.get('Strasse', ''))
        e_plz = self.create_input(d_edit, "PLZ"); e_plz.insert(0, f_daten.get('PLZ', ''))
        e_ort = self.create_input(d_edit, "Ort"); e_ort.insert(0, f_daten.get('Ort', ''))
        e_land = self.create_input(d_edit, "Land (z.B. DE)"); e_land.insert(0, f_daten.get('Land', 'DE'))
        e_ustid = self.create_input(d_edit, "USt-Id"); e_ustid.insert(0, f_daten.get('UStId', ''))
        e_stnr = self.create_input(d_edit, "Steuernummer"); e_stnr.insert(0, f_daten.get('Steuernummer', ''))
        e_bank = self.create_input(d_edit, "Bank Name"); e_bank.insert(0, f_daten.get('BankName', ''))
        e_iban = self.create_input(d_edit, "IBAN"); e_iban.insert(0, f_daten.get('IBAN', ''))
        e_bic = self.create_input(d_edit, "BIC"); e_bic.insert(0, f_daten.get('BIC', ''))
        e_inhaber = self.create_input(d_edit, "Kontoinhaber"); e_inhaber.insert(0, f_daten.get('Kontoinhaber', ''))
        f_giro = ctk.CTkFrame(d_edit, fg_color="transparent"); f_giro.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(f_giro, text="", width=120).pack(side="left") # Platzhalter für saubere Einrückung
        chk_giro = ctk.CTkCheckBox(f_giro, text="Girocode (QR-Code) auf Rechnung andrucken")
        chk_giro.pack(side="left", padx=(10, 0))
        if str(f_daten.get('Girocode', '1')).lower() in ['true', '1', 'ja', 'yes']: chk_giro.select()
        else: chk_giro.deselect()
        # Falzmarken Checkbox ---
        f_falz = ctk.CTkFrame(d_edit, fg_color="transparent"); f_falz.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(f_falz, text="", width=120).pack(side="left")
        chk_falz = ctk.CTkCheckBox(f_falz, text="Falz- und Lochmarken (DIN Lang) andrucken")
        chk_falz.pack(side="left", padx=(10, 0))
        # Standardmäßig aktivieren (1)
        if str(f_daten.get('Falzmarken', '1')).lower() in ['true', '1', 'ja', 'yes']: chk_falz.select()
        else: chk_falz.deselect()
        # --------------------------------
        
        e_mail = self.create_input(d_edit, "Email"); e_mail.insert(0, f_daten.get('Email', ''))
        e_tel = self.create_input(d_edit, "Telefon"); e_tel.insert(0, f_daten.get('Telefon', ''))
       
        def save():
            name, plz, ort, iban = e_name.get().strip(), e_plz.get().strip(), e_ort.get().strip(), e_iban.get().strip()
            ustid, stnr = e_ustid.get().strip(), e_stnr.get().strip()
            if not name or not plz or not ort or not iban or (not ustid and not stnr):
                return messagebox.showwarning("Fehler", "Zwingend: Name, PLZ, Ort, IBAN, USt-Id ODER Steuernummer", parent=d_edit)
            
            speichere_firma(pfad_firma, {
                'FirmaName': name, 'Strasse': e_str.get().strip(), 'PLZ': plz, 'Ort': ort, 'Land': e_land.get().strip(), 
                'UStId': ustid, 'Steuernummer': stnr, 'BankName': e_bank.get().strip(), 'IBAN': iban, 'BIC': e_bic.get().strip(), 
                'Kontoinhaber': e_inhaber.get().strip(), 'Girocode': '1' if chk_giro.get() else '0', 
                'Falzmarken': '1' if chk_falz.get() else '0',
                'Email': e_mail.get().strip(), 'Telefon': e_tel.get().strip()
            })
            messagebox.showinfo("Gespeichert", "Firmendaten wurden aktualisiert!", parent=d_edit); d_edit.destroy()
            
        self.create_button(d_edit, text="Speichern", command=save).pack(pady=20)
             
    def open_kunden_manager(self):
        dialog = ctk.CTkToplevel(self); dialog.title("Kundendaten verwalten")
        self.center_window(dialog, 700, 500); dialog.transient(self); dialog.grab_set()
        scroll = ctk.CTkScrollableFrame(dialog); scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def refresh():
            for w in scroll.winfo_children(): w.destroy()
            for idx, k in enumerate(self.kunden_liste):
                f = ctk.CTkFrame(scroll); f.pack(fill="x", pady=2)
                self.create_button(f, text="🗑", width=30, fg_color="#b30000", hover_color="#800000", command=lambda i=idx: delete_k(i)).pack(side="right", padx=5, pady=5)
                self.create_button(f, text="✎", width=30, fg_color="#555", hover_color="#777", command=lambda i=idx: edit_k(i)).pack(side="right", padx=5, pady=5)
                ctk.CTkLabel(f, text=f"{k.get('Name','')} | {k.get('PLZ_Ort','')}", anchor="w").pack(side="left", padx=10, fill="x", expand=True)

        def delete_k(index):
            if messagebox.askyesno("Löschen", "Kunde wirklich löschen?", parent=dialog):
                del self.kunden_liste[index]
                speichere_alle_kunden(self.p_config.get("kunden_csv", "kunden.csv"), self.kunden_liste)
                refresh()

        def edit_k(index=None):
            d_edit = ctk.CTkToplevel(dialog); d_edit.title("Kunde bearbeiten" if index is not None else "Neuer Kunde")
            self.center_window(d_edit, 500, 350); d_edit.transient(dialog); d_edit.grab_set()
            
            e_name = self.create_input(d_edit, "Name"); e_str = self.create_input(d_edit, "Straße")
            e_plz = self.create_input(d_edit, "PLZ Ort"); e_nr = self.create_input(d_edit, "Kunden-Nr."); 
            e_az = self.create_input(d_edit, "Unser Zeichen"); e_k_az = self.create_input(d_edit, "Ihr Zeichen")
            e_endpoint = self.create_input(d_edit, "E-Mail / Leitweg-ID"); e_endpoint_scheme = self.create_input(d_edit, "Endpoint-Schema")
            
            if index is not None:
                k = self.kunden_liste[index]
                e_name.insert(0, k.get('Name','')); e_str.insert(0, k.get('Strasse',''))
                e_plz.insert(0, k.get('PLZ_Ort','')); e_nr.insert(0, k.get('KundeNr',''))
                e_az.insert(0, k.get('Aktenzeichen',''))
                e_k_az.insert(0, k.get('KundeAktenzeichen',''))
                e_endpoint.insert(0, k.get('Endpoint', k.get('Email', ''))); e_endpoint_scheme.insert(0, k.get('EndpointScheme', ''))
                
            def save():
                if not e_name.get().strip(): return messagebox.showwarning("Fehler", "Name darf nicht leer sein!", parent=d_edit)
                endpoint = e_endpoint.get().strip(); endpoint_scheme = e_endpoint_scheme.get().strip()
                if endpoint and not endpoint_scheme and '@' in endpoint: endpoint_scheme = 'EM'
                if endpoint and not endpoint_scheme:
                    return messagebox.showwarning("Fehler", "Für eine Leitweg-ID ist ein Endpoint-Schema erforderlich (regelmäßig 0204).", parent=d_edit)
                neu = {'Name': e_name.get().strip(), 'Strasse': e_str.get().strip(), 'PLZ_Ort': e_plz.get().strip(), 'Land': 'DE', 'KundeNr': e_nr.get().strip(), 'Aktenzeichen': e_az.get().strip(), 'KundeAktenzeichen': e_k_az.get().strip(), 'Endpoint': endpoint, 'EndpointScheme': endpoint_scheme}
                if index is not None: self.kunden_liste[index] = neu
                else: self.kunden_liste.append(neu)
                speichere_alle_kunden(self.p_config.get("kunden_csv", "kunden.csv"), self.kunden_liste)
                self.entry_k_name.configure(values=[k['Name'] for k in self.kunden_liste]); refresh(); d_edit.destroy()
                
            self.create_button(d_edit, text="Speichern", command=save).pack(pady=20)
        self.create_button(dialog, text="+ Neuen Kunden anlegen", command=lambda: edit_k()).pack(pady=10); refresh()

    def open_produkte_manager(self):
        dialog = ctk.CTkToplevel(self); dialog.title("Produktdaten verwalten")
        self.center_window(dialog, 700, 500); dialog.transient(self); dialog.grab_set()
        scroll = ctk.CTkScrollableFrame(dialog); scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def refresh():
            for w in scroll.winfo_children(): w.destroy()
            for idx, p in enumerate(self.produkte_liste):
                f = ctk.CTkFrame(scroll); f.pack(fill="x", pady=2)
                self.create_button(f, text="🗑", width=30, fg_color="#b30000", hover_color="#800000", command=lambda i=idx: delete_p(i)).pack(side="right", padx=5, pady=5)
                self.create_button(f, text="✎", width=30, fg_color="#555", hover_color="#777", command=lambda i=idx: edit_p(i)).pack(side="right", padx=5, pady=5)
                ctk.CTkLabel(f, text=f"{p.get('Bezeichnung','')} | {p.get('EinzelpreisNetto','0')}€ | {p.get('Steuersatz','19')}%", anchor="w").pack(side="left", padx=10, fill="x", expand=True)

        def delete_p(index):
            if messagebox.askyesno("Löschen", "Produkt wirklich löschen?", parent=dialog):
                del self.produkte_liste[index]
                speichere_alle_produkte(self.p_config.get("produkte_csv", "produkte.csv"), self.produkte_liste); refresh()

        def edit_p(index=None):
            d_edit = ctk.CTkToplevel(dialog); d_edit.title("Produkt bearbeiten" if index is not None else "Neues Produkt")
            self.center_window(d_edit, 500, 350); d_edit.transient(dialog); d_edit.grab_set()
            
            e_bez = self.create_input(d_edit, "Bezeichnung"); e_menge = self.create_input(d_edit, "Standard-Menge")
            e_einheit = self.create_input(d_edit, "Einheit", is_combo=True, combo_values=EINHEITEN_LISTE)
            e_preis = self.create_input(d_edit, "Einzelpreis (€)"); e_steuer = self.create_input(d_edit, "Steuer (%)")
            
            if index is not None:
                p = self.produkte_liste[index]
                e_bez.insert(0, p.get('Bezeichnung','')); e_menge.insert(0, f"{safe_float(p.get('Menge',1)):g}")
                e_preis.insert(0, p.get('EinzelpreisNetto','')); e_steuer.insert(0, p.get('Steuersatz','19'))
                c = p.get('Einheit', 'C62')
                for val in EINHEITEN_LISTE:
                    if c in val or EINHEITEN_MAPPING.get(c, c) in val: e_einheit.set(val); break
            else:
                e_menge.insert(0, "1"); e_einheit.set("Stück (C62)"); e_steuer.insert(0, "19")
                
            def save():
                if not e_bez.get().strip(): return messagebox.showwarning("Fehler", "Bezeichnung darf nicht leer sein!", parent=d_edit)
                try: float(e_menge.get().replace(',', '.') or "1"); float(e_preis.get().replace(',', '.') or "0.0"); float(e_steuer.get().replace(',', '.') or "19")
                except ValueError: return messagebox.showwarning("Eingabefehler", "Zahlenwerte fehlerhaft!", parent=d_edit)
                
                einheit_code = re.search(r'\((.*?)\)', e_einheit.get()).group(1).strip() if re.search(r'\((.*?)\)', e_einheit.get()) else e_einheit.get().strip()
                neu = {'Bezeichnung': e_bez.get().strip(), 'Menge': e_menge.get().replace(',','.'), 'Einheit': einheit_code, 'EinzelpreisNetto': e_preis.get().replace(',','.'), 'Steuersatz': e_steuer.get().replace(',','.')}
                if index is not None: self.produkte_liste[index] = neu
                else: self.produkte_liste.append(neu)
                speichere_alle_produkte(self.p_config.get("produkte_csv", "produkte.csv"), self.produkte_liste)
                refresh(); d_edit.destroy()
                
            self.create_button(d_edit, text="Speichern", command=save).pack(pady=20)
        self.create_button(dialog, text="+ Neues Produkt anlegen", command=lambda: edit_p()).pack(pady=10); refresh()

class TabHilfeMixin:
    def build_hilfe_tab(self):
        f = ctk.CTkFrame(self.tab_hilfe, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=40, pady=20)
        
        ctk.CTkLabel(f, text="Handbuch & Dokumentation", font=("Helvetica", 20, "bold")).pack(pady=(0, 10))
        ctk.CTkLabel(f, text="Das Handbuch wurde als HTML-Datei erstellt und öffnet sich in Ihrem Standard-Webbrowser.\n(Die Dateien 'SokoIur_Hilfe.html' und 'html.txt' liegen im Programmordner).", justify="center").pack(pady=(0, 15))
        
        self.create_button(f, text="📖 Handbuch im Browser öffnen", width=250, height=35, command=self.open_html_help).pack(pady=(0, 10))
        self.create_button(f, text="📜 Changelog im Browser öffnen", width=250, height=35, command=self.open_changelog_html).pack(pady=(0, 15))
        
        # --- NEU: Statistik-Bereich für Bearbeitungszahlen ---
        f_stat = ctk.CTkFrame(f, fg_color="#2b2b2b" if ctk.get_appearance_mode()=="Dark" else "#e6e6e6", corner_radius=8)
        f_stat.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(f_stat, text="📊 Programm- & Beleg-Statistik (Aktive Firma)", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
        
        akt_jahr = str(datetime.now().year)
        
        # Statistiken berechnen
        starts, out_ges, out_jahr, in_ges, in_jahr = self.berechne_statistiken(akt_jahr)
        
        stat_text = (
            f"• Programstarts insgesamt: {starts}\n\n"
            f"• Ausgangsrechnungen insgesamt: {out_ges}  |  Im laufenden Jahr ({akt_jahr}): {out_jahr}\n"
            f"• Eingangsrechnungen insgesamt: {in_ges}  |  Im laufenden Jahr ({akt_jahr}): {in_jahr}"
        )
        ctk.CTkLabel(f_stat, text=stat_text, justify="left", font=("Helvetica", 12)).pack(pady=(0, 15), padx=20)

    def berechne_statistiken(self, akt_jahr):
        # 1. Programmstarts zählen (über eine kleine Zählerdatei im Firmenordner oder Basis-Pfad)
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

        # 2. Ausgangsrechnungen zählen (aus dem Auswertungen-Ordner)
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
                                    anzahl = len(reader) - 1 # Kopfzeile abziehen
                                    out_ges += anzahl
                                    if str(akt_jahr) in f:
                                        out_jahr += anzahl
                        except:
                            pass

        # 3. Eingangsrechnungen zählen (aus dem Archivordner rchn)
        in_ges = 0
        in_jahr = 0
        eingang_ordner = self.p_config.get("eingangsrechnungen_ordner", "")
        if eingang_ordner and os.path.exists(eingang_ordner):
            for root, dirs, files in os.walk(eingang_ordner):
                for f in files:
                    if f.lower().endswith('_leseabschrift.pdf'):
                        continue
                    if f.upper().startswith('ER'):
                        in_ges += 1
                        if os.path.basename(root) == str(akt_jahr):
                            in_jahr += 1

        return starts, out_ges, out_jahr, in_ges, in_jahr

    def open_html_help(self):
        import webbrowser
        import os
        import tkinter.messagebox as messagebox
        from datenbank import get_appdata_dir
        
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
        import os
        import sys
        import tkinter.messagebox as messagebox
        
        try:
            from datenbank import get_appdata_dir
            app_dir = get_appdata_dir()
            changelog_pfad = os.path.join(app_dir, "changelog.html")
            
            if not os.path.exists(changelog_pfad):
                import hilfe_texte
                with open(changelog_pfad, "w", encoding="utf-8") as f:
                    f.write(hilfe_texte.get_changelog_html(getattr(self, 'current_version', '1.000')))
            
            if hasattr(os, 'startfile'):
                os.startfile(changelog_pfad)
            else:
                hilfe_url = changelog_pfad.replace("\\", "/")
                webbrowser.open(f"file:///{hilfe_url}")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Die Changelog-Datei konnte nicht geöffnet werden:\n\n{str(e)}", parent=self)
            
class UpdaterMixin:
    def enforce_network_version(self):
        base_path = self.config.get("base_data_path", "")
        if not base_path or not os.path.exists(base_path): return True
                
        version_file = os.path.join(base_path, "erech.txt")
        stored_version = ""
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as f:
                    stored_version = f.read().strip()
            except: pass
            
        def parse_v(v):
            if not v: return 0.0
            p = v.split('.')
            return float(p[0] + '.' + ''.join(p[1:]))
            
        c_v = parse_v(self.current_version)
        s_v = parse_v(stored_version)
        
        if c_v < s_v:
            self.withdraw()  # Hauptfenster verstecken, um Datenzugriff zu blockieren
            messagebox.showerror("Versionskonflikt", f"Die Daten wurden mit einer neueren Programmversion ({stored_version}) bearbeitet.\n\nUm Datenverlust im Netzwerk zu vermeiden, ist ein Update zwingend erforderlich!")
            self.check_for_updates(force=True)
            return False
        elif c_v > s_v:
            try:
                with open(version_file, "w") as f:
                    f.write(self.current_version)
            except: pass
        return True

    def check_for_updates(self, force=False):
        if not force:
            if not messagebox.askyesno("Verbindung herstellen?", "Möchten Sie jetzt die Verbindung zum Update-Server (erech.6078.de) herstellen?"): return
        else:
            if not messagebox.askyesno("Update erforderlich", "Möchten Sie jetzt zum Update-Server verbinden, um das zwingend erforderliche Update zu laden?\n(Bei 'Nein' wird das Programm sicherheitshalber beendet)"):
                self.do_update_exit()
                return
                
        if hasattr(self, 'btn_update'): self.btn_update.configure(text="⏳ Suche läuft...", state="disabled")
        if hasattr(self, 'btn_footer_update'): self.btn_footer_update.configure(text="⏳ Suche...", state="disabled")
        def _check():
            try:
                import ssl
                # --- NEU: SSL-Verifizierung deaktivieren ---
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                # --- NEU: Standard Browser User-Agent nutzen ---
                req = urllib.request.Request(
                    "https://erech.6078.de/erech.txt", 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Cache-Control': 'no-cache'}
                )
                with urllib.request.urlopen(req, context=ctx) as response: 
                    latest_version = response.read().decode('utf-8').strip()
                
                if not latest_version:
                    self.after(0, lambda: [
                        (self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal") if hasattr(self, 'btn_update') else None),
                        (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                        messagebox.showerror("Fehler", "Keine gültigen Versionsdaten auf dem Server gefunden."),
                        self.do_update_exit() if force else None
                    ])
                    return
                
                download_url = "https://erech.6078.de/SokoIur_eRechnung.exe"
                
                is_newer = False
                try:
                    def parse_v(v):
                        p = v.split('.')
                        return float(p[0] + '.' + ''.join(p[1:]))
                    
                    is_newer = parse_v(latest_version) > parse_v(self.current_version)
                except: 
                    is_newer = latest_version > self.current_version
                
                if is_newer: 
                    self.after(0, lambda: self.prompt_update(latest_version, download_url, force))
                else:
                    self.after(0, lambda: [
                        (self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal") if hasattr(self, 'btn_update') else None),
                        (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                        messagebox.showinfo("Update-Prüfung", f"Sie nutzen bereits die aktuellste Version!\n\nIhre: {self.current_version}\nOnline: {latest_version}") if not force else messagebox.showerror("Fehler", "Online ist keine neuere Version verfügbar. Abbruch!"),
                        self.do_update_exit() if force else None
                    ])
            except Exception as e:
                self.after(0, lambda: [
                    (self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal") if hasattr(self, 'btn_update') else None),
                    (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                    messagebox.showerror("Fehler", f"Fehler bei der Update-Prüfung:\n{str(e)}"),
                    self.do_update_exit() if force else None
                ])
        threading.Thread(target=_check, daemon=True).start()
    
    def prompt_update(self, latest_version, download_url, force=False):
        if hasattr(self, 'btn_update'): self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal")
        if hasattr(self, 'btn_footer_update'): self.btn_footer_update.configure(text="Update?", state="normal")
        
        msg = f"Version {latest_version} ist verfügbar!\nMöchten Sie diese jetzt herunterladen und installieren?"
        if force: msg = f"Zwingendes Update auf Version {latest_version} gefunden!\nJetzt installieren und neu starten?"
        
        if messagebox.askyesno("Update verfügbar!", msg):
            self.download_and_install_update(download_url)
        elif force:
            self.do_update_exit()

    def download_and_install_update(self, download_url):
        dl_win = ctk.CTkToplevel(self); dl_win.title("Update")
        self.center_window(dl_win, 300, 150); dl_win.transient(self); dl_win.grab_set()
        ctk.CTkLabel(dl_win, text="Lade Update herunter...\nBitte warten.", font=("Helvetica", 14)).pack(expand=True); self.update()
        
        def _download():
            try:
                import ssl
                import shutil
                import os
                import subprocess
                import urllib.request
                
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                # 1. Absolute Pfade des laufenden Programms ermitteln
                current_exe = os.path.abspath(sys.executable)
                exe_dir = os.path.dirname(current_exe)
                
                # 2. Ziel im Netzwerk ermitteln (Dein Vorschlag!)
                base_path = self.config.get("base_data_path", "")
                if base_path and os.path.exists(base_path):
                    dl_target = os.path.join(base_path, "SokoIur_eRechnung_Update.exe")
                else:
                    dl_target = os.path.join(exe_dir, "SokoIur_eRechnung_Update.exe")
                
                # 3. Download direkt dorthin durchführen
                req_dl = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req_dl, context=ctx) as response, open(dl_target, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                
                if not getattr(sys, 'frozen', False):
                    self.after(0, lambda: [dl_win.destroy(), messagebox.showinfo("Info", f"Update im Skript-Modus geladen nach:\n{dl_target}")])
                    return
                
                # --- AB HIER: ADMIN-RECHTE UND VERBESSERTER BATCH-CODE ---
                import tempfile
                import ctypes
                
                # 1. Batch-Datei im TEMP-Ordner erstellen (da C:\Programme schreibgeschützt ist!)
                bat_path = os.path.join(tempfile.gettempdir(), "sokoiur_update.bat")
                
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write('@echo off\n')
                    f.write(':loop\n')
                    f.write('timeout /t 1 /nobreak > NUL\n')
                    # Kopieren (überschreiben)
                    f.write(f'copy /Y "{dl_target}" "{current_exe}" > NUL\n')
                    # Wenn Fehler (Datei noch gelockt oder fehlende Rechte), nochmal versuchen
                    f.write('if errorlevel 1 goto loop\n')
                    # Nach Erfolg: Neues Programm starten und Batch löschen
                    f.write(f'start "" "{current_exe}"\n')
                    f.write('del "%~f0"\n')
                
                # 2. Batch-Datei mit Admin-Rechten ausführen (UAC-Prompt erscheint)
                # Der Parameter 0 (SW_HIDE) sorgt dafür, dass das schwarze Konsolenfenster unsichtbar bleibt
                ctypes.windll.shell32.ShellExecuteW(None, "runas", bat_path, None, None, 0)
                
                # 3. Update-Fenster schließen und altes Programm sofort beenden
                self.after(0, self.do_update_exit)
                                
            except Exception as e:
                self.after(0, lambda: [dl_win.destroy(), messagebox.showerror("Fehler", f"Download fehlgeschlagen:\n{str(e)}")])
                
        threading.Thread(target=_download, daemon=True).start()

    def do_update_exit(self):
        # --- NEU: Lock-Datei vor dem Update-Neustart zwingend entfernen ---
        try:
            if hasattr(self, 'unlock_firm'):
                self.unlock_firm()
        except Exception as e:
            print(f"Fehler beim Entfernen der Lock-Datei während des Updates: {e}")
                
        self.destroy()
        import sys
        sys.exit(0)
    

class TabErfassenMixin:
    def build_erfassen_tab(self):
        if not hasattr(self, 'skipped_incoming_files'):
            self.skipped_incoming_files = set()

        f = ctk.CTkFrame(self.tab_erfassen)
        f.pack(pady=15, padx=20, fill="both", expand=True)

        ctk.CTkLabel(f, text="Eingangsrechnungen erfassen", font=("Helvetica", 16, "bold")).pack(pady=(12, 4))

        folder = self.p_config.get('eingangsordner', '')
        self.lbl_eingangsordner = ctk.CTkLabel(f, text=f"Eingangsordner (reneu): {folder}", wraplength=780, justify="center")
        self.lbl_eingangsordner.pack(padx=15, pady=2)

        ctk.CTkLabel(
            f,
            text="Die formelle und rechnerische Prüfung ist eine automatisierte Plausibilitätsprüfung und keine steuerliche oder rechtliche Freigabe.",
            text_color="orange", wraplength=780, justify="center"
        ).pack(pady=4)

        btn_bar = ctk.CTkFrame(f, fg_color="transparent")
        btn_bar.pack(pady=8)
        self.create_button(
            btn_bar, text="📥 Nächste Eingangsrechnung prüfen", command=self.process_next_incoming,
            fg_color="#1f538d", hover_color="#14375d", height=36, width=260
        ).pack(side="left", padx=6)
        self.create_button(
            btn_bar, text="🔄 Liste aktualisieren", command=self.refresh_incoming_list,
            fg_color="#444", hover_color="#666", height=36, width=160
        ).pack(side="left", padx=6)
        self.create_button(
            btn_bar, text="📂 Ordner öffnen", command=self.open_incoming_folder,
            fg_color="#444", hover_color="#666", height=36, width=140
        ).pack(side="left", padx=6)

        ctk.CTkLabel(f, text="Wartende Belege im Eingangsordner:", font=("Helvetica", 13, "bold")).pack(pady=(8, 2))
        self.incoming_scroll = ctk.CTkScrollableFrame(f, height=220)
        self.incoming_scroll.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(
            f,
            text="Nach der Erfassung wird das Original im Jahresordner „rebearb/<Jahr>“ archiviert; die nummerierte Archivkopie wird unter „rchn/<Jahr>“ gespeichert.",
            wraplength=750, justify="center", text_color="gray"
        ).pack(pady=6)

        self.refresh_incoming_list()

    def open_incoming_folder(self):
        folder = self.p_config.get('eingangsordner', '')
        if folder and os.path.isdir(folder):
            try:
                os.startfile(folder)
            except Exception:
                subprocess.Popen(['explorer', folder])
        else:
            messagebox.showwarning("Ordner fehlt", f"Der Ordner existiert noch nicht:\n{folder}")

    def _open_file_external(self, path):
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Datei konnte nicht geöffnet werden:\n{e}")

    def _remove_duplicate_source_file(self, path):
        """Entfernt eine als Duplikat erkannte Datei aus reneu (oder verschiebt sie nach rebearb)."""
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            wait = self.p_config.get('eingang_loesch_warteliste', []) or []
            abs_p = os.path.abspath(path)
            if abs_p not in [os.path.abspath(x) for x in wait]:
                wait.append(path)
                self.p_config['eingang_loesch_warteliste'] = wait
                speichere_config(self.config)
        self.refresh_incoming_list()

    def refresh_incoming_list(self):
        if not hasattr(self, 'incoming_scroll'):
            return
        from eingangsrechnung import check_duplicate_incoming

        for w in self.incoming_scroll.winfo_children():
            w.destroy()

        self._retry_incoming_deletions()
        folder = self.p_config.get('eingangsordner', '')
        if not folder or not os.path.isdir(folder):
            ctk.CTkLabel(self.incoming_scroll, text="Eingangsordner noch nicht angelegt.", text_color="gray").pack(pady=15)
            return

        waiting_list = self.p_config.get('eingang_loesch_warteliste', []) or []
        norm_wait = {os.path.abspath(p) for p in waiting_list if p}

        # Dateien auf der Lösch-Warteliste werden direkt ausgeblendet, damit sie niemals doppelt erfasst werden
        all_files = sorted([
            os.path.join(folder, x) for x in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, x)) and not x.startswith('.')
        ])
        files = [f for f in all_files if os.path.abspath(f) not in norm_wait]

        if hasattr(self, 'skipped_incoming_files'):
            self.skipped_incoming_files.intersection_update(files)

        if not files:
            hinweis = "Keine offenen Eingangsrechnungen im Ordner vorhanden."
            if len(all_files) > len(files):
                hinweis += f" ({len(all_files) - len(files)} bereits erfasste Datei(en) warten auf automatische Löschung nach Schließen des PDF-Viewers)."
            ctk.CTkLabel(self.incoming_scroll, text=hinweis, text_color="gray", wraplength=680).pack(pady=15)
            return

        journal_folder = self.p_config.get('eingangsjournal_ordner', '')
        
        # NEU: Journale genau EINMAL auslesen, bevor die Schleife startet!
        alle_journale = load_all_journal_entries(journal_folder)

        for idx, fpath in enumerate(files):
            row = ctk.CTkFrame(self.incoming_scroll)
            row.pack(fill="x", pady=2, padx=4)
            fname = os.path.basename(fpath)
            is_skipped = fpath in getattr(self, 'skipped_incoming_files', set())
            
            # NEU: Die Variable "alle_journale" per Parameter 'entries' übergeben
            is_dup, dup_reason, dup_rec = check_duplicate_incoming(
                fpath, journal_folder, waiting_list, entries=alle_journale
            )

            status_tag = ""
            lbl_color = None
            if is_dup:
                er_id = dup_rec.get("Interne ER-Nr.", "") if dup_rec else ""
                status_tag = f" [BEREITS ERFASST: {er_id}]"
                lbl_color = "#d9534f"
            elif is_skipped:
                status_tag = " (Zurückgestellt)"

            lbl_kwargs = {"text": f"{idx+1}. {fname}{status_tag}", "anchor": "w"}
            if lbl_color:
                lbl_kwargs["text_color"] = lbl_color
            ctk.CTkLabel(row, **lbl_kwargs).pack(side="left", padx=10, pady=4, fill="x", expand=True)

            if is_dup:
                self.create_button(
                    row, text="🗑 Duplikat entfernen", width=140, fg_color="#b30000", hover_color="#800000",
                    command=lambda p=fpath: self._remove_duplicate_source_file(p)
                ).pack(side="right", padx=4, pady=4)

            self.create_button(
                row, text="👁 Öffnen", width=80, fg_color="#555", hover_color="#777",
                command=lambda p=fpath: self._open_file_external(p)
            ).pack(side="right", padx=4, pady=4)
            self.create_button(
                row, text="Prüfen", width=90, fg_color="#1f538d", hover_color="#14375d",
                command=lambda p=fpath: self.process_next_incoming(specific_path=p)
            ).pack(side="right", padx=4, pady=4)

    def process_next_incoming(self, specific_path=None):
        from eingangsrechnung import detect_invoice, parse_einvoice, error_notice, check_duplicate_incoming
        folder = self.p_config.get('eingangsordner', '')
        if not os.path.isdir(folder):
            return messagebox.showwarning('Eingangsordner fehlt', f'Der Eingangsordner existiert nicht:\n{folder}')

        self._retry_incoming_deletions()
        waiting_list = self.p_config.get('eingang_loesch_warteliste', []) or []
        norm_wait = {os.path.abspath(p) for p in waiting_list if p}

        files = sorted([
            os.path.join(folder, x) for x in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, x)) and not x.startswith('.') and os.path.abspath(os.path.join(folder, x)) not in norm_wait
        ])
        if not files:
            self.refresh_incoming_list()
            return messagebox.showinfo('Keine Eingangsrechnungen', f'Im Ordner\n{folder}\nsind keine unbearbeiteten Eingangsrechnungen vorhanden.')

        if specific_path and os.path.exists(specific_path):
            path = specific_path
        else:
            unskipped = [f for f in files if f not in getattr(self, 'skipped_incoming_files', set())]
            if not unskipped:
                self.skipped_incoming_files.clear()
                unskipped = files
            path = unskipped[0]

        journal_folder = self.p_config.get('eingangsjournal_ordner', '')

        # 1. Vorab-Duplikatsprüfung über Datei-Hash / Lösch-Warteliste
        is_dup, dup_msg, _ = check_duplicate_incoming(path, journal_folder, waiting_list)
        if is_dup:
            if messagebox.askyesno(
                "Bereits erfasste Rechnung erkannt",
                f"Erneute Erfassung blockiert:\n\n{dup_msg}\n\n"
                f"Datei im Eingangsordner: {os.path.basename(path)}\n\n"
                f"Soll diese doppelt vorhandene Datei jetzt aus dem Eingangsordner (reneu) entfernt werden?"
            ):
                self._remove_duplicate_source_file(path)
            else:
                self.skipped_incoming_files.add(path)
                self.refresh_incoming_list()
            return

        kind, xml, detail = detect_invoice(path)
        if kind in ('ZUGFeRD', 'XRechnung'):
            data, errors = parse_einvoice(xml, kind)
            # 2. Inhaltliche Duplikatsprüfung (Lieferant + Externe RE-Nr. + Bruttobetrag)
            is_dup_content, dup_msg_content, _ = check_duplicate_incoming(path, journal_folder, waiting_list, invoice_data=data)
            if is_dup_content:
                if messagebox.askyesno(
                    "Bereits erfasste Rechnung erkannt",
                    f"Erneute Erfassung blockiert:\n\n{dup_msg_content}\n\n"
                    f"Datei im Eingangsordner: {os.path.basename(path)}\n\n"
                    f"Soll diese doppelt vorhandene Datei jetzt aus dem Eingangsordner (reneu) entfernt werden?"
                ):
                    self._remove_duplicate_source_file(path)
                else:
                    self.skipped_incoming_files.add(path)
                    self.refresh_incoming_list()
                return

            if errors:
                subject, body = error_notice(data, errors)
                self._show_invoice_error(path, kind, data, subject, body)
                return
            self._show_einvoice_confirmation(path, kind, data, xml)
        else:
            self._show_other_invoice_form(path, detail)

    def _retry_incoming_deletions(self):
        waiting = self.p_config.get('eingang_loesch_warteliste', []) or []
        left = []
        for path in waiting:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                left.append(path)
        if left != waiting:
            self.p_config['eingang_loesch_warteliste'] = left
            speichere_config(self.config)

    def _show_invoice_error(self, path, kind, data, subject, body):
        d = ctk.CTkToplevel(self)
        d.title('Formelle Prüfung nicht bestanden')
        self.center_window(d, 760, 620)
        d.transient(self)
        d.grab_set()

        ctk.CTkLabel(
            d, text=f'{kind}-Rechnung ({os.path.basename(path)}): Prüfung nicht bestanden',
            font=('Helvetica', 14, 'bold'), text_color='#b30000'
        ).pack(pady=10)

        info_text = (
            f"Aussteller: {data.get('supplier') or 'nicht auslesbar'} | "
            f"E-Mail: {data.get('supplier_email') or 'nicht auslesbar'}\n"
            f"Rechnungsnummer: {data.get('number') or 'nicht auslesbar'} | "
            f"Rechnungsdatum: {data.get('date') or 'nicht auslesbar'}"
        )
        ctk.CTkLabel(d, text=info_text, justify='left').pack(padx=20, anchor='w')

        ctk.CTkLabel(d, text='Kopierbarer Betreff:').pack(padx=20, pady=(10, 0), anchor='w')
        e = ctk.CTkEntry(d)
        e.insert(0, subject)
        e.pack(fill='x', padx=20)

        ctk.CTkLabel(d, text='Kopierbarer Hinweis an den Rechnungsaussteller:').pack(padx=20, pady=(10, 0), anchor='w')
        t = ctk.CTkTextbox(d, height=220)
        t.insert('1.0', body)
        t.pack(fill='both', expand=True, padx=20, pady=4)

        bf = ctk.CTkFrame(d, fg_color='transparent')
        bf.pack(pady=12)

        def skip_and_close():
            self.skipped_incoming_files.add(path)
            d.destroy()
            self.refresh_incoming_list()

        def force_manual():
            d.destroy()
            self._show_other_invoice_form(path, detail="Trotz XML-Prüffehler manuell erfassen", prefill=data)

        self.create_button(bf, text='👁 Datei öffnen', width=130, fg_color='#555', command=lambda: self._open_file_external(path)).pack(side='left', padx=6)
        self.create_button(bf, text='⏭ Überspringen (Später)', width=180, fg_color='#666', command=skip_and_close).pack(side='left', padx=6)
        self.create_button(bf, text='⚠️ Trotzdem manuell erfassen', width=210, fg_color='#b85c00', command=force_manual).pack(side='left', padx=6)

    def _show_einvoice_confirmation(self, path, kind, data, xml):
        from eingangsrechnung import _money
        d = ctk.CTkToplevel(self)
        d.title('Eingangsrechnung prüfen und erfassen')
        self.center_window(d, 640, 560)
        d.transient(self)
        d.grab_set()

        ctk.CTkLabel(
            d, text=f'Gültige {kind}-Rechnung – Zusammenfassung',
            font=('Helvetica', 15, 'bold'), text_color='#208000'
        ).pack(pady=12)

        lines = [
            f"Quelldatei: {os.path.basename(path)}",
            f"Rechnungsaussteller: {data.get('supplier', '')}",
            f"Anschrift: {data.get('supplier_street', '')}, {data.get('supplier_zip', '')} {data.get('supplier_city', '')}".strip(", "),
            f"USt-IdNr. / StNr.: {data.get('supplier_tax_id', '')}",
            f"Rechnungsnummer: {data.get('number', '')}",
            f"Rechnungsdatum: {data.get('date', '')}",
            f"Leistungs-/Lieferdatum: {data.get('delivery_date', '') or '-'}",
            f"Fälligkeitsdatum: {data.get('due_date', '') or '-'}",
            f"Netto: {_money(data.get('net', '0'))} EUR",
            f"Umsatzsteuer: {_money(data.get('tax', '0'))} EUR",
            f"Brutto: {_money(data.get('gross', '0'))} EUR",
        ]
        ctk.CTkLabel(d, text='\n'.join(lines), justify='left').pack(padx=35, anchor='w')

        var = ctk.BooleanVar(value=bool(self.p_config.get('xrechnung_leseabschrift', True)))
        if kind == 'XRechnung':
            ctk.CTkCheckBox(d, text='Lesbare PDF-Leseabschrift im Archiv erstellen', variable=var).pack(pady=12)

        def yes():
            if kind == 'XRechnung':
                self.p_config['xrechnung_leseabschrift'] = bool(var.get())
                speichere_config(self.config)
            d.destroy()
            self._archive_incoming(path, kind, data, xml, bool(var.get()) if kind == 'XRechnung' else False, True)

        def skip():
            self.skipped_incoming_files.add(path)
            d.destroy()
            self.refresh_incoming_list()

        bf = ctk.CTkFrame(d, fg_color='transparent')
        bf.pack(pady=20)
        self.create_button(bf, text='👁 Beleg ansehen', command=lambda: self._open_file_external(path), width=140, fg_color='#555').pack(side='left', padx=6)
        self.create_button(bf, text='Nein – zurückstellen', command=skip, width=160, fg_color='#666').pack(side='left', padx=6)
        self.create_button(bf, text='Ja – jetzt erfassen', command=yes, width=200, fg_color='#208000').pack(side='left', padx=6)

    def _show_other_invoice_form(self, path, detail='', prefill=None):
        from eingangsrechnung import _d, normalize_date_de, check_duplicate_incoming
        d = ctk.CTkToplevel(self)
        d.title('Sonstige Eingangsrechnung erfassen')
        self.center_window(d, 640, 680)
        d.transient(self)
        d.grab_set()

        ctk.CTkLabel(d, text='Erfassung einer Rechnung (Manuelle Ergänzung)', font=('Helvetica', 14, 'bold')).pack(pady=(12, 4))
        ctk.CTkLabel(d, text=f"Datei: {os.path.basename(path)} ({detail})", text_color="gray").pack(pady=(0, 8))

        self.create_button(d, text="👁 Originaldatei zur Ansicht öffnen", width=240, fg_color="#555", command=lambda: self._open_file_external(path)).pack(pady=4)

        kind = ctk.StringVar(value='PDF-Rechnung')
        ff = ctk.CTkFrame(d, fg_color='transparent')
        ff.pack(pady=6)
        for x in ('PDF-Rechnung', 'Gescannte Papierrechnung', 'Sonstiges'):
            ctk.CTkRadioButton(ff, text=x, variable=kind, value=x).pack(side='left', padx=8)

        entries = {}
        fields = [
            ('Lieferant *', 'supplier'),
            ('Externe Rechnungs-Nr. *', 'number'),
            ('Rechnungsdatum (TT.MM.JJJJ) *', 'date'),
            ('Nettobetrag (€)', 'net'),
            ('Umsatzsteuer (€)', 'tax'),
            ('Bruttobetrag (€)', 'gross'),
        ]
        for label, key in fields:
            entries[key] = self.create_input(d, label)

        combo_vat = self.create_input(d, "Steuersatz (%)", is_combo=True, combo_values=["19", "7", "0"])
        combo_vat.set("19")

        if prefill:
            for k in ('supplier', 'number', 'date', 'net', 'tax', 'gross'):
                if prefill.get(k):
                    entries[k].insert(0, str(prefill.get(k)))
        else:
            entries['date'].insert(0, datetime.now().strftime('%d.%m.%Y'))

        checked = ctk.CTkCheckBox(d, text='Ich habe geprüft, dass diese Rechnung zum Vorsteuerabzug berechtigt')
        checked.pack(pady=10)

        ctk.CTkLabel(
            d,
            text='Hinweis: Mindestens Netto oder Brutto eingeben. Fehlende Beträge werden anhand des gewählten Steuersatzes berechnet.',
            text_color='orange', wraplength=540, justify='center'
        ).pack(pady=4)

        def save():
            supplier = entries['supplier'].get().strip()
            number = entries['number'].get().strip()
            raw_date = entries['date'].get().strip()
            norm_date = normalize_date_de(raw_date)

            if not supplier:
                return messagebox.showwarning('Angabe fehlt', 'Bitte geben Sie den Namen des Lieferanten ein.', parent=d)
            if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', norm_date):
                return messagebox.showwarning('Datumsformat', 'Bitte geben Sie ein gültiges Rechnungsdatum ein (z. B. 15.03.2026).', parent=d)

            net_str = entries['net'].get().strip()
            tax_str = entries['tax'].get().strip()
            gross_str = entries['gross'].get().strip()

            net = _d(net_str) if net_str else Decimal('0.00')
            tax = _d(tax_str) if tax_str else Decimal('0.00')
            gross = _d(gross_str) if gross_str else Decimal('0.00')

            rate_dec = _d(combo_vat.get(), '19.00')
            rate_factor = rate_dec / Decimal('100.00')

            if not net_str and not gross_str:
                return messagebox.showwarning('Angabe fehlt', 'Bitte mindestens Netto oder Brutto eingeben.', parent=d)

            if net_str and not tax_str and not gross_str:
                tax = (net * rate_factor).quantize(Decimal('0.01'))
                gross = net + tax
            elif net_str and tax_str and not gross_str:
                gross = net + tax
            elif gross_str and not net_str and not tax_str:
                net = (gross / (Decimal('1.00') + rate_factor)).quantize(Decimal('0.01'))
                tax = gross - net
            elif gross_str and tax_str and not net_str:
                net = gross - tax
            elif net_str and gross_str and not tax_str:
                tax = gross - net

            if abs((net + tax) - gross) > Decimal('0.05'):
                return messagebox.showwarning(
                    'Rechenfehler',
                    f'Netto ({net} €) + Steuer ({tax} €) stimmt nicht mit Brutto ({gross} €) überein!',
                    parent=d
                )

            rate_key = str(int(rate_dec)) if rate_dec == int(rate_dec) else str(rate_dec)
            taxes_dict = {rate_key: tax} if tax != Decimal('0.00') else {}

            data = {
                'supplier': supplier,
                'number': number or 'ohne Nr.',
                'date': norm_date,
                'net': str(net),
                'tax': str(tax),
                'gross': str(gross),
                'taxes': taxes_dict,
                'delivery_date': ''
            }

            # Duplikatsprüfung vor dem Speichern
            is_dup, dup_msg, _ = check_duplicate_incoming(
                path,
                self.p_config.get('eingangsjournal_ordner', ''),
                self.p_config.get('eingang_loesch_warteliste', []),
                invoice_data=data
            )
            if is_dup:
                return messagebox.showerror(
                    'Duplikat erkannt',
                    f'Diese Rechnung kann nicht erneut erfasst werden:\n\n{dup_msg}',
                    parent=d
                )

            d.destroy()
            self._archive_incoming(path, kind.get(), data, None, False, bool(checked.get()))

        def skip():
            self.skipped_incoming_files.add(path)
            d.destroy()
            self.refresh_incoming_list()

        bf = ctk.CTkFrame(d, fg_color='transparent')
        bf.pack(pady=14)
        self.create_button(bf, text='Abbrechen / Zurückstellen', command=skip, fg_color='#666', width=180).pack(side='left', padx=6)
        self.create_button(bf, text='Als Eingangsrechnung erfassen', command=save, fg_color='#208000', width=220).pack(side='left', padx=6)

    def _archive_incoming(self, path, kind, data, xml, make_pdf, vat_checked):
        from eingangsrechnung import (
            next_number, write_journal, make_readable_pdf, _d, _money,
            normalize_date_de, file_sha256, check_duplicate_incoming
        )

        # Letzte Sicherheitsbarriere gegen doppelte Erfassung unmittelbar vor Nummernvergabe
        is_dup, dup_msg, _ = check_duplicate_incoming(
            path,
            self.p_config.get('eingangsjournal_ordner', ''),
            self.p_config.get('eingang_loesch_warteliste', []),
            invoice_data=data
        )
        if is_dup:
            messagebox.showerror("Bereits erfasst", f"Erfassung abgebrochen, da die Rechnung bereits existiert:\n\n{dup_msg}")
            self.refresh_incoming_list()
            return

        f_hash = file_sha256(path)
        today_str = datetime.now().strftime('%d.%m.%Y')
        invoice_date = normalize_date_de(data.get('date', '')) or today_str
        year = invoice_date[-4:] if re.match(r'^\d{2}\.\d{2}\.\d{4}$', invoice_date) else str(datetime.now().year)

        nr = next_number(self.p_config.get('letzte_eingangsrechnungsnummer', ''), year)

        work = os.path.join(self.p_config['bearbeitete_eingangsrechnungen_ordner'], year)
        arch = os.path.join(self.p_config['eingangsrechnungen_ordner'], year)
        os.makedirs(work, exist_ok=True)
        os.makedirs(arch, exist_ok=True)

        ext = os.path.splitext(path)[1].lower() or '.dat'
        archive_main = os.path.join(arch, nr + ext)

        base_name = os.path.basename(path)
        work_target = os.path.join(work, base_name)
        if os.path.exists(work_target):
            work_target = os.path.join(work, f"{nr}_{base_name}")

        try:
            shutil.move(path, work_target)
        except Exception:
            shutil.copy2(path, work_target)
            wait = self.p_config.get('eingang_loesch_warteliste', []) or []
            if path not in wait:
                wait.append(path)
                self.p_config['eingang_loesch_warteliste'] = wait

        shutil.copy2(work_target if os.path.exists(work_target) else path, archive_main)

        if make_pdf:
            readable = os.path.join(arch, nr + '_Leseabschrift.pdf')
            try:
                make_readable_pdf(data, readable)
            except Exception as e:
                print(f"Leseabschrift konnte nicht erzeugt werden: {e}")

        taxes = data.get('taxes', {}) or {}
        t19 = _d(taxes.get('19', taxes.get('19.0', taxes.get('19.00', '0'))))
        t7 = _d(taxes.get('7', taxes.get('7.0', taxes.get('7.00', '0'))))
        other = _d(data.get('tax')) - t19 - t7

        record = {
            'Interne ER-Nr.': nr,
            'Eingangsdatum': today_str,
            'Rechnungsdatum': invoice_date,
            'Lieferant': data.get('supplier', ''),
            'Externe Rechnungsnummer': data.get('number', ''),
            'Format': kind,
            'Netto': _money(data.get('net')),
            'MwSt_19': _money(t19),
            'MwSt_7': _money(t7),
            'MwSt_sonstige': _money(other),
            'Brutto': _money(data.get('gross')),
            'Vorsteuer geprüft': 'Ja' if vat_checked else 'Nein',
            'Quelldatei': os.path.basename(path),
            'Archivdatei': archive_main,
            'Dateihash': f_hash,
        }

        write_journal(self.p_config['eingangsjournal_ordner'], record)
        self.p_config['letzte_eingangsrechnungsnummer'] = nr
        speichere_config(self.config)

        if hasattr(self, 'lbl_letzte_er_nr'):
            self.lbl_letzte_er_nr.configure(text=nr)
        if hasattr(self, 'combo_eingang_jahr'):
            ej_path = self.p_config.get("eingangsjournal_ordner", "")
            if os.path.isdir(ej_path):
                years = sorted([x for x in os.listdir(ej_path) if re.fullmatch(r"\d{4}", x)], reverse=True)
                if years:
                    self.combo_eingang_jahr.configure(values=years)
                    self.combo_eingang_jahr.set(year if year in years else years[0])
        if hasattr(self, 'refresh_eingang_journal_ui'):
            self.refresh_eingang_journal_ui()

        self.skipped_incoming_files.discard(path)
        self.refresh_incoming_list()

        messagebox.showinfo(
            'Eingangsrechnung erfasst',
            f'Die Eingangsrechnung {nr} wurde erfolgreich erfasst und archiviert.\n\nArchiv: {archive_main}'
        )
