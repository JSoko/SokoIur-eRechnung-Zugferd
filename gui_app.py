import customtkinter as ctk
import tkinter.messagebox as messagebox
import os
import sys
from datetime import datetime, timedelta
import webbrowser

from datenbank import speichere_config, get_resource_path, LOCK_FILE, berechne_naechste_rechnungsnummer
from gui_module import TabManuellMixin, TabAuswertungenMixin, TabEinstellungenMixin, TabHilfeMixin, UpdaterMixin

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk, TabManuellMixin, TabAuswertungenMixin, TabEinstellungenMixin, TabHilfeMixin, UpdaterMixin):
    def __init__(self, config, start_in_edit=False):
        super().__init__()
        self.config = config
        self.title("SokoIur eRechnung")
        
        if getattr(sys, 'frozen', False):
            exe_zeit = os.path.getmtime(sys.executable)
            kompilierungs_datum = datetime.fromtimestamp(exe_zeit)
        else:
            kompilierungs_datum = datetime.now()
            
        yy = kompilierungs_datum.strftime('%y')
        tag_des_jahres = kompilierungs_datum.timetuple().tm_yday
        minute_des_tages = kompilierungs_datum.hour * 60 + kompilierungs_datum.minute
        
        self.current_version = f"1.{yy}{tag_des_jahres:03d}{minute_des_tages:04d}"
        
        icon_path = get_resource_path("SokoIur.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except Exception: pass
                
        self.geometry(self.config.get("window_geometry", "950x850"))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.bind('<plus>', self.handle_plus_key)
        self.bind('<KP_Add>', self.handle_plus_key)
        self.bind('<Alt-l>', lambda e: self.load_manual_invoice(is_button_click=True))
        self.bind('<Alt-L>', lambda e: self.load_manual_invoice(is_button_click=True))
        self.bind('<Alt-t>', lambda e: self.open_texte_popup())
        self.bind('<Alt-T>', lambda e: self.open_texte_popup())
        self.bind('<Alt-s>', lambda e: self.save_manual_invoice())
        self.bind('<Alt-S>', lambda e: self.save_manual_invoice())
        self.bind('<Alt-p>', lambda e: self.save_generate_open_exit())
        self.bind('<Alt-P>', lambda e: self.save_generate_open_exit())
        
        self.header_container = ctk.CTkFrame(self, fg_color="transparent")
        self.header_container.pack(fill="x", padx=20, pady=(10, 0))
        
        self.build_profile_header()
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=(10, 5), fill="both", expand=True)
        
        self.tab_manuell = self.tabview.add("Manuelle Eingabe")
        self.tab_ausw = self.tabview.add("Auswertungen")
        self.tab_settings = self.tabview.add("Einstellungen")
        self.tab_hilfe = self.tabview.add("Hilfe & Doku")
        
        self.refresh_all_ui()
        self.tabview.set("Manuelle Eingabe")

        if start_in_edit:
            self.after(200, lambda: self.load_manual_invoice(is_button_click=False, silent=True))
            
        f_footer = ctk.CTkFrame(self, fg_color="transparent")
        f_footer.pack(side="bottom", fill="x", padx=20, pady=5)
        
        lbl_footer_l = ctk.CTkLabel(f_footer, text="(C) Joachim Sokolowski", text_color="#1f538d", cursor="hand2")
        lbl_footer_l.pack(side="left")
        lbl_footer_l.bind("<Button-1>", lambda e: webbrowser.open("https://sokolowski.org"))
        
        lbl_footer_c = ctk.CTkLabel(f_footer, text=f"| Version: {self.current_version}")
        lbl_footer_c.pack(side="left", padx=10)
        
        self.btn_footer_update = ctk.CTkButton(f_footer, text="Update?", width=80, fg_color="#555", hover_color="#777", command=self.check_for_updates)
        self.btn_footer_update.pack(side="right")

    @property
    def p_config(self):
        return self.config["profiles"][self.config["active_profile_index"]]

    def build_profile_header(self):
        for w in self.header_container.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.header_container, text="Aktive Firma / Profil:", font=("Helvetica", 14, "bold")).pack(side="left")
        
        profil_namen = [p["profil_name"] for p in self.config["profiles"]]
        self.combo_profile = ctk.CTkComboBox(self.header_container, values=profil_namen, command=self.on_profile_switch)
        self.combo_profile.set(self.p_config["profil_name"])
        self.combo_profile.pack(side="left", padx=10)
        
        self.create_button(self.header_container, text="+ Neu", width=60, command=self.add_profile).pack(side="left", padx=5)
        self.create_button(self.header_container, text="✎ Umbenennen", width=100, command=self.rename_profile).pack(side="left", padx=5)
        
        if len(self.config["profiles"]) > 1:
            self.create_button(self.header_container, text="🗑 Löschen", width=80, fg_color="#b30000", hover_color="#800000", command=self.delete_profile).pack(side="left", padx=5)

    def on_profile_switch(self, wahl):
        for i, p in enumerate(self.config["profiles"]):
            if p["profil_name"] == wahl:
                self.config["active_profile_index"] = i
                speichere_config(self.config)
                self.refresh_all_ui()
                break

    def add_profile(self):
        from datenbank import get_default_profile, create_csv_if_missing
        import time
        if len(self.config["profiles"]) >= 5: return messagebox.showwarning("Limit erreicht", "Maximal 5 Profile.")
        d_name = ctk.CTkInputDialog(text="Name der neuen Firma:", title="Neues Profil")
        name = d_name.get_input()
        if name:
            new_p = get_default_profile(str(int(time.time()))[-5:])
            new_p["profil_name"] = name
            os.makedirs(new_p["ausgabe_ordner"], exist_ok=True); os.makedirs(new_p["auswertungen_ordner"], exist_ok=True)
            create_csv_if_missing(new_p["firma_csv"], "FirmaName;Strasse;PLZ;Ort;Land;UStId;Steuernummer;BankName;IBAN;BIC;Email;Telefon")
            create_csv_if_missing(new_p["rechnung_csv"], "Rechnungsnummer;Rechnungsdatum;Faelligkeitsdatum;KundeName;KundeStrasse;KundePLZ;KundeOrt;KundeLand;KundeNr;Aktenzeichen;LeistungszeitraumKopf;Ratenzahlung;PosNr;Menge;Einheit;Bezeichnung;EinzelpreisNetto;Steuersatz;Zusatztext;LeistungszeitraumPos")
            create_csv_if_missing(new_p["kunden_csv"], "Name;Strasse;PLZ_Ort;Land;KundeNr;Aktenzeichen")
            create_csv_if_missing(new_p["produkte_csv"], "Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz")
            for f in ["zusatz_csv", "gruss_csv", "header_csv", "einleitung_csv"]: create_csv_if_missing(new_p[f], "")
            self.config["profiles"].append(new_p); self.config["active_profile_index"] = len(self.config["profiles"]) - 1
            speichere_config(self.config); self.build_profile_header(); self.refresh_all_ui()

    def rename_profile(self):
        d_name = ctk.CTkInputDialog(text="Neuer Name für das Profil:", title="Profil umbenennen")
        name = d_name.get_input()
        if name:
            self.p_config["profil_name"] = name; speichere_config(self.config); self.build_profile_header()

    def delete_profile(self):
        if len(self.config["profiles"]) <= 1: return messagebox.showwarning("Fehler", "Letztes Profil kann nicht gelöscht werden.")
        pwd = ctk.CTkInputDialog(text="Bitte geben Sie das Sicherheitspasswort ein, um die Firma zu löschen:", title="Sicherheitsabfrage").get_input()
        if pwd == "63263":
            del self.config["profiles"][self.config["active_profile_index"]]
            self.config["active_profile_index"] = 0
            speichere_config(self.config); self.build_profile_header(); self.refresh_all_ui()
            messagebox.showinfo("Gelöscht", "Die Firma wurde entfernt.")
        elif pwd is not None: messagebox.showerror("Fehler", "Falsches Passwort!")

    def refresh_all_ui(self):
        from datenbank import lade_kunden, lade_produkte, lade_textdatei
        self.kunden_liste = lade_kunden(self.p_config.get("kunden_csv", "kunden.csv"))
        self.produkte_liste = lade_produkte(self.p_config.get("produkte_csv", "produkte.csv"))
        self.header_text = lade_textdatei(self.p_config.get('header_csv', ''))
        self.einleitung_text = lade_textdatei(self.p_config.get('einleitung_csv', ''))
        self.gruss_text = lade_textdatei(self.p_config.get('gruss_csv', ''))
        self.positionen_liste = []; self.zusatz_dict = {}

        for w in self.tab_manuell.winfo_children() + self.tab_ausw.winfo_children() + self.tab_settings.winfo_children() + self.tab_hilfe.winfo_children(): w.destroy()

        self.build_manuell_tab(); self.build_auswertungen_tab(); self.build_settings_tab(); self.build_hilfe_tab()
        
        heute = datetime.now()
        tage = int(self.p_config.get("faelligkeit_tage", "29")) if str(self.p_config.get("faelligkeit_tage", "29")).isdigit() else 29
        self.entry_r_datum.delete(0, 'end'); self.entry_r_datum.insert(0, heute.strftime('%Y-%m-%d'))
        self.entry_f_datum.delete(0, 'end'); self.entry_f_datum.insert(0, (heute + timedelta(days=tage)).strftime('%Y-%m-%d'))
        self.entry_r_nr.delete(0, 'end'); self.entry_r_nr.insert(0, berechne_naechste_rechnungsnummer(self.p_config.get("letzte_rechnungsnummer", "")))

    def on_closing(self):
        self.config["window_geometry"] = self.geometry()
        speichere_config(self.config)
        try: os.remove(LOCK_FILE)
        except: pass
        self.destroy()

    def center_window(self, dialog, width, height):
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def handle_plus_key(self, event):
        if self.tabview.get() == "Manuelle Eingabe":
            widget = self.focus_get()
            if widget and widget.winfo_class() in ('Entry', 'Text'): return
            self.open_pos_popup()

    def create_button(self, parent, text, command, **kwargs):
        btn = ctk.CTkButton(parent, text=text, command=command, **kwargs)
        btn.bind('<Return>', lambda e: command()); btn.bind('<space>', lambda e: command())
        return btn

    def create_input(self, parent, label_text, is_combo=False, combo_values=None, command=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
        entry = ctk.CTkComboBox(frame, values=combo_values or [], command=command) if is_combo else ctk.CTkEntry(frame)
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        return entry
        
    def create_input_with_button(self, parent, label_text, btn_text, btn_cmd):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame); entry.pack(side="left", fill="x", expand=True, padx=(10, 5))
        self.create_button(frame, text=btn_text, width=40, command=lambda: btn_cmd(entry)).pack(side="right")
        return entry
