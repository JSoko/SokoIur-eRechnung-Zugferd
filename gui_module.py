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
from hilfe_texte import get_doku_text, HILFE_KAPITEL

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
        pfad = filedialog.askopenfilename(title="Rechnungs-CSV wählen", filetypes=[("CSV-Dateien", "*.csv*"), ("Alle Dateien", "*.*")])
        if pfad: self.load_manual_invoice(is_button_click=True, custom_path=pfad)

    def open_kdnr_search(self, entry_widget):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Kundennummer suchen")
        self.center_window(dialog, 350, 400)
        dialog.transient(self); dialog.grab_set()
        
        kunden_mit_nr = sorted([k for k in self.kunden_liste if k.get('KundeNr', '').strip()], key=lambda k: int(re.sub(r'\D', '', k.get('KundeNr', '')) or 0))
        if not kunden_mit_nr:
            ctk.CTkLabel(dialog, text="Keine Kunden mit gespeicherter Kundennummer vorhanden.", wraplength=300).pack(pady=20, padx=20)
            self.create_button(dialog, text="Schließen", command=dialog.destroy).pack(pady=10)
            return

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def select_kdnr(k):
            self.entry_k_name.set(k.get('Name', ''))
            self.entry_k_strasse.delete(0, 'end'); self.entry_k_strasse.insert(0, k.get('Strasse', ''))
            self.entry_k_plz_ort.delete(0, 'end'); self.entry_k_plz_ort.insert(0, k.get('PLZ_Ort', ''))
            self.entry_k_nr.delete(0, 'end'); self.entry_k_nr.insert(0, k.get('KundeNr', ''))
            self.entry_az.delete(0, 'end'); self.entry_az.insert(0, k.get('Aktenzeichen', ''))
            dialog.destroy()

        for k in kunden_mit_nr:
            self.create_button(scroll, text=f"Nr: {k.get('KundeNr')} - {k.get('Name')}", anchor="w", command=lambda k_obj=k: select_kdnr(k_obj)).pack(fill="x", pady=2)

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
        
        self.chk_kunde_speichern = ctk.CTkCheckBox(left_frame, text="Kunde speichern/updaten"); self.chk_kunde_speichern.pack(pady=3, padx=10, anchor="w")
        if self.p_config.get("keep_kunde_speichern", False): self.chk_kunde_speichern.select()
        
        self.create_button(left_frame, text="📝 Texte bearbeiten (Alt+T)", command=self.open_texte_popup).pack(pady=15, padx=10, fill="x")
        ctk.CTkFrame(left_frame, height=2, fg_color="#555").pack(fill="x", pady=10, padx=10)
        self.lbl_totals = ctk.CTkLabel(left_frame, text="Netto Gesamt: 0,00 €\nBrutto Gesamt: 0,00 €", justify="left", font=("Helvetica", 14, "bold"))
        self.lbl_totals.pack(pady=5, padx=15, anchor="w")
        
        ctk.CTkLabel(right_frame, text="Positionen", font=("Helvetica", 14, "bold")).pack(pady=10)
        self.pos_scroll = ctk.CTkScrollableFrame(right_frame); self.pos_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_button(right_frame, text="+ Position hinzufügen (+)", command=self.open_pos_popup).pack(pady=10)
        self.create_button(right_frame, text="Nur Speichern [CSV] (Alt+S)", fg_color="green", hover_color="darkgreen", command=self.save_manual_invoice).pack(pady=5, fill="x", padx=20)
        self.create_button(right_frame, text="Speichern, PDF erstellen & öffnen (Alt+P)", fg_color="#b85c00", hover_color="#8f4700", command=self.save_generate_open_exit).pack(pady=5, fill="x", padx=20)

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
                self.entry_k_nr.delete(0, 'end'); self.entry_k_nr.insert(0, kopf.get('KundeNr', ''))
                self.entry_az.delete(0, 'end'); self.entry_az.insert(0, kopf.get('Aktenzeichen', ''))
                self.entry_lz_kopf.delete(0, 'end'); self.entry_lz_kopf.insert(0, kopf.get('LeistungszeitraumKopf', ''))
                self.entry_k_plz_ort.delete(0, 'end'); self.entry_k_plz_ort.insert(0, f"{kopf.get('KundePLZ', '')} {kopf.get('KundeOrt', '')}".strip())
                
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
        dialog = ctk.CTkToplevel(self); dialog.title("Texte bearbeiten")
        self.center_window(dialog, 600, 600); dialog.transient(self); dialog.grab_set() 
        
        ctk.CTkLabel(dialog, text="Zentrierter Header (über Rechnungs-Nr.):").pack(anchor="w", padx=20, pady=(10, 0))
        t_head = ctk.CTkTextbox(dialog, height=60); t_head.pack(fill="x", padx=20, pady=2); t_head.insert("0.0", self.header_text)
        chk_head = ctk.CTkCheckBox(dialog, text="Merken"); chk_head.pack(anchor="w", padx=20, pady=(0, 10))
        if self.p_config.get("keep_header", True): chk_head.select()
        
        ctk.CTkLabel(dialog, text="Einleitung (vor Positionen):").pack(anchor="w", padx=20, pady=(5, 0))
        t_einl = ctk.CTkTextbox(dialog, height=80); t_einl.pack(fill="x", padx=20, pady=2); t_einl.insert("0.0", self.einleitung_text)
        chk_einl = ctk.CTkCheckBox(dialog, text="Merken"); chk_einl.pack(anchor="w", padx=20, pady=(0, 10))
        if self.p_config.get("keep_einleitung", True): chk_einl.select()
        
        ctk.CTkLabel(dialog, text="Gruß (unten):").pack(anchor="w", padx=20, pady=(5, 0))
        t_gruss = ctk.CTkTextbox(dialog, height=80); t_gruss.pack(fill="x", padx=20, pady=2); t_gruss.insert("0.0", self.gruss_text)
        chk_gruss = ctk.CTkCheckBox(dialog, text="Merken"); chk_gruss.pack(anchor="w", padx=20, pady=(0, 10))
        if self.p_config.get("keep_gruss", True): chk_gruss.select()
        
        def save_texte():
            self.header_text, self.einleitung_text, self.gruss_text = t_head.get("0.0", "end").strip(), t_einl.get("0.0", "end").strip(), t_gruss.get("0.0", "end").strip()
            self.p_config["keep_header"], self.p_config["keep_einleitung"], self.p_config["keep_gruss"] = bool(chk_head.get()), bool(chk_einl.get()), bool(chk_gruss.get())
            speichere_config(self.config); dialog.destroy()
            
        self.create_button(dialog, text="Übernehmen", command=save_texte).pack(pady=20)

    def open_pos_popup(self, edit_index=None):
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

    def save_manual_invoice(self, silent=False):
        if not self.positionen_liste: 
            messagebox.showwarning("Fehler", "Bitte erfassen Sie zunächst Positionen!"); return False
        r_datum = parse_flexible_date(self.entry_r_datum.get()); f_datum = parse_flexible_date(self.entry_f_datum.get())
        lz_kopf = parse_flexible_date_span(self.entry_lz_kopf.get())
        try:
            datetime.strptime(r_datum, "%Y-%m-%d"); datetime.strptime(f_datum, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Fehler", "Datumsangaben fehlerhaft!"); return False
            
        self.entry_r_datum.delete(0, 'end'); self.entry_r_datum.insert(0, r_datum)
        self.entry_f_datum.delete(0, 'end'); self.entry_f_datum.insert(0, f_datum)
        self.entry_lz_kopf.delete(0, 'end'); self.entry_lz_kopf.insert(0, lz_kopf)
        r_nr = self.entry_r_nr.get()
        plz_ort = self.entry_k_plz_ort.get().split(' ', 1)
        plz = plz_ort[0] if len(plz_ort) > 0 else ""; ort = plz_ort[1] if len(plz_ort) > 1 else ""
        
        full_positions = []
        for p in self.positionen_liste:
            p_copy = p.copy()
            p_copy.update({'Rechnungsnummer': r_nr, 'Rechnungsdatum': r_datum, 'Faelligkeitsdatum': f_datum, 'KundeName': self.entry_k_name.get(), 'KundeStrasse': self.entry_k_strasse.get(), 'KundePLZ': plz, 'KundeOrt': ort, 'KundeLand': 'DE', 'Zusatztext': '', 'KundeNr': self.entry_k_nr.get().strip(), 'Aktenzeichen': self.entry_az.get().strip(), 'LeistungszeitraumKopf': lz_kopf, 'Ratenzahlung': str(bool(self.chk_raten.get()))})
            full_positions.append(p_copy)
            
        fieldnames = ['Rechnungsnummer', 'Rechnungsdatum', 'Faelligkeitsdatum', 'KundeName', 'KundeStrasse', 'KundePLZ', 'KundeOrt', 'KundeLand', 'KundeNr', 'Aktenzeichen', 'LeistungszeitraumKopf', 'Ratenzahlung', 'PosNr', 'Menge', 'Einheit', 'Bezeichnung', 'EinzelpreisNetto', 'Steuersatz', 'Zusatztext', 'LeistungszeitraumPos']
        try:
            with open(self.p_config['rechnung_csv'], 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';'); writer.writeheader(); writer.writerows(full_positions)
                
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
            speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)
            
            if self.chk_kunde_speichern.get() and self.entry_k_name.get().strip():
                speichere_kunde(self.p_config.get("kunden_csv", "kunden.csv"), {'Name': self.entry_k_name.get().strip(), 'Strasse': self.entry_k_strasse.get().strip(), 'PLZ_Ort': self.entry_k_plz_ort.get().strip(), 'Land': 'DE', 'KundeNr': self.entry_k_nr.get().strip(), 'Aktenzeichen': self.entry_az.get().strip()})
                self.kunden_liste = lade_kunden(self.p_config.get("kunden_csv", "kunden.csv"))
                self.entry_k_name.configure(values=[k['Name'] for k in self.kunden_liste])
                
            self.p_config['letzte_rechnungsnummer'] = r_nr
            self.p_config['keep_raten'] = bool(self.chk_raten.get()); self.p_config['keep_kunde_speichern'] = bool(self.chk_kunde_speichern.get())
            speichere_config(self.config)
            if not silent: messagebox.showinfo("Erfolg", "Ihre Daten wurden erfolgreich gespeichert!")
            return True
        except Exception as e:
            messagebox.showerror("Fehler", str(e)); return False

def save_generate_open_exit(self):
        if not self.positionen_liste: return messagebox.showwarning("Fehler", "Bitte erfassen Sie Positionen!")
        valid, lz_msg = check_lz_logic({'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())}, [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste])
        if not valid: return messagebox.showwarning("Prüfung fehlgeschlagen", lz_msg)
        if not self.save_manual_invoice(silent=True): return
        
        run_auto_generation(self.config)
        
        r_nr = self.entry_r_nr.get(); akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        pdf_pfad = os.path.join(self.p_config['ausgabe_ordner'], akt_jahr, f"Rechnung_{r_nr}.pdf")
        
        if os.path.exists(pdf_pfad):
            # PDF nur öffnen, wenn --no-open nicht übergeben wurde
            if not self.config.get("cli_no_open", False):
                try: os.startfile(pdf_pfad)
                except: pass
            self.on_closing()
        else: messagebox.showerror("Fehler", "PDF konnte nicht erstellt werden (ggf. noch geöffnet?).")

class TabAuswertungenMixin:
    def build_auswertungen_tab(self):
        f = ctk.CTkFrame(self.tab_ausw); f.pack(pady=30, padx=20, fill="x")
        ctk.CTkLabel(f, text="Auswertungen generieren (Journal)", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        f_ord = ctk.CTkFrame(f, fg_color="transparent"); f_ord.pack(pady=(10, 5), fill="x", padx=10)
        ctk.CTkLabel(f_ord, text="Journal-Ordner:", width=150).pack(side="left")
        self.entry_ausw_ordner = ctk.CTkEntry(f_ord, width=300); self.entry_ausw_ordner.pack(side="left", padx=10, expand=True, fill="x")
        self.entry_ausw_ordner.insert(0, self.p_config.get("auswertungen_ordner", "Auswertungen"))
        self.create_button(f_ord, text="📂", width=40, command=lambda: self.browse_path_for_entry(self.entry_ausw_ordner, is_dir=True, on_change=self.update_ausw_jahre)).pack(side="left")
        self.entry_ausw_ordner.bind('<FocusOut>', lambda e: self.update_ausw_jahre())
        
        f_zeit = ctk.CTkFrame(f, fg_color="transparent"); f_zeit.pack(pady=5, fill="x", padx=10)
        ctk.CTkLabel(f_zeit, text="Zeitraum (Monat / Jahr):", width=150).pack(side="left")
        self.combo_ausw_monat = ctk.CTkComboBox(f_zeit, values=["Alle Monate"] + [f"{i:02d}" for i in range(1,13)], width=120)
        self.combo_ausw_monat.pack(side="left", padx=(10, 5)); self.combo_ausw_monat.set(datetime.now().strftime("%m"))
        self.combo_ausw_jahr = ctk.CTkComboBox(f_zeit, values=[], width=120); self.combo_ausw_jahr.pack(side="left", padx=5)
        
        self.create_button(f, text="Journal als PDF erzeugen & öffnen", command=self.generate_auswertung, fg_color="#b85c00", hover_color="#8f4700").pack(pady=20)
        self.update_ausw_jahre()

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
                c_obj.drawRightString(500, hoehe - 80, "Netto"); c_obj.drawRightString(580, hoehe - 80, "MwSt 19%"); c_obj.drawRightString(660, hoehe - 80, "MwSt 7%")
                c_obj.drawRightString(740, hoehe - 80, "MwSt 0%"); c_obj.drawRightString(820, hoehe - 80, "Brutto")
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

    def build_settings_tab(self):
        f_stammdaten = ctk.CTkFrame(self.tab_settings); f_stammdaten.pack(fill="x", pady=(10, 10), padx=20)
        ctk.CTkLabel(f_stammdaten, text="Stammdaten der aktiven Firma verwalten", font=("Helvetica", 14, "bold")).pack(pady=5)
        
        f_btns = ctk.CTkFrame(f_stammdaten, fg_color="transparent"); f_btns.pack(pady=10)
        self.create_button(f_btns, text="🏢 Firmendaten bearbeiten", command=self.open_firma_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=10)
        self.create_button(f_btns, text="👥 Kundendaten verwalten", command=self.open_kunden_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=10)
        self.create_button(f_btns, text="📦 Produktdaten verwalten", command=self.open_produkte_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=10)
        
        f_num_jahr = ctk.CTkFrame(self.tab_settings); f_num_jahr.pack(fill="x", pady=10, padx=20)
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

        ctk.CTkLabel(self.tab_settings, text="Dateipfade der aktiven Firma:", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.path_vars = {}
        for key in ["firma_csv", "rechnung_csv", "briefbogen_pdf", "zusatz_csv", "gruss_csv", "header_csv", "einleitung_csv", "ausgabe_ordner", "auswertungen_ordner", "kunden_csv", "produkte_csv"]:
            val = self.p_config.get(key, "")
            f = ctk.CTkFrame(self.tab_settings, fg_color="transparent"); f.pack(fill="x", pady=2, padx=20)
            ctk.CTkLabel(f, text=key, width=150, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(f, width=400); entry.insert(0, val); entry.pack(side="left", padx=10, fill="x", expand=True)
            self.path_vars[key] = entry
            self.create_button(f, text="📂", width=40, command=lambda k=key, e=entry: self.browse_path_for_entry(e, is_dir=("ordner" in k))).pack(side="left")
            
        self.create_button(self.tab_settings, text="Pfade Speichern", command=self.save_settings).pack(pady=10)

    def save_settings(self):
        for key, entry in self.path_vars.items(): self.p_config[key] = entry.get()
        speichere_config(self.config); messagebox.showinfo("Gespeichert", "Die Dateipfade wurden gespeichert!")

    def open_firma_manager(self):
        d_edit = ctk.CTkToplevel(self); d_edit.title("Firmendaten bearbeiten")
        self.center_window(d_edit, 500, 500); d_edit.transient(self); d_edit.grab_set()
        
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
        e_mail = self.create_input(d_edit, "Email"); e_mail.insert(0, f_daten.get('Email', ''))
        e_tel = self.create_input(d_edit, "Telefon"); e_tel.insert(0, f_daten.get('Telefon', ''))
        
        def save():
            name, plz, ort, iban = e_name.get().strip(), e_plz.get().strip(), e_ort.get().strip(), e_iban.get().strip()
            ustid, stnr = e_ustid.get().strip(), e_stnr.get().strip()
            if not name or not plz or not ort or not iban or (not ustid and not stnr):
                return messagebox.showwarning("Fehler", "Zwingend: Name, PLZ, Ort, IBAN, USt-Id ODER Steuernummer", parent=d_edit)
            speichere_firma(pfad_firma, {'FirmaName': name, 'Strasse': e_str.get().strip(), 'PLZ': plz, 'Ort': ort, 'Land': e_land.get().strip(), 'UStId': ustid, 'Steuernummer': stnr, 'BankName': e_bank.get().strip(), 'IBAN': iban, 'BIC': e_bic.get().strip(), 'Email': e_mail.get().strip(), 'Telefon': e_tel.get().strip()})
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
                self.entry_k_name.configure(values=[k['Name'] for k in self.kunden_liste]); refresh()

        def edit_k(index=None):
            d_edit = ctk.CTkToplevel(dialog); d_edit.title("Kunde bearbeiten" if index is not None else "Neuer Kunde")
            self.center_window(d_edit, 500, 350); d_edit.transient(dialog); d_edit.grab_set()
            
            e_name = self.create_input(d_edit, "Name"); e_str = self.create_input(d_edit, "Straße")
            e_plz = self.create_input(d_edit, "PLZ Ort"); e_nr = self.create_input(d_edit, "Kunden-Nr."); e_az = self.create_input(d_edit, "Aktenzeichen")
            
            if index is not None:
                k = self.kunden_liste[index]
                e_name.insert(0, k.get('Name','')); e_str.insert(0, k.get('Strasse',''))
                e_plz.insert(0, k.get('PLZ_Ort','')); e_nr.insert(0, k.get('KundeNr',''))
                e_az.insert(0, k.get('Aktenzeichen',''))
                
            def save():
                if not e_name.get().strip(): return messagebox.showwarning("Fehler", "Name darf nicht leer sein!", parent=d_edit)
                neu = {'Name': e_name.get().strip(), 'Strasse': e_str.get().strip(), 'PLZ_Ort': e_plz.get().strip(), 'Land': 'DE', 'KundeNr': e_nr.get().strip(), 'Aktenzeichen': e_az.get().strip()}
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
        f_split = ctk.CTkFrame(self.tab_hilfe, fg_color="transparent"); f_split.pack(fill="both", expand=True, padx=10, pady=5)
        f_toc = ctk.CTkScrollableFrame(f_split, width=220); f_toc.pack(side="left", fill="y", padx=(0, 10))
        
        hilfe_box = ctk.CTkTextbox(f_split, font=("Consolas", 13)); hilfe_box.pack(side="left", fill="both", expand=True)
        hilfe_box.insert("0.0", get_doku_text(self.current_version)); hilfe_box.configure(state="disabled")
        
        def jump_to(search_text):
            hilfe_box.configure(state="normal")
            idx = hilfe_box._textbox.search(search_text, "1.0", stopindex="end")
            if idx: hilfe_box.see(idx)
            hilfe_box.configure(state="disabled")

        ctk.CTkLabel(f_toc, text="Inhaltsverzeichnis", font=("Helvetica", 12, "bold")).pack(pady=(0, 10))
        for label, search_str in HILFE_KAPITEL:
            self.create_button(f_toc, text=label, anchor="w", fg_color="#444", hover_color="#666", command=lambda s=search_str: jump_to(s)).pack(pady=2, fill="x")


class UpdaterMixin:
    def check_for_updates(self):
        if not messagebox.askyesno("Verbindung herstellen?", "Möchten Sie jetzt die Verbindung zu GitHub für die Update-Prüfung herstellen?"): return
        self.btn_update.configure(text="⏳ Suche läuft...", state="disabled")
        if hasattr(self, 'btn_footer_update'): self.btn_footer_update.configure(text="⏳ Suche...", state="disabled")
        
        def _check():
            try:
                req = urllib.request.Request("https://api.github.com/repos/JSoko/SokoIur-eRechnung-Zugferd/releases/latest", headers={'User-Agent': 'SokoIur-Updater'})
                with urllib.request.urlopen(req) as response: data = json.loads(response.read().decode())
                
                latest_version = data.get("tag_name", "").lstrip("vV")
                assets = data.get("assets", [])
                
                if not latest_version or not assets:
                    self.after(0, lambda: [
                        self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal"),
                        (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                        messagebox.showerror("Fehler", "Keine gültigen Release-Daten gefunden.")
                    ])
                    return
                
                download_url = assets[0].get("browser_download_url")
                
                is_newer = False
                try:
                    l_v = list(map(int, latest_version.split('.')))
                    c_v = list(map(int, self.current_version.split('.')))
                    is_newer = l_v > c_v
                except: is_newer = latest_version > self.current_version
                
                if is_newer: self.after(0, lambda: self.prompt_update(latest_version, download_url))
                else:
                    self.after(0, lambda: [
                        self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal"),
                        (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                        messagebox.showinfo("Update-Prüfung", f"Sie nutzen bereits die aktuellste Version!\n\nIhre: {self.current_version}\nOnline: {latest_version}")
                    ])
            except Exception as e:
                self.after(0, lambda: [
                    self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal"),
                    (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                    messagebox.showerror("Fehler", f"Fehler bei der Update-Prüfung:\n{str(e)}")
                ])
        threading.Thread(target=_check, daemon=True).start()

    def prompt_update(self, latest_version, download_url):
        self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal")
        if hasattr(self, 'btn_footer_update'): self.btn_footer_update.configure(text="Update?", state="normal")
        if messagebox.askyesno("Update verfügbar!", f"Version {latest_version} ist verfügbar!\nMöchten Sie diese jetzt herunterladen und installieren?"):
            self.download_and_install_update(download_url)

    def download_and_install_update(self, download_url):
        dl_win = ctk.CTkToplevel(self); dl_win.title("Update")
        self.center_window(dl_win, 300, 150); dl_win.transient(self); dl_win.grab_set()
        ctk.CTkLabel(dl_win, text="Lade Update herunter...\nBitte warten.", font=("Helvetica", 14)).pack(expand=True); self.update()
        
        def _download():
            try:
                new_exe = "SokoIur_eRechnung_neu.exe"
                urllib.request.urlretrieve(download_url, new_exe)
                
                if not getattr(sys, 'frozen', False):
                    self.after(0, lambda: [dl_win.destroy(), messagebox.showinfo("Info", "Update im Skript-Modus geladen.")])
                    return
                
                current_exe = sys.executable
                with open("update.bat", "w") as f:
                    f.write(f'@echo off\ntimeout /t 3 /nobreak > NUL\nmove /Y "{new_exe}" "{current_exe}"\nstart "" "{current_exe}"\ndel "%~f0"\n')
                subprocess.Popen("update.bat", shell=True)
                self.after(0, self.do_update_exit) 
            except Exception as e:
                self.after(0, lambda: [dl_win.destroy(), messagebox.showerror("Fehler", f"Download fehlgeschlagen:\n{str(e)}")])
        threading.Thread(target=_download, daemon=True).start()

    def do_update_exit(self):
        try: os.remove(LOCK_FILE)
        except: pass
        os._exit(0)
