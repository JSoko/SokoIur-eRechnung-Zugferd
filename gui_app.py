"""
gui_app.py
----------
Hauptklasse und Fensterverwaltung für die grafische Benutzeroberfläche (GUI).
Dieses Modul definiert die zentrale `App`-Klasse der SokoIur eRechnung basierend auf 
CustomTkinter[cite: 4]. Es übernimmt die Initialisierung des Hauptfensters, das Routing 
der Tastenkürzel und den Aufbau der Basis-UI (Header mit Profilwahl, Tab-Navigation 
und Footer mit Versionsanzeige)[cite: 4]. Die fachliche Logik und die Inhalte der 
einzelnen Reiter (Tabs) werden strukturiert über Mixin-Klassen aus dem `gui_module` 
eingebunden[cite: 4, 5]. Zudem steuert dieses Modul das wichtige Lock-Management 
(Sperrdateien) beim netzwerkbasierten Betrieb, um Datenverlust durch gleichzeitige 
Bearbeitung derselben Firma zu verhindern[cite: 4].
"""
import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog  # <--- Diese Zeile muss hinzugefügt werden
import os
import sys
from datetime import datetime, timedelta
import webbrowser

from datenbank import speichere_config, get_resource_path, LOCK_FILE, berechne_naechste_rechnungsnummer
from gui_module import TabManuellMixin, TabErfassenMixin, TabAuswertungenMixin, TabEinstellungenMixin, TabHilfeMixin, UpdaterMixin

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk, TabManuellMixin, TabErfassenMixin, TabAuswertungenMixin, TabEinstellungenMixin, TabHilfeMixin, UpdaterMixin):

    def get_firm_lock_path(self, lock_name="erechnung.lock"):
        base_path = self.config.get("base_data_path")
        if not base_path: return None
        firm_dir = os.path.join(base_path, self.p_config["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir): os.makedirs(firm_dir, exist_ok=True)
        return os.path.join(firm_dir, lock_name)
    
    def set_firm_lock(self, lock_name="erechnung.lock"):
        lock_file = self.get_firm_lock_path(lock_name)
        if not lock_file: return
        if not hasattr(self, 'current_lock_files'): self.current_lock_files = {}
        try:
            with open(lock_file, "w") as f: f.write(str(os.getpid()))
            self.current_lock_files[lock_name] = lock_file
        except: pass
    
    def unlock_firm(self, lock_name=None):
        if not hasattr(self, 'current_lock_files'): self.current_lock_files = {}
        locks_to_remove = [lock_name] if lock_name else list(self.current_lock_files.keys())
            
        for lname in locks_to_remove:
            lfile = self.current_lock_files.get(lname)
            if lfile and os.path.exists(lfile):
                try: os.remove(lfile)
                except: pass
            self.current_lock_files[lname] = None

    def lock_firm(self, p_dict, lock_name="erechnung.lock"):
        base_path = self.config.get("base_data_path")
        if not base_path: return True
        firm_dir = os.path.join(base_path, p_dict["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir): os.makedirs(firm_dir, exist_ok=True)
        
        lock_file = os.path.join(firm_dir, lock_name)
        if not hasattr(self, 'current_lock_files'): self.current_lock_files = {}
        
        if self.current_lock_files.get(lock_name) == lock_file:
            return True

        if os.path.exists(lock_file):
            try:
                file_age = time.time() - os.path.getmtime(lock_file)
                if file_age > 43200:
                    os.remove(lock_file)
                else:
                    messagebox.showwarning("Firma gesperrt", f"Die Firma '{p_dict['profil_name']}' wird aktuell bearbeitet ({lock_name}).")
                    return False
            except: return False
            
        try:
            with open(lock_file, "w") as f: f.write(str(os.getpid()))
            self.current_lock_files[lock_name] = lock_file
            return True
        except: return True

    def check_and_handle_lock(self, target_tab, lock_name="erechnung.lock"):
        base_path = self.config.get("base_data_path")
        if not base_path: return True
        firm_dir = os.path.join(base_path, self.p_config["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir): os.makedirs(firm_dir, exist_ok=True)
        lock_file = os.path.join(firm_dir, lock_name)

        if not hasattr(self, 'current_lock_files'): self.current_lock_files = {}
        if self.current_lock_files.get(lock_name) == lock_file:
            return True

        while os.path.exists(lock_file):
            try:
                with open(lock_file, "r") as f: content = f.read().strip()
                if content == str(os.getpid()):
                    self.current_lock_files[lock_name] = lock_file
                    return True
            except: pass

            dlg = ctk.CTkToplevel(self)
            dlg.title("Firma gesperrt")
            self.center_window(dlg, 450, 200)
            dlg.transient(self); dlg.grab_set()

            modul = "Rechnungserfassung" if lock_name == "erfassung.lock" else "Rechnungserstellung"
            ctk.CTkLabel(dlg, text=f"Die Firma '{self.p_config['profil_name']}' wird aktuell\nim Bereich {modul} bearbeitet.", font=("Helvetica", 13, "bold"), justify="center").pack(pady=20)

            f_btn = ctk.CTkFrame(dlg, fg_color="transparent")
            f_btn.pack(pady=10)

            result = {"action": None}

            def do_retry():
                result["action"] = "retry"; dlg.destroy()
            def do_force_unlock():
                if messagebox.askyesno("Sicherheitswarnung", f"Soll der Lock ({lock_name}) wirklich entfernt werden?\n\nEs droht Datenverlust!", parent=dlg, default="no"):
                    result["action"] = "force"; dlg.destroy()

            self.create_button(f_btn, text="Erneut prüfen", width=120, command=do_retry).pack(side="left", padx=5)
            self.create_button(f_btn, text="Lock entfernen", width=120, fg_color="#b30000", hover_color="#800000", command=do_force_unlock).pack(side="left", padx=5)
            self.wait_window(dlg)

            if result["action"] == "retry": continue
            elif result["action"] == "force":
                try: os.remove(lock_file)
                except: pass
                break
            else: return False
        return True
    
    def on_tab_change(self):
        if getattr(self, '_initializing', False): return  
        selected_tab = self.tabview.get()
        
        if selected_tab == "📝 ERSTELLEN":
            if not self.check_and_handle_lock(selected_tab, "erechnung.lock"):
                self.tabview.set("ℹ️ Info")
                return
            self.lock_firm(self.p_config, "erechnung.lock")
            self.unlock_firm("erfassung.lock")
            
        elif selected_tab == "📥 ERFASSEN":
            if not self.check_and_handle_lock(selected_tab, "erfassung.lock"):
                self.tabview.set("ℹ️ Info")
                return
            self.lock_firm(self.p_config, "erfassung.lock")
            self.unlock_firm("erechnung.lock")
            
        elif selected_tab == "⚙️ Einst.":
            if not self.check_and_handle_lock(selected_tab, "erechnung.lock") or not self.check_and_handle_lock(selected_tab, "erfassung.lock"):
                self.tabview.set("ℹ️ Info")
                return
            self.lock_firm(self.p_config, "erechnung.lock")
            self.lock_firm(self.p_config, "erfassung.lock")
            
        else:
            self.unlock_firm()
        
    def __init__(self, config, start_in_edit=False):
        super().__init__()
        self.config = config
        self._initializing = True  # Verhindert zu frühes Auslösen beim Start
        self.title("SokoIur eRechnung")
        
        # 1. Versionsnummer aus der .exe auslesen
        from datenbank import get_app_version
        self.current_version = get_app_version()
        
        # 2. Fenster-Setup & Tastenkürzel
        icon_path = get_resource_path("SokoIur.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except Exception: pass
                
        self.geometry(self.config.get("window_geometry", "950x850"))
        self.minsize(650, 850)  # <-- NEU: Verhindert, dass das Fenster kleiner als 950x750 Pixel gezogen wird
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
        self.bind('<Alt-e>', lambda e: self.tabview.set("📝 ERSTELLEN"))
        self.bind('<Alt-E>', lambda e: self.tabview.set("📝 ERSTELLEN"))
        self.bind('<Alt-a>', lambda e: self.tabview.set("📊 AUSGANG"))
        self.bind('<Alt-A>', lambda e: self.tabview.set("📊 AUSGANG"))
        self.bind('<Alt-f>', lambda e: self.tabview.set("📥 ERFASSEN"))
        self.bind('<Alt-F>', lambda e: self.tabview.set("📥 ERFASSEN"))
        self.bind('<Alt-i>', lambda e: self.tabview.set("📊 EINGANG"))
        self.bind('<Alt-I>', lambda e: self.tabview.set("📊 EINGANG"))
        self.bind('<F1>', lambda e: self.tabview.set("ℹ️ Info"))
        
        self.header_container = ctk.CTkFrame(self, fg_color="transparent")
        self.header_container.pack(fill="x", padx=20, pady=(10, 0))
        
        self.build_profile_header()
        
        self.tabview = ctk.CTkTabview(self) 
        self.tabview.pack(padx=20, pady=(10, 5), fill="both", expand=True)
        
        self.tab_manuell = self.tabview.add("📝 ERSTELLEN")
        self.tab_erfassen = self.tabview.add("📥 ERFASSEN")
        self.tab_ausgang = self.tabview.add("📊 AUSGANG")
        self.tab_eingang = self.tabview.add("📊 EINGANG")
        self.tab_settings = self.tabview.add("⚙️ Einst.")
        self.tab_hilfe = self.tabview.add("ℹ️ Info")
        
        self.tabview.set("📝 ERSTELLEN")

        # 3. DATENSPEICHERORT PRÜFEN & ORDNER SETUP
        if not self.config.get("base_data_path"):
            new_path = self.ask_for_base_path("Zentralen Datenspeicherort festlegen")
            if not new_path:
                sys.exit(0)
            self.config["base_data_path"] = new_path
            
            # --- NEU: Synchronisation beim allerersten Start ---
            # Wenn bereits Firmen im ausgewählten Netzwerklaufwerk existieren, diese sofort einbinden
            shared_config_path = os.path.join(new_path, "shared_firms.json")
            firmen_gefunden = False
            if os.path.exists(shared_config_path):
                import json
                try:
                    with open(shared_config_path, 'r', encoding='utf-8') as f:
                        net_profiles = json.load(f)
                        if net_profiles:
                            self.config["profiles"] = net_profiles
                            self.config["active_profile_index"] = 0
                            self.build_profile_header()
                            firmen_gefunden = True
                            
                            # HIER WURDE DIE IMPORT-ZEILE ENTFERNT!
                            messagebox.showinfo(
                                "Netzwerk-Daten gefunden", 
                                f"Es wurden {len(net_profiles)} bereits bestehende Firmen im Netzwerklaufwerk gefunden und in Ihre lokale Ansicht übernommen!"
                            )
                except: pass
            
            # Setup nur mit Meldung, falls nicht ohnehin schon Firmen gefunden wurden
            self.setup_firm_folders(self.p_config, show_message=not firmen_gefunden)
            speichere_config(self.config)
        else:
            # BEIM NORMALEN START: Leises Setup ohne Meldung!
            self.setup_firm_folders(self.p_config)

        # 4. Netzwerk-Version erzwingen
        if not self.enforce_network_version():
            return
        
        # 5. Lock-Prüfung beim Programmstart
        lock_file = self.get_firm_lock_path()
        if lock_file and os.path.exists(lock_file):
            is_other_process = True
            try:
                with open(lock_file, "r") as f:
                    content = f.read().strip()
                if content == str(os.getpid()):
                    is_other_process = False
            except:
                pass

            if is_other_process:
                messagebox.showerror(
                    "Programmstart verweigert", 
                    f"Die Firma '{self.p_config['profil_name']}' ist bereits auf diesem oder einem anderen Rechner in Bearbeitung (Lock aktiv).\n\n"
                    "Das Programm wird zum Schutz vor Datenkonflikten beendet."
                )
                sys.exit(0)

        # 6. Start-Firma als aktiv sperren und UI aufbauen
        self.set_firm_lock()
        self.refresh_all_ui()
        
        self.tabview.set("📝 ERSTELLEN")
        
        # Initialisierung abgeschlossen - Überwachung jetzt aktivieren
        self._initializing = False
        self.tabview.configure(command=self.on_tab_change)

        if start_in_edit:
            self.after(200, lambda: self.load_manual_invoice(is_button_click=False, silent=True))
            
        # 7. Footer aufbauen
        f_footer = ctk.CTkFrame(self, fg_color="transparent")
        f_footer.pack(side="bottom", fill="x", padx=20, pady=5)
        
        lbl_footer_l = ctk.CTkLabel(f_footer, text="(C) Joachim Sokolowski", text_color="#1f538d", cursor="hand2")
        lbl_footer_l.pack(side="left")
        lbl_footer_l.bind("<Button-1>", lambda e: webbrowser.open("https://sokolowski.org"))
        
        lbl_footer_c = ctk.CTkLabel(f_footer, text=f"| Version: {self.current_version}")
        lbl_footer_c.pack(side="left", padx=10)
        self.btn_footer_exit = ctk.CTkButton(f_footer, text="Beenden", width=80, fg_color="#b30000", hover_color="#800000", command=self.on_closing)
        self.btn_footer_exit.pack(side="right", padx=(5, 0))

        self.btn_footer_hilfe = ctk.CTkButton(f_footer, text="Hilfe", width=80, fg_color="#1f538d", hover_color="#14375d", command=self.open_html_help)
        self.btn_footer_hilfe.pack(side="right", padx=5)

        self.btn_footer_update = ctk.CTkButton(f_footer, text="Update?", width=80, fg_color="#555", hover_color="#777", command=self.check_for_updates)
        self.btn_footer_update.pack(side="right")
    
    @property
    def p_config(self):
        return self.config["profiles"][self.config["active_profile_index"]]

    def ask_for_base_path(self, title_text):
        program_dir = os.path.abspath(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__))
        while True:
            messagebox.showinfo(
                "Datenspeicherort wählen", 
                f"{title_text}\n\nBitte wählen Sie einen Ordner für die Datenspeicherung.\n\n"
                "WICHTIG: Der Ordner darf NICHT im oder unterhalb des Programmverzeichnisses liegen! "
                "Bei der Nutzung von mehreren Rechnern aus sollte zwingend ein freigegebenes Netzwerklaufwerk gewählt werden."
            )
            path = filedialog.askdirectory(title="Daten-Grundpfad wählen")
            if not path:
                if messagebox.askyesno("Abbruch", "Ohne Datenspeicherort kann die Firma nicht eingerichtet werden. Möchten Sie abbrechen?"):
                    return None
                continue
            
            path_abs = os.path.abspath(path)
            try:
                common = os.path.commonpath([program_dir, path_abs])
                if common == program_dir:
                    messagebox.showwarning("Ungültiger Pfad", f"Der gewählte Pfad liegt innerhalb des Programmordners:\n{program_dir}\n\nBitte wählen Sie einen anderen Ort (z. B. auf einem Netzwerklaufwerk).")
                    continue
            except ValueError:
                # Unterschiedliche Laufwerke (z.B. C: und Z:) lösen einen ValueError aus = Gültig und sicher!
                pass
            
            return path_abs

    def setup_firm_folders(self, p_dict, show_message=False):
        base_path = self.config.get("base_data_path")
        
        # SICHERHEITSABFRAGE: Wenn noch kein Pfad existiert, sofort abbrechen!
        if not base_path:
            return
            
        firm_folder = p_dict["profil_name"].replace(" ", "_")
        firm_dir = os.path.join(base_path, firm_folder)
        ausw_dir = os.path.join(firm_dir, "ausw")
        are_dir = os.path.join(firm_dir, "are")
        reneu_dir = os.path.join(firm_dir, "reneu")
        rebearb_dir = os.path.join(firm_dir, "rebearb")
        rchn_dir = os.path.join(firm_dir, "rchn")
        einj_dir = os.path.join(firm_dir, "einj")
        
        already_exists = os.path.exists(firm_dir) and os.path.exists(os.path.join(firm_dir, "firma.csv"))
        
        os.makedirs(ausw_dir, exist_ok=True)
        os.makedirs(are_dir, exist_ok=True)
        for _d in (reneu_dir, rebearb_dir, rchn_dir, einj_dir): os.makedirs(_d, exist_ok=True)
        
        p_dict["auswertungen_ordner"] = ausw_dir
        p_dict["ausgabe_ordner"] = are_dir
        p_dict["eingangsordner"] = reneu_dir
        p_dict["bearbeitete_eingangsrechnungen_ordner"] = rebearb_dir
        p_dict["eingangsrechnungen_ordner"] = rchn_dir
        p_dict["eingangsjournal_ordner"] = einj_dir
        
        dateien = ["firma.csv", "rechnung.csv", "briefbogen.pdf", "zusatz.csv", "gruss.csv", "header.csv", "einleitung.csv", "kunden.csv", "produkte.csv"]
        for datei in dateien:
            key_name = datei.replace(".", "_")
            p_dict[key_name] = os.path.join(firm_dir, datei)
            
        if already_exists:
            if show_message:
                messagebox.showinfo("Netzwerk-Daten gefunden", f"Es wurden bestehende Daten für '{p_dict['profil_name']}' gefunden und erfolgreich verknüpft!")
        else:
            from datenbank import create_csv_if_missing
            create_csv_if_missing(p_dict["firma_csv"], "FirmaName;Strasse;PLZ;Ort;Land;UStId;Steuernummer;BankName;IBAN;BIC;Kontoinhaber;Email;Telefon")
            create_csv_if_missing(p_dict["rechnung_csv"], "Rechnungsnummer;Rechnungsdatum;Faelligkeitsdatum;KundeName;KundeStrasse;KundePLZ;KundeOrt;KundeLand;KundeEmail;KundeEndpoint;KundeEndpointScheme;KundeNr;Aktenzeichen;KundeAktenzeichen;LeistungszeitraumKopf;Ratenzahlung;PosNr;Menge;Einheit;Bezeichnung;EinzelpreisNetto;Steuersatz;Zusatztext;LeistungszeitraumPos")
            create_csv_if_missing(p_dict["kunden_csv"], "Name;Strasse;PLZ_Ort;Land;KundeNr;Aktenzeichen;KundeAktenzeichen;Endpoint;EndpointScheme")
            create_csv_if_missing(p_dict["produkte_csv"], "Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz")
            for f in ["zusatz_csv", "gruss_csv", "header_csv", "einleitung_csv"]: create_csv_if_missing(p_dict[f], "")
    
    def build_profile_header(self):
        for w in self.header_container.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.header_container, text="Aktive Firma / Profil:", font=("Helvetica", 14, "bold")).pack(side="left")
        
        profil_namen = [p["profil_name"] for p in self.config["profiles"]]
        self.combo_profile = ctk.CTkComboBox(self.header_container, values=profil_namen, command=self.on_profile_switch)
        self.combo_profile.set(self.p_config["profil_name"])
        self.combo_profile.pack(side="left", padx=10)
    
    def on_profile_switch(self, wahl):
        for i, p in enumerate(self.config["profiles"]):
            if p["profil_name"] == wahl:
                # 1. Check Lock manuell vorab, um ggf. den Wechsel abzubrechen
                base_path = self.config.get("base_data_path")
                if base_path:
                    new_lock = os.path.join(base_path, p["profil_name"].replace(" ", "_"), "erechnung.lock")
                    if os.path.exists(new_lock):
                        messagebox.showwarning("Firma gesperrt", f"Die Firma '{p['profil_name']}' wird aktuell bearbeitet.\nBitte warten.")
                        self.combo_profile.set(self.p_config["profil_name"])
                        return

                # 2. Alte Locks aufheben, neue Firma setzen
                self.unlock_firm()
                self.config["active_profile_index"] = i
                speichere_config(self.config)
                
                # 3. Ordner für die gewählte Firma sicherstellen
                self.setup_firm_folders(self.p_config)
                self.lock_firm(self.p_config, "erechnung.lock")
                
                if not self.enforce_network_version():
                    return
                    
                # 4. Gesamte Benutzeroberfläche und Daten mit der neuen Firma neu laden
                self.refresh_all_ui()
                break

    def add_profile(self):
        from datenbank import get_default_profile
        import time
        d_name = ctk.CTkInputDialog(text="Name der neuen Firma:", title="Neues Profil")
        name = d_name.get_input()
        if name:
            new_p = get_default_profile(str(int(time.time()))[-5:])
            new_p["profil_name"] = name
            # Ordneranlage nach Deklaration von new_p aufrufen
            self.setup_firm_folders(new_p, show_message=True) 
            self.config["profiles"].append(new_p)
            
            # Neue Firma sofort sperren (da sie jetzt aktiv wird)
            self.unlock_firm()
            self.lock_firm(new_p)
            
            self.config["active_profile_index"] = len(self.config["profiles"]) - 1
            speichere_config(self.config)
            self.build_profile_header()
            self.refresh_all_ui()

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
        self.positionen_liste = []
        self.zusatz_dict = {}
        self.has_unsaved_changes = False

        # Alte Inhalte in allen Reitern löschen
        reiter_liste = [
            self.tab_manuell, 
            self.tab_erfassen, 
            self.tab_ausgang, 
            self.tab_eingang, 
            self.tab_settings, 
            self.tab_hilfe
        ]
        for tab in reiter_liste:
            for w in tab.winfo_children():
                w.destroy()

        # Inhalte neu aufbauen
        self.build_manuell_tab()
        self.build_erfassen_tab()
        self.build_ausgang_tab()
        self.build_eingang_tab()
        self.build_settings_tab()
        self.build_hilfe_tab()
        
        # Datumsfelder und Rechnungsnummer im Reiter "Rechnung erstellen" füllen
        heute = datetime.now()
        tage = int(self.p_config.get("faelligkeit_tage", "29")) if str(self.p_config.get("faelligkeit_tage", "29")).isdigit() else 29
        
        self.entry_r_datum.delete(0, 'end')
        self.entry_r_datum.insert(0, heute.strftime('%Y-%m-%d'))
        
        self.entry_f_datum.delete(0, 'end')
        self.entry_f_datum.insert(0, (heute + timedelta(days=tage)).strftime('%Y-%m-%d'))
        
        self.entry_r_nr.delete(0, 'end')
        self.entry_r_nr.insert(0, berechne_naechste_rechnungsnummer(self.p_config.get("letzte_rechnungsnummer", "")))

    def on_closing(self, skip_warning=False):
        # 1. Sicherheitsabfrage: Prüft, ob Positionen da sind UND ob keine Ausnahme gilt
        if not skip_warning and hasattr(self, 'positionen_liste') and len(self.positionen_liste) > 0:
            import tkinter.messagebox as messagebox
            antwort = messagebox.askyesno(
                "Programm beenden?",
                "Es befinden sich aktuell Rechnungspositionen in der Bearbeitungsmaske.\n\n"
                "Nicht gespeicherte Daten gehen beim Beenden unwiderruflich verloren.\n\n"
                "Möchten Sie das Programm wirklich schließen?"
            )
            if not antwort:
                return 
        self.config["window_geometry"] = self.geometry()
        from datenbank import speichere_config
        speichere_config(self.config)
        
        # 2. Lock-Dateien sicher über die interne Funktion entfernen
        try:
            self.unlock_firm()
        except:
            pass
            
        self.destroy()
        import sys
        sys.exit(0)
        
    def center_window(self, dialog, width, height):
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def handle_plus_key(self, event):
        if self.tabview.get() == "📝 ERSTELLEN":
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
