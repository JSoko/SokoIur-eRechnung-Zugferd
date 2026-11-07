import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog  # <--- Diese Zeile muss hinzugefügt werden
import os
import sys
from datetime import datetime, timedelta
import webbrowser

from datenbank import speichere_config, get_resource_path, LOCK_FILE, berechne_naechste_rechnungsnummer
from gui_module import TabManuellMixin, TabAuswertungenMixin, TabEinstellungenMixin, TabHilfeMixin, UpdaterMixin

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk, TabManuellMixin, TabAuswertungenMixin, TabEinstellungenMixin, TabHilfeMixin, UpdaterMixin):
    
    def get_firm_lock_path(self):
        base_path = self.config.get("base_data_path")
        if not base_path: return None
        firm_dir = os.path.join(base_path, p_dict["profil_name"].replace(" ", "_")) if 'p_dict' in locals() else os.path.join(base_path, self.p_config["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir): os.makedirs(firm_dir, exist_ok=True)
        return os.path.join(firm_dir, "erechnung.lock")
    
    def set_firm_lock(self):
        lock_file = self.get_firm_lock_path()
        if not lock_file: return
        try:
            with open(lock_file, "w") as f: f.write("LOCKED")
            self.current_lock_file = lock_file
        except: pass
    
    def unlock_firm(self):
        if hasattr(self, 'current_lock_file') and self.current_lock_file and os.path.exists(self.current_lock_file):
            try: os.remove(self.current_lock_file)
            except: pass
            self.current_lock_file = None
    
    def on_tab_change(self):
        if getattr(self, '_initializing', False):
            return  # Während des Starts ignorieren
            
        selected_tab = self.tabview.get()
        if selected_tab in ["Manuelle Eingabe", "Einstellungen"]:
            if not self.check_and_handle_lock(selected_tab):
                self.tabview.set("Hilfe & Doku")
                return
            self.lock_firm(self.p_config)
        else:
            self.unlock_firm()

    def lock_firm(self, p_dict):
        base_path = self.config.get("base_data_path")
        if not base_path: return True
        firm_dir = os.path.join(base_path, p_dict["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir): os.makedirs(firm_dir, exist_ok=True)
        
        lock_file = os.path.join(firm_dir, "erechnung.lock")
        
        # WICHTIG: Wenn wir den Lock selbst halten (gleiche Sitzung), ist das unschädlich
        if hasattr(self, 'current_lock_file') and self.current_lock_file == lock_file:
            return True

        if os.path.exists(lock_file):
            # Optional: Prüfen ob die Lock-Datei veraltet ist (z.B. älter als 12 Stunden von einem abgestürzten Prozess)
            try:
                file_age = time.time() - os.path.getmtime(lock_file)
                if file_age > 43200: # 12 Stunden
                    os.remove(lock_file)
                else:
                    messagebox.showwarning("Firma gesperrt", f"Die Firma '{p_dict['profil_name']}' wird aktuell von einem anderen Benutzer bearbeitet.\nBitte warten Sie, bis diese freigegeben ist.")
                    return False
            except:
                return False
            
        try:
            with open(lock_file, "w") as f: f.write(str(os.getpid())) # Speichert die Prozess-ID zur Sicherheit
            self.current_lock_file = lock_file
            return True
        except: return True

    def check_and_handle_lock(self, target_tab):
        base_path = self.config.get("base_data_path")
        if not base_path: return True
        firm_dir = os.path.join(base_path, self.p_config["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir): os.makedirs(firm_dir, exist_ok=True)
        lock_file = os.path.join(firm_dir, "erechnung.lock")

        # WICHTIG: Wenn wir den Lock in dieser Instanz bereits halten, gar nicht erst warnen!
        if hasattr(self, 'current_lock_file') and self.current_lock_file == lock_file:
            return True

        while os.path.exists(lock_file):
            # Wenn wir selbst der Halter sind (gleiche PID), automatisch bereinigen und fortfahren
            try:
                with open(lock_file, "r") as f:
                    content = f.read().strip()
                if content == str(os.getpid()):
                    self.current_lock_file = lock_file
                    return True
            except:
                pass

            dlg = ctk.CTkToplevel(self)
            dlg.title("Firma gesperrt")
            self.center_window(dlg, 450, 200)
            dlg.transient(self); dlg.grab_set()

            ctk.CTkLabel(dlg, text=f"Die Firma '{self.p_config['profil_name']}' wird aktuell\nvon einem anderen Benutzer bearbeitet.", font=("Helvetica", 13, "bold"), justify="center").pack(pady=20)

            f_btn = ctk.CTkFrame(dlg, fg_color="transparent")
            f_btn.pack(pady=10)

            result = {"action": None}

            def do_retry():
                result["action"] = "retry"
                dlg.destroy()

            def do_force_unlock():
                if messagebox.askyesno(
                    "Sicherheitswarnung", 
                    "Soll der Lock wirklich entfernt werden?\n\nEs droht Datenverlust! Stellen Sie sicher, dass die Daten aktuell nicht von einem anderen Benutzer bearbeitet werden.",
                    parent=dlg,
                    default="no"
                ):
                    result["action"] = "force"
                    dlg.destroy()

            self.create_button(f_btn, text="Erneut prüfen", width=120, command=do_retry).pack(side="left", padx=5)
            self.create_button(f_btn, text="Lock entfernen", width=120, fg_color="#b30000", hover_color="#800000", command=do_force_unlock).pack(side="left", padx=5)

            self.wait_window(dlg)

            if result["action"] == "retry":
                continue
            elif result["action"] == "force":
                try: os.remove(lock_file)
                except: pass
                break
            else:
                return False

        return True
        
    def __init__(self, config, start_in_edit=False):
        super().__init__()
        self.config = config
        self._initializing = True  # NEU: Verhindert zu frühes Auslösen beim Start
        self.title("SokoIur eRechnung")
        self.setup_firm_folders(self.p_config, show_message=True)
        
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
        
        self.tabview = ctk.CTkTabview(self)  # Ohne command=...
        self.tabview.pack(padx=20, pady=(10, 5), fill="both", expand=True)
        
        self.tab_manuell = self.tabview.add("Manuelle Eingabe")
        self.tab_ausw = self.tabview.add("Auswertungen")
        self.tab_settings = self.tabview.add("Einstellungen")
        self.tab_hilfe = self.tabview.add("Hilfe & Doku")
        
        # Abfrage des Datenspeicherorts beim allerersten Start
        if not self.config.get("base_data_path"):
            new_path = self.ask_for_base_path("Zentralen Datenspeicherort festlegen")
            if not new_path:
                sys.exit(0)
            self.config["base_data_path"] = new_path
            # Hier ist show_message=True gewollt, da es die Ersteinrichtung ist
            self.setup_firm_folders(self.p_config, show_message=True)
            speichere_config(self.config)

        # Versionsprüfung vor dem Laden der UI-Daten
        if not self.enforce_network_version():
            return
        
        # NEU: Sofortige Lock-Prüfung beim Programmstart für die Start-Firma
        # Wenn die Firma bereits blockiert ist, den Start abbrechen oder in den Hilfe-Modus schalten
        lock_file = self.get_firm_lock_path()
        if lock_file and os.path.exists(lock_file):
            # Prüfen ob der Lock von einem *anderen* Prozess stammt
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

        # Start-Firma als aktiv sperren
        self.set_firm_lock()
            
        self.refresh_all_ui()
        self.tabview.set("Manuelle Eingabe")
        
        # NEU: Initialisierung abgeschlossen - Überwachung jetzt aktivieren
        self._initializing = False
        self.tabview.configure(command=self.on_tab_change)
        
        # GEÄNDERT: Abfrage der config (global) anstelle von p_config
        if not self.config.get("base_data_path"):
            new_path = self.ask_for_base_path("Zentralen Datenspeicherort festlegen")
            if not new_path:
                sys.exit(0)
            self.config["base_data_path"] = new_path
            self.setup_firm_folders(self.p_config)
            speichere_config(self.config)

        # Versionsprüfung vor dem Laden der UI-Daten
        if not self.enforce_network_version():
            return
        
        # NEU: Start-Firma sperren
        if not self.lock_firm(self.p_config):
            # Falls beim Start gesperrt, Programm nicht hart beenden, aber der User wurde gewarnt.
            pass
            
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
        
        # NEU: Beenden-Button ganz rechts im Footer platziert
        self.btn_footer_exit = ctk.CTkButton(f_footer, text="Beenden", width=80, fg_color="#b30000", hover_color="#800000", command=self.on_closing)
        self.btn_footer_exit.pack(side="right", padx=(5, 0))

        # Update-Button wandert dadurch (per pack side="right") optisch links neben den Beenden-Button
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
        firm_folder = p_dict["profil_name"].replace(" ", "_")
        firm_dir = os.path.join(base_path, firm_folder)
        ausw_dir = os.path.join(firm_dir, "ausw")
        are_dir = os.path.join(firm_dir, "are")
        
        already_exists = os.path.exists(firm_dir) and os.path.exists(os.path.join(firm_dir, "firma.csv"))
        
        os.makedirs(ausw_dir, exist_ok=True)
        os.makedirs(are_dir, exist_ok=True)
        
        p_dict["auswertungen_ordner"] = ausw_dir
        p_dict["ausgabe_ordner"] = are_dir
        
        dateien = ["firma.csv", "rechnung.csv", "briefbogen.pdf", "zusatz.csv", "gruss.csv", "header.csv", "einleitung.csv", "kunden.csv", "produkte.csv"]
        for datei in dateien:
            key_name = datei.replace(".", "_")
            p_dict[key_name] = os.path.join(firm_dir, datei)
            
        if already_exists:
            # Nur anzeigen, wenn es explizit gewünscht ist (z.B. bei Neuzuweisung / Ersteinrichtung)
            if show_message:
                messagebox.showinfo("Netzwerk-Daten gefunden", f"Es wurden bestehende Daten für '{p_dict['profil_name']}' gefunden und erfolgreich verknüpft!")
        else:
            from datenbank import create_csv_if_missing
            create_csv_if_missing(p_dict["firma_csv"], "FirmaName;Strasse;PLZ;Ort;Land;UStId;Steuernummer;BankName;IBAN;BIC;Email;Telefon")
            create_csv_if_missing(p_dict["rechnung_csv"], "Rechnungsnummer;Rechnungsdatum;Faelligkeitsdatum;KundeName;KundeStrasse;KundePLZ;KundeOrt;KundeLand;KundeNr;Aktenzeichen;LeistungszeitraumKopf;Ratenzahlung;PosNr;Menge;Einheit;Bezeichnung;EinzelpreisNetto;Steuersatz;Zusatztext;LeistungszeitraumPos")
            create_csv_if_missing(p_dict["kunden_csv"], "Name;Strasse;PLZ_Ort;Land;KundeNr;Aktenzeichen")
            create_csv_if_missing(p_dict["produkte_csv"], "Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz")
            for f in ["zusatz_csv", "gruss_csv", "header_csv", "einleitung_csv"]: create_csv_if_missing(p_dict[f], "")

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
        self.setup_firm_folders(p)  # Bleibt ohne show_message=True, daher keine Meldung!
        for i, p in enumerate(self.config["profiles"]):
            if p["profil_name"] == wahl:
                # Stelle sicher, dass die Ordner im Zentralpfad für diese Firma existieren
                self.setup_firm_folders(p)
                
                # Check Lock manuell vorab, um ggf. den Wechsel abzubrechen
                base_path = self.config.get("base_data_path")
                if base_path:
                    new_lock = os.path.join(base_path, p["profil_name"].replace(" ", "_"), "erechnung.lock")
                    if os.path.exists(new_lock):
                        messagebox.showwarning("Firma gesperrt", f"Die Firma '{p['profil_name']}' wird aktuell bearbeitet.\nBitte warten.")
                        self.combo_profile.set(self.p_config["profil_name"])
                        return

                self.unlock_firm()
                self.lock_firm(p)
                
                self.config["active_profile_index"] = i
                speichere_config(self.config)
                
                if not self.enforce_network_version():
                    return
                    
                self.refresh_all_ui()
                break

    def add_profile(self):
        self.setup_firm_folders(new_p, show_message=True)
        from datenbank import get_default_profile
        import time
        if len(self.config["profiles"]) >= 5: return messagebox.showwarning("Limit erreicht", "Maximal 5 Profile.")
        d_name = ctk.CTkInputDialog(text="Name der neuen Firma:", title="Neues Profil")
        name = d_name.get_input()
        if name:
            new_p = get_default_profile(str(int(time.time()))[-5:])
            new_p["profil_name"] = name
            
            # Automatische Ordneranlage im bereits festgelegten ZENTRALEN Pfad
            self.setup_firm_folders(new_p)
            
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
        self.unlock_firm() # NEU: Hebt die Sperre der aktiven Firma auf
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
