"""
tab_verwaltung.py
-----------------
Popup-Logik für die Stammdatenverwaltung (Kunden & Produkte).
"""
import customtkinter as ctk
from tkinter import ttk
import tkinter.messagebox as messagebox
from config import *
from utils import *
from crud import speichere_kunde, loesche_kunde, speichere_produkt, loesche_produkt

class TabVerwaltungMixin:
    def open_verwaltung_popup(self):
        self.vw_popup = ctk.CTkToplevel(self)
        self.vw_popup.title("👥 Kunden & Artikel verwalten")
        
        # Zentriert das Popup exakt über dem Hauptfenster der App
        self.center_window(self.vw_popup, 850, 550) 
        
        self.vw_popup.transient(self)
        self.vw_popup.grab_set()
        
        self.vw_mode = ctk.StringVar(value="Kunden")
        
        f_top = ctk.CTkFrame(self.vw_popup, fg_color="transparent")
        f_top.pack(fill="x", pady=(10, 10))
        
        self.seg_btn = ctk.CTkSegmentedButton(f_top, values=["Kunden", "Produkte"], variable=self.vw_mode, command=self.vw_switch_mode)
        self.seg_btn.pack(pady=5)
        
        f_main = ctk.CTkFrame(self.vw_popup, fg_color="transparent")
        f_main.pack(fill="both", expand=True)
        
        f_left = ctk.CTkFrame(f_main, width=280)
        f_left.pack(side="left", fill="y", padx=(10, 10))
        f_left.pack_propagate(False)
        
        self.f_right = ctk.CTkFrame(f_main)
        self.f_right.pack(side="right", fill="both", expand=True, padx=(0, 10))
        
        self.vw_search_var = ctk.StringVar()
        self.vw_search_var.trace("w", lambda name, index, mode: self.vw_refresh_list())
        ctk.CTkEntry(f_left, textvariable=self.vw_search_var, placeholder_text="🔍 Suchen...").pack(fill="x", padx=10, pady=10)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        
        self.vw_tree = ttk.Treeview(f_left, columns=("Name",), show="headings")
        self.vw_tree.heading("Name", text="Eintrag")
        self.vw_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.vw_tree.bind("<<TreeviewSelect>>", self.vw_on_select)
        
        self.vw_form_frame = ctk.CTkScrollableFrame(self.f_right, fg_color="transparent")
        self.vw_form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        f_actions = ctk.CTkFrame(self.f_right, fg_color="transparent")
        f_actions.pack(fill="x", side="bottom", padx=10, pady=10)
        
        ctk.CTkButton(f_actions, text="➕ Neu", width=80, command=self.vw_clear_form).pack(side="left", padx=5)
        ctk.CTkButton(f_actions, text="💾 Speichern", width=120, command=self.vw_save_entry).pack(side="left", padx=5)
        ctk.CTkButton(f_actions, text="🗑️ Löschen", width=80, fg_color="#b30000", hover_color="#800000", command=self.vw_delete_entry).pack(side="right", padx=5)
        
        self.vw_entries = {}
        self.vw_switch_mode("Kunden")
        
    def vw_switch_mode(self, mode):
        self.vw_search_var.set("")
        self.vw_clear_form()
        for widget in self.vw_form_frame.winfo_children(): widget.destroy()
        self.vw_entries.clear()
        
        if mode == "Kunden": 
            fields = ['Name', 'Strasse', 'PLZ_Ort', 'Land', 'KundeNr', 'Aktenzeichen', 'KundeAktenzeichen', 'Endpoint', 'EndpointScheme']
            for field in fields: 
                self.vw_entries[field] = self.create_input(self.vw_form_frame, field + ":")
        else: 
            # Produkte: Menge wird ausgeblendet, Einheit und Steuersatz werden Dropdowns
            self.vw_entries['Bezeichnung'] = self.create_input(self.vw_form_frame, "Bezeichnung:")
            self.vw_entries['Einheit'] = self.create_input(self.vw_form_frame, "Einheit:", is_combo=True, combo_values=EINHEITEN_LISTE)
            self.vw_entries['EinzelpreisNetto'] = self.create_input(self.vw_form_frame, "Einzelpreis Netto:")
            self.vw_entries['Steuersatz'] = self.create_input(self.vw_form_frame, "Steuersatz (%):", is_combo=True, combo_values=["19", "7", "0"])
            
        self.vw_refresh_list()
        
    def vw_refresh_list(self):
        for item in self.vw_tree.get_children(): self.vw_tree.delete(item)
        search_q = self.vw_search_var.get().lower()
        mode = self.vw_mode.get()
        data = self.kunden_liste if mode == "Kunden" else self.produkte_liste
        key = "Name" if mode == "Kunden" else "Bezeichnung"
        
        for record in data:
            val = record.get(key, "")
            if search_q in val.lower(): self.vw_tree.insert("", "end", values=(val,), tags=(val,))
                
    def vw_on_select(self, event):
        selected = self.vw_tree.selection()
        if not selected: return
        val = self.vw_tree.item(selected[0])['values'][0]
        mode = self.vw_mode.get()
        data = self.kunden_liste if mode == "Kunden" else self.produkte_liste
        key = "Name" if mode == "Kunden" else "Bezeichnung"
        
        self.vw_clear_form()
        for record in data:
            if record.get(key, "") == val:
                for k, entry in self.vw_entries.items(): 
                    rec_val = record.get(k, "")
                    # ComboBoxen benötigen .set(), normale Textfelder .insert()
                    if isinstance(entry, ctk.CTkComboBox):
                        entry.set(rec_val)
                    else:
                        entry.insert(0, rec_val)
                break
                
    def vw_clear_form(self):
        for entry in self.vw_entries.values(): 
            if isinstance(entry, ctk.CTkComboBox):
                entry.set("")
            else:
                entry.delete(0, 'end')
    
    def vw_save_entry(self):
        mode = self.vw_mode.get()
        primary_key = "Name" if mode == "Kunden" else "Bezeichnung"
        
        if not self.vw_entries[primary_key].get().strip(): 
            return messagebox.showwarning("Fehler", f"Das Feld '{primary_key}' darf nicht leer sein.", parent=self.vw_popup)
            
        new_data = {k: entry.get().strip() for k, entry in self.vw_entries.items()}
        
        if mode == "Kunden": 
            speichere_kunde(self.p_config.get("kunden_csv"), new_data)
        else: 
            # Menge hart auf "1" setzen, damit die Produkte-CSV nicht beschädigt wird
            new_data['Menge'] = "1"
            speichere_produkt(self.p_config.get("produkte_csv"), new_data)
            
        self.refresh_all_ui()
        # NEU: Alertbox entfernt - stattdessen die sichtbare Tabelle sofort aktualisieren
        self.vw_refresh_list() 
        
    def vw_delete_entry(self):
        mode = self.vw_mode.get()
        primary_key = "Name" if mode == "Kunden" else "Bezeichnung"
        val = self.vw_entries[primary_key].get().strip()
        
        if not val: 
            return
        
        if messagebox.askyesno("Löschen", f"Soll '{val}' wirklich gelöscht werden?", parent=self.vw_popup):
            if mode == "Kunden": 
                loesche_kunde(self.p_config.get("kunden_csv"), val)
            else: 
                loesche_produkt(self.p_config.get("produkte_csv"), val)
                
            self.refresh_all_ui()
            self.vw_clear_form()
            # NEU: Gelöschten Eintrag sofort aus der sichtbaren Tabelle entfernen
            self.vw_refresh_list()
            
