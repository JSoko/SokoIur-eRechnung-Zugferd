"""
tab_einstellungen.py
--------------------
Logik und Aufbau des Reiters "Einstellungen / Konfig."
"""
import os
import shutil
import zipfile
import re
from datetime import datetime
import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog

from config import *
from utils import *
from crud import *
from gui_utils import create_tooltip

class TabEinstellungenMixin:
    def backup_profile_data(self):
        import zipfile
        
        # 1. Backup-Verzeichnis abfragen beim ersten Mal
        backup_dir = self.config.get("backup_dir", "")
        if not backup_dir or not os.path.exists(backup_dir):
            messagebox.showinfo("Sicherung", "Bitte wählen Sie ein Verzeichnis aus, in dem Ihre Backups dauerhaft gespeichert werden sollen.")
            backup_dir = filedialog.askdirectory(title="Backup-Verzeichnis wählen")
            if not backup_dir: return
            self.config["backup_dir"] = backup_dir
            speichere_config(self.config)
            
        prof_name = self.p_config["profil_name"]
        safe_prof_name = prof_name.replace(" ", "_")
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        base_name = f"{safe_prof_name}_{date_str}"
        
        # 2. Dateinamen mit Schema und Zähler generieren
        counter = 0
        while True:
            suffix = f"_{counter:02d}" if counter > 0 else ""
            zip_name = f"{base_name}{suffix}.zip"
            zip_path = os.path.join(backup_dir, zip_name)
            if not os.path.exists(zip_path):
                break
            counter += 1
            
        base_data_path = self.config.get("base_data_path", "")
        if not base_data_path: return
        firm_dir = os.path.join(base_data_path, safe_prof_name)
        
        if not os.path.exists(firm_dir):
            return messagebox.showerror("Fehler", "Firmenverzeichnis nicht gefunden!")
            
        try:
            # 3. ZIP-Archiv erstellen (Lock-Dateien ausschließen)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(firm_dir):
                    for file in files:
                        if file.endswith(".lock"): continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, firm_dir)
                        zipf.write(file_path, arcname)
                        
            messagebox.showinfo("Erfolg", f"Backup erfolgreich erstellt:\n{zip_path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen des Backups:\n{e}")

    def restore_profile_data(self):
        import zipfile
        import shutil
        from datenbank import get_default_profile
        
        backup_dir = self.config.get("backup_dir", os.path.expanduser("~"))
        zip_path = filedialog.askopenfilename(
            title="Backup-Archiv (ZIP) auswählen",
            initialdir=backup_dir,
            filetypes=[("ZIP-Archive", "*.zip")]
        )
        if not zip_path: return
        
        # 1. Auswahlfenster: Geöffnete oder neue Firma?
        d_choice = ctk.CTkToplevel(self)
        d_choice.title("Restore Ziel")
        self.center_window(d_choice, 480, 200)
        d_choice.transient(self)
        d_choice.grab_set()
        
        ctk.CTkLabel(d_choice, text="Wohin sollen die Backup-Daten importiert werden?", font=("Helvetica", 14, "bold")).pack(pady=20)
        result = {"choice": None}
        
        def choose_current():
            if messagebox.askyesno("Warnung", "ACHTUNG: Alle bestehenden Daten der GEÖFFNETEN Firma werden überschrieben!\nFortfahren?"):
                result["choice"] = "current"
                d_choice.destroy()
                
        def choose_new():
            result["choice"] = "new"
            d_choice.destroy()
            
        f_btn = ctk.CTkFrame(d_choice, fg_color="transparent")
        f_btn.pack(pady=10)
        self.create_button(f_btn, text="In GEÖFFNETE Firma", fg_color="#b30000", hover_color="#800000", command=choose_current).pack(side="left", padx=10)
        self.create_button(f_btn, text="In NEUE Firma (anlegen)", command=choose_new).pack(side="left", padx=10)
        
        self.wait_window(d_choice)
        if not result["choice"]: return
        
        base_data_path = self.config.get("base_data_path", "")
        if not base_data_path: return
        
        if result["choice"] == "current":
            firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_"))
            try:
                # Verzeichnis leeren (außer Locks)
                for item in os.listdir(firm_dir):
                    if item.endswith(".lock"): continue
                    item_path = os.path.join(firm_dir, item)
                    if os.path.isdir(item_path): shutil.rmtree(item_path)
                    else: os.remove(item_path)
                        
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(firm_dir)
                    
                self.refresh_all_ui()
                messagebox.showinfo("Restore", "Daten wurden erfolgreich in die geöffnete Firma importiert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Restore: {e}")
                
        elif result["choice"] == "new":
            d_name = ctk.CTkInputDialog(text="Name der NEUEN Firma für den Import:", title="Neue Firma")
            new_name = d_name.get_input()
            if not new_name: return
            
            for p in self.config["profiles"]:
                if p["profil_name"].lower() == new_name.lower():
                    return messagebox.showerror("Fehler", "Eine Firma mit diesem Namen existiert bereits!")
                    
            safe_new_name = new_name.replace(" ", "_")
            new_firm_dir = os.path.join(base_data_path, safe_new_name)
            
            if os.path.exists(new_firm_dir):
                return messagebox.showerror("Fehler", "Der Ordner existiert bereits im Dateisystem!")
                
            try:
                os.makedirs(new_firm_dir)
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(new_firm_dir)
                    
                import time
                new_p = get_default_profile(str(int(time.time()))[-5:])
                new_p["profil_name"] = new_name
                self.setup_firm_folders(new_p, show_message=False)
                
                self.config["profiles"].append(new_p)
                self.config["active_profile_index"] = len(self.config["profiles"]) - 1
                speichere_config(self.config)
                
                self.build_profile_header()
                self.unlock_firm()
                self.lock_firm(new_p)
                self.refresh_all_ui()
                messagebox.showinfo("Restore", f"Daten wurden erfolgreich in die neue Firma '{new_name}' importiert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Erstellen der Firma: {e}")
    
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
            neue_nr = val.strip()
            self.p_config["letzte_rechnungsnummer"] = neue_nr
            speichere_config(self.config)
            self.lbl_letzte_nr.configure(text=neue_nr)
            
            naechste = berechne_naechste_rechnungsnummer(neue_nr)
            self.entry_r_nr.delete(0, 'end')
            self.entry_r_nr.insert(0, naechste)
            
            # NEU: CLI-Beispiel unten im Fenster dynamisch aktualisieren
            if hasattr(self, 'entry_cli'):
                prof_name = self.p_config.get("profil_name", "")
                cmd = f'SokoIur_eRechnung.exe --auto --profil "{prof_name}" --renr "{naechste}" --rechnung "%TEMP%\\rechnung.csv" --kopie "%USERPROFILE%\\Documents"'
                self.entry_cli.configure(state="normal")
                self.entry_cli.delete(0, 'end')
                self.entry_cli.insert(0, cmd)
                self.entry_cli.configure(state="readonly")

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
    
    #Einstellungstab
    def build_settings_tab(self):
        from config import get_appdata_dir
        
        scroll_main = ctk.CTkScrollableFrame(self.tab_settings)
        scroll_main.pack(fill="both", expand=True, padx=10, pady=5)

        # Farb-Design für die "Karten" (Hellmodus / Dunkelmodus)
        card_fg = ("#e8e8e8", "#2b2b2b") 

        # --- KARTE 1: Profil & Firma ---
        f_prof_card = ctk.CTkFrame(scroll_main, fg_color=card_fg, corner_radius=10)
        f_prof_card.pack(fill="x", pady=(5, 10), padx=10)
        
        ctk.CTkLabel(f_prof_card, text="👤 Aktive Firma / Profil verwalten", font=("Helvetica", 15, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        f_prof_btns = ctk.CTkFrame(f_prof_card, fg_color="transparent")
        f_prof_btns.pack(fill="x", padx=15, pady=(0, 15))
        
        self.create_button(f_prof_btns, text="+ Neu", width=100, command=self.add_profile).pack(side="left", padx=(0, 10))
        self.create_button(f_prof_btns, text="✎ Umbenennen", width=110, command=self.rename_profile).pack(side="left", padx=10)
        
        btn_leer = self.create_button(f_prof_btns, text="🧹 Daten leeren", width=110, fg_color="#b85c00", hover_color="#8f4700", command=self.clear_profile_data)
        btn_leer.pack(side="left", padx=10)
        create_tooltip(btn_leer, "Löscht alle Rechnungen und Journale der aktiven Firma.\nStammdaten (Kunden, Produkte, Briefbogen) bleiben erhalten.")
        
        if len(self.config["profiles"]) > 1:
            self.create_button(f_prof_btns, text="🗑 Löschen", width=100, fg_color="#b30000", hover_color="#800000", command=self.delete_profile).pack(side="left", padx=10)

        # NEU: Zweite Zeile für Backup/Restore
        f_prof_btns2 = ctk.CTkFrame(f_prof_card, fg_color="transparent")
        f_prof_btns2.pack(fill="x", padx=15, pady=(0, 15))
        
        btn_backup = self.create_button(f_prof_btns2, text="💾 Firmendaten backup", width=150, command=self.backup_profile_data, fg_color="#1f538d", hover_color="#14375d")
        btn_backup.pack(side="left", padx=(0, 10))
        
        btn_restore = self.create_button(f_prof_btns2, text="📂 Firmendaten restore", width=150, command=self.restore_profile_data, fg_color="#444", hover_color="#666")
        btn_restore.pack(side="left", padx=10)

        # --- KARTE 2: Stammdaten & Datenbanken ---
        f_stamm_card = ctk.CTkFrame(scroll_main, fg_color=card_fg, corner_radius=10)
        f_stamm_card.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(f_stamm_card, text="📁 Stammdaten & Datenbanken", font=("Helvetica", 15, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        f_stamm_r1 = ctk.CTkFrame(f_stamm_card, fg_color="transparent")
        f_stamm_r1.pack(fill="x", padx=15, pady=5)
        self.create_button(f_stamm_r1, text="🏢 Firmendaten", command=self.open_firma_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=(0, 10))
        self.create_button(f_stamm_r1, text="👥 Kunden", command=self.open_kunden_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=10)
        self.create_button(f_stamm_r1, text="📦 Produkte", command=self.open_produkte_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=10)
        
        btn_datev = self.create_button(f_stamm_r1, text="📈 DATEV-Konten", command=self.open_datev_manager, fg_color="#107C41", hover_color="#0b5c30")
        btn_datev.pack(side="left", padx=10)
        create_tooltip(btn_datev, "Konfigurieren Sie hier die Erlös- und Aufwandskonten\nfür den Buchhaltungsexport zum Steuerberater.")
        
        btn_brief = self.create_button(f_stamm_r1, text="📄 Briefbogen hinterlegen", command=self.choose_briefbogen, fg_color="#1f538d", hover_color="#14375d")
        btn_brief.pack(side="left", padx=10)
        create_tooltip(btn_brief, "Hinterlegen Sie ein PDF als Design-Vorlage\n(Logo, Fußzeile) für Ihre Ausgangsrechnungen.")

        f_stamm_r2 = ctk.CTkFrame(f_stamm_card, fg_color="transparent")
        f_stamm_r2.pack(fill="x", padx=15, pady=(5, 15))
        self.create_button(f_stamm_r2, text="⬇️ Kunden importieren (CSV)", command=self.import_kunden_csv, fg_color="#444", hover_color="#666").pack(side="left", padx=(0, 10))
        self.create_button(f_stamm_r2, text="⬇️ Produkte importieren (CSV)", command=self.import_produkte_csv, fg_color="#444", hover_color="#666").pack(side="left", padx=10)

        # --- KARTE 3: Nummernkreise ---
        f_num_card = ctk.CTkFrame(scroll_main, fg_color=card_fg, corner_radius=10)
        f_num_card.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_num_card, text="🔢 Nummernkreise & Rechnungsjahr", font=("Helvetica", 15, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        f_num_grid = ctk.CTkFrame(f_num_card, fg_color="transparent")
        f_num_grid.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(f_num_grid, text="Aktuelles Rechnungsjahr:", width=180, anchor="w").grid(row=0, column=0, pady=5, sticky="w")
        self.combo_jahr = ctk.CTkComboBox(f_num_grid, values=self.get_available_years(), command=self.on_settings_jahr_change)
        self.combo_jahr.set(self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year)))
        self.combo_jahr.grid(row=0, column=1, pady=5, sticky="w")
        
        ctk.CTkLabel(f_num_grid, text="Letzte Rechnungs-Nr.:", width=180, anchor="w").grid(row=1, column=0, pady=5, sticky="w")
        self.lbl_letzte_nr = ctk.CTkLabel(f_num_grid, text=self.p_config.get("letzte_rechnungsnummer", "Noch keine"), width=150, anchor="w")
        self.lbl_letzte_nr.grid(row=1, column=1, pady=5, sticky="w")
        self.create_button(f_num_grid, text="✏️ Korrigieren", width=100, command=self.edit_letzte_nr).grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(f_num_grid, text="Letzte ER-Nr.:", width=180, anchor="w").grid(row=2, column=0, pady=5, sticky="w")
        self.lbl_letzte_er_nr = ctk.CTkLabel(f_num_grid, text=self.p_config.get("letzte_eingangsrechnungsnummer","") or "Noch keine", width=150, anchor="w")
        self.lbl_letzte_er_nr.grid(row=2, column=1, pady=5, sticky="w")
        self.create_button(f_num_grid, text="✏️ Korrigieren", width=100, command=self.edit_letzte_eingangs_nr).grid(row=2, column=2, padx=10, pady=5, sticky="w")

        # Direkte Speicher-Funktionen für die Checkboxen, damit sie beim Klick sofort ins Profil geschrieben werden
        def toggle_xrechnung_leseabschrift():
            self.p_config["xrechnung_leseabschrift"] = bool(self.chk_xrechnung_leseabschrift.get())
            speichere_config(self.config)
            
        def toggle_audit_reason():
            self.p_config["audit_reason_required"] = bool(self.chk_audit_reason.get())
            speichere_config(self.config)

        self.chk_xrechnung_leseabschrift = ctk.CTkCheckBox(f_num_grid, text="Bei XRechnungen standardmäßig PDF-Leseabschrift erzeugen", command=toggle_xrechnung_leseabschrift)
        self.chk_xrechnung_leseabschrift.grid(row=3, column=0, columnspan=3, pady=(15, 5), sticky="w")
        create_tooltip(self.chk_xrechnung_leseabschrift, "XRechnungen sind reine XML-Dateien.\nDiese Option erzeugt zusätzlich ein menschlich\nlesbares PDF-Dokument für Ihr Ausgangsarchiv.")
        if self.p_config.get("xrechnung_leseabschrift", True): self.chk_xrechnung_leseabschrift.select()
        else: self.chk_xrechnung_leseabschrift.deselect()

        self.chk_audit_reason = ctk.CTkCheckBox(f_num_grid, text="GoBD: Begründungszwang bei Änderung/Löschung von Rechnungen (Audit-Log)", command=toggle_audit_reason)
        self.chk_audit_reason.grid(row=4, column=0, columnspan=3, pady=(5, 5), sticky="w")
        create_tooltip(self.chk_audit_reason, "Erfordert die Eingabe eines Grundes, wenn eine Rechnung\nüberschrieben oder im Journal gelöscht wird.\nWichtig für die GoBD-Konformität.")
        if self.p_config.get("audit_reason_required", False): self.chk_audit_reason.select()
        else: self.chk_audit_reason.deselect()

        # --- KARTE 4: Speicherorte ---
        f_path_card = ctk.CTkFrame(scroll_main, fg_color=card_fg, corner_radius=10)
        f_path_card.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_path_card, text="📂 Speicherorte & Ordnerstruktur", font=("Helvetica", 15, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        f_base = ctk.CTkFrame(f_path_card, fg_color="transparent")
        f_base.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(f_base, text="Daten-Grundpfad:", width=180, anchor="w").pack(side="left")
        self.entry_base_path = ctk.CTkEntry(f_base)
        self.entry_base_path.insert(0, self.config.get("base_data_path", ""))
        self.entry_base_path.pack(side="left", padx=10, fill="x", expand=True)
        btn_browse = self.create_button(f_base, text="📁", width=40, command=lambda: self.browse_path_for_entry(self.entry_base_path, is_dir=True))
        btn_browse.pack(side="left")
        create_tooltip(btn_browse, "Hauptverzeichnis für alle Firmendaten.\nSollte bei Nutzung durch mehrere Rechner\nzwingend auf einem Netzlaufwerk liegen.")
        
        self.create_button(f_base, text="💾 Pfade anlegen & speichern", command=self.save_settings, fg_color="#1f538d", hover_color="#14375d").pack(side="left", padx=(10,0))
        
        ctk.CTkLabel(f_path_card, text="Aktive Pfade der aktuellen Firma (schreibgeschützt):", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 0))
        
        f_pfade = ctk.CTkFrame(f_path_card, fg_color="transparent")
        f_pfade.pack(fill="x", padx=15, pady=(5, 15))
        
        # Audit-Pfad dynamisch ermitteln
        base_data_path = self.config.get("base_data_path", "")
        firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_")) if base_data_path else ""
        audit_dir = os.path.join(firm_dir, "audit") if firm_dir else "Nicht gesetzt"
        
        pfade_liste = [
            ("Lokale App-Data", get_appdata_dir()),
            ("Ausgangsrechnungen", self.p_config.get("ausgabe_ordner", "Nicht gesetzt")),
            ("Ausgangsjournale", self.p_config.get("auswertungen_ordner", "Nicht gesetzt")),
            ("Eingangsarchiv Originale", self.p_config.get("bearbeitete_eingangsrechnungen_ordner", "Nicht gesetzt")),
            ("Eingangsarchiv Belege", self.p_config.get("eingangsrechnungen_ordner", "Nicht gesetzt")),
            ("Eingangsjournale", self.p_config.get("eingangsjournal_ordner", "Nicht gesetzt")),
            ("Audit-Logs (GoBD)", audit_dir)
        ]
        
        def open_folder_in_explorer(path_to_open):
            if os.path.exists(path_to_open):
                try:
                    os.startfile(path_to_open)
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler beim Öffnen:\n{e}")
            else:
                messagebox.showwarning("Ordner fehlt", f"Dieser Ordner wurde noch nicht automatisch angelegt:\n{path_to_open}")
        
        for r_idx, (label_text, val) in enumerate(pfade_liste):
            ctk.CTkLabel(f_pfade, text=label_text + ":", width=180, anchor="w").grid(row=r_idx, column=0, pady=3, sticky="w")
            e_pfad = ctk.CTkEntry(f_pfade, fg_color="transparent", border_width=0, text_color="gray")
            e_pfad.insert(0, val)
            e_pfad.configure(state="readonly")
            e_pfad.grid(row=r_idx, column=1, pady=3, sticky="ew", padx=10)
            
            btn_open = self.create_button(f_pfade, text="📂", width=30, fg_color="#444", hover_color="#666", command=lambda p=val: open_folder_in_explorer(p))
            btn_open.grid(row=r_idx, column=2, padx=(0, 10), pady=3)
            create_tooltip(btn_open, "Ordner im Windows-Explorer öffnen")
            
        f_pfade.columnconfigure(1, weight=1)

        # --- KARTE 5: CLI ---
        f_cli_card = ctk.CTkFrame(scroll_main, fg_color=card_fg, corner_radius=10)
        f_cli_card.pack(fill="x", pady=10, padx=10)
        
        lbl_cli = ctk.CTkLabel(f_cli_card, text="💻 Kommandozeile (CLI) / Fremdprogramme", font=("Helvetica", 15, "bold"))
        lbl_cli.pack(anchor="w", padx=15, pady=(10, 0))
        create_tooltip(lbl_cli, "Kopierbarer Beispielaufruf.\nFremdprogramme können diesen nutzen,\num Rechnungen unsichtbar im Hintergrund zu generieren.")
        
        prof_name = self.p_config.get("profil_name", "")
        letzte_nr = self.p_config.get("letzte_rechnungsnummer") or "RE-1000"
        naechste_nr = berechne_naechste_rechnungsnummer(letzte_nr)
        cmd = f'SokoIur_eRechnung.exe --auto --profil "{prof_name}" --renr "{naechste_nr}" --rechnung "%TEMP%\\rechnung.csv" --kopie "%USERPROFILE%\\Documents"'
        
        self.entry_cli = ctk.CTkEntry(f_cli_card, font=("Consolas", 12))
        self.entry_cli.insert(0, cmd)
        self.entry_cli.configure(state="readonly")
        self.entry_cli.pack(fill="x", padx=15, pady=(10, 15))
    
    def save_settings(self):
        base_path = self.entry_base_path.get().strip()
        if not base_path:
            return messagebox.showwarning("Fehler", "Bitte einen Grundpfad angeben.")
            
        self.config["base_data_path"] = base_path
        
        firm_folder = self.p_config["profil_name"].replace(" ", "_")
        firm_dir = os.path.join(base_path, firm_folder)
        ausw_dir = os.path.join(firm_dir, "aausw")
        are_dir = os.path.join(firm_dir, "are")
        arecsv_dir = os.path.join(firm_dir, "arecsv")  
        
        os.makedirs(ausw_dir, exist_ok=True)
        os.makedirs(are_dir, exist_ok=True)
        os.makedirs(arecsv_dir, exist_ok=True)  
        reneu_dir=os.path.join(firm_dir,"reneu"); rebearb_dir=os.path.join(firm_dir,"rebearb"); rchn_dir=os.path.join(firm_dir,"rchn"); einj_dir=os.path.join(firm_dir,"eausw")
        for incoming_dir in (reneu_dir,rebearb_dir,rchn_dir,einj_dir): os.makedirs(incoming_dir,exist_ok=True)
        
        self.p_config["auswertungen_ordner"] = ausw_dir
        self.p_config["ausgabe_ordner"] = are_dir
        self.p_config["eingangsordner"]=reneu_dir; self.p_config["bearbeitete_eingangsrechnungen_ordner"]=rebearb_dir
        self.p_config["eingangsrechnungen_ordner"]=rchn_dir; self.p_config["eingangsjournal_ordner"]=einj_dir
        self.p_config["xrechnung_leseabschrift"]=bool(self.chk_xrechnung_leseabschrift.get())
        self.p_config["audit_reason_required"] = bool(self.chk_audit_reason.get())
        dateien = ["firma.csv", "rechnung.csv", "briefbogen.pdf", "zusatz.csv", "gruss.csv", "vor_gruss.csv", "header.csv", "einleitung.csv", "kunden.csv", "produkte.csv"]
        
        for datei in dateien:
            key_name = datei.replace(".", "_")
            self.p_config[key_name] = os.path.join(firm_dir, datei)
            
        speichere_config(self.config)
        messagebox.showinfo("Gespeichert", f"Die Ordnerstruktur wurde in\n{firm_dir}\nangelegt und gespeichert!")

    
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
    
    def open_datev_manager(self):
        d_edit = ctk.CTkToplevel(self)
        d_edit.title("DATEV & Buchhaltung konfigurieren")
        self.center_window(d_edit, 500, 520)
        d_edit.transient(self)
        d_edit.grab_set()
        
        f_skr = ctk.CTkFrame(d_edit, fg_color="transparent")
        f_skr.pack(fill="x", padx=10, pady=(10, 20))
        ctk.CTkLabel(f_skr, text="Kontenrahmen:", width=120, anchor="w").pack(side="left")
        
        def on_skr_change(wahl):
            if messagebox.askyesno("Standardkonten laden", f"Möchten Sie die typischen DATEV-Standardkonten für {wahl} laden?\n\n(Ihre manuellen Eingaben werden überschrieben)"):
                if wahl == "SKR03":
                    e_e19.delete(0, 'end'); e_e19.insert(0, "8400")
                    e_e7.delete(0, 'end'); e_e7.insert(0, "8300")
                    e_e0.delete(0, 'end'); e_e0.insert(0, "8200")
                    e_deb.delete(0, 'end'); e_deb.insert(0, "10000")
                    e_a19.delete(0, 'end'); e_a19.insert(0, "3400")
                    e_a7.delete(0, 'end'); e_a7.insert(0, "3300")
                    e_a0.delete(0, 'end'); e_a0.insert(0, "3200")
                    e_kred.delete(0, 'end'); e_kred.insert(0, "70000")
                elif wahl == "SKR04":
                    e_e19.delete(0, 'end'); e_e19.insert(0, "4400")
                    e_e7.delete(0, 'end'); e_e7.insert(0, "4300")
                    e_e0.delete(0, 'end'); e_e0.insert(0, "4120")
                    e_deb.delete(0, 'end'); e_deb.insert(0, "10000")
                    e_a19.delete(0, 'end'); e_a19.insert(0, "5400")
                    e_a7.delete(0, 'end'); e_a7.insert(0, "5300")
                    e_a0.delete(0, 'end'); e_a0.insert(0, "5200")
                    e_kred.delete(0, 'end'); e_kred.insert(0, "70000")

        combo_skr = ctk.CTkComboBox(f_skr, values=["SKR03", "SKR04"], command=on_skr_change)
        combo_skr.set(self.p_config.get("datev_kontenrahmen", "SKR03"))
        combo_skr.pack(side="left", fill="x", expand=True, padx=(10, 0))

        ctk.CTkLabel(d_edit, text="Ausgangsrechnungen (Erlöse)", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(5, 0))
        e_e19 = self.create_input(d_edit, "Erlöskonto 19%:")
        e_e19.insert(0, self.p_config.get("datev_erloese_19", "8400"))
        e_e7 = self.create_input(d_edit, "Erlöskonto 7%:")
        e_e7.insert(0, self.p_config.get("datev_erloese_7", "8300"))
        e_e0 = self.create_input(d_edit, "Erlöskonto 0%:")
        e_e0.insert(0, self.p_config.get("datev_erloese_0", "8200"))
        e_deb = self.create_input(d_edit, "Sammel-Debitor:")
        e_deb.insert(0, self.p_config.get("datev_debitor", "10000"))
        
        ctk.CTkLabel(d_edit, text="Eingangsrechnungen (Aufwand)", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 0))
        e_a19 = self.create_input(d_edit, "Aufwandskonto 19%:")
        e_a19.insert(0, self.p_config.get("datev_aufwand_19", "3400"))
        e_a7 = self.create_input(d_edit, "Aufwandskonto 7%:")
        e_a7.insert(0, self.p_config.get("datev_aufwand_7", "3300"))
        e_a0 = self.create_input(d_edit, "Aufwandskonto 0%:")
        e_a0.insert(0, self.p_config.get("datev_aufwand_0", "3200"))
        e_kred = self.create_input(d_edit, "Sammel-Kreditor:")
        e_kred.insert(0, self.p_config.get("datev_kreditor", "70000"))

        def save():
            self.p_config["datev_kontenrahmen"] = combo_skr.get()
            self.p_config["datev_erloese_19"] = e_e19.get().strip()
            self.p_config["datev_erloese_7"] = e_e7.get().strip()
            self.p_config["datev_erloese_0"] = e_e0.get().strip()
            self.p_config["datev_debitor"] = e_deb.get().strip()
            self.p_config["datev_aufwand_19"] = e_a19.get().strip()
            self.p_config["datev_aufwand_7"] = e_a7.get().strip()
            self.p_config["datev_aufwand_0"] = e_a0.get().strip()
            self.p_config["datev_kreditor"] = e_kred.get().strip()
            speichere_config(self.config)
            d_edit.destroy()
            messagebox.showinfo("Gespeichert", "DATEV-Kontenrahmen aktualisiert!")
            
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

    def clear_profile_data(self):
        warnung = (
            "ACHTUNG: Dies löscht unwiderruflich ALLE erfassten Rechnungen, Journale und PDFs der aktiven Firma!\n"
            "Stammdaten (Firmendaten, Kunden, Produkte, Briefbogen) und Textvorlagen bleiben erhalten.\n\n"
            "Bitte geben Sie 'LEEREN' ein, um fortzufahren:"
        )
        pwd = ctk.CTkInputDialog(text=warnung, title="Sicherheitsabfrage").get_input()
        if pwd == "LEEREN":
            try:
                # 1. rechnung.csv leeren (nur Kopfzeile behalten)
                rechnung_pfad = self.p_config.get("rechnung_csv", "")
                if os.path.exists(rechnung_pfad):
                    header = "Rechnungsnummer;Rechnungsdatum;Faelligkeitsdatum;KundeName;KundeStrasse;KundePLZ;KundeOrt;KundeLand;KundeEmail;KundeEndpoint;KundeEndpointScheme;KundeNr;Aktenzeichen;KundeAktenzeichen;LeistungszeitraumKopf;Ratenzahlung;PosNr;Menge;Einheit;Bezeichnung;EinzelpreisNetto;Steuersatz;Zusatztext;LeistungszeitraumPos"
                    with open(rechnung_pfad, 'w', encoding='utf-8-sig') as f:
                        f.write(header + "\n")
                
                # HINWEIS: Die zusatz_csv (Texte nach Zahlungshinweis / vor Gruß) 
                # wird hier bewusst NICHT mehr gelöscht, damit Ihre Vorlagen erhalten bleiben!

                # 2. Zähler zurücksetzen
                self.p_config["letzte_rechnungsnummer"] = ""
                self.p_config["letzte_eingangsrechnungsnummer"] = ""
                speichere_config(self.config)
                
                # 3. Ordnerinhalte löschen (Journale, Archiv, Auswertungen)
                ordner_keys = ["ausgabe_ordner", "auswertungen_ordner", "eingangsordner", "bearbeitete_eingangsrechnungen_ordner", "eingangsrechnungen_ordner", "eingangsjournal_ordner"]
                for key in ordner_keys:
                    ordner = self.p_config.get(key, "")
                    if ordner and os.path.exists(ordner):
                        for filename in os.listdir(ordner):
                            file_path = os.path.join(ordner, filename)
                            try:
                                if os.path.isdir(file_path): shutil.rmtree(file_path)
                                else: os.unlink(file_path)
                            except: pass
                
                # Zusatz: arecsv Ordner leeren
                are_dir = self.p_config.get("ausgabe_ordner", "")
                if are_dir:
                    arecsv_dir = os.path.join(os.path.dirname(are_dir), "arecsv")
                    if os.path.exists(arecsv_dir):
                        for filename in os.listdir(arecsv_dir):
                            file_path = os.path.join(arecsv_dir, filename)
                            try:
                                if os.path.isdir(file_path): shutil.rmtree(file_path)
                                else: os.unlink(file_path)
                            except: pass

                self.refresh_all_ui()
                messagebox.showinfo("Erfolg", "Alle Rechnungsdaten und Journale der Firma wurden erfolgreich geleert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Leeren der Daten: {e}")
        elif pwd is not None:
            messagebox.showerror("Fehler", "Falsche Eingabe! Vorgang abgebrochen.")

    def import_kunden_csv(self):
        pfad = filedialog.askopenfilename(title="Kunden CSV wählen", filetypes=[("CSV-Dateien", "*.csv*")])
        if not pfad: return
        ensure_utf8_csv(pfad)
        
        try:
            importierte_kunden = []
            with open(pfad, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                if not set(['Name', 'Strasse', 'PLZ_Ort', 'Land']).issubset(reader.fieldnames or []):
                    return messagebox.showwarning("Falsches Format", "Die Kopfzeile der CSV-Datei entspricht nicht dem geforderten Format.")
                for row in reader:
                    importierte_kunden.append(row)
                    
            if not importierte_kunden:
                return messagebox.showwarning("Fehler", "Die Datei ist leer oder ungültig.")

            bestehende_kunden = self.kunden_liste
            aktualisiert = 0
            neu = 0
            
            for imp_k in importierte_kunden:
                k_nr = imp_k.get('KundeNr', '').strip()
                matched = False
                if k_nr: # Überschreiben nur prüfen, wenn eine Kundennummer vorhanden ist
                    for i, best_k in enumerate(bestehende_kunden):
                        if best_k.get('KundeNr', '').strip() == k_nr:
                            bestehende_kunden[i].update(imp_k)
                            aktualisiert += 1
                            matched = True
                            break
                if not matched:
                    bestehende_kunden.append(imp_k)
                    neu += 1
                    
            speichere_alle_kunden(self.p_config.get("kunden_csv", "kunden.csv"), bestehende_kunden)
            self.kunden_liste = bestehende_kunden
            messagebox.showinfo("Import erfolgreich", f"Kunden importiert!\n\nNeu angelegt: {neu}\nAktualisiert (überschrieben): {aktualisiert}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Import: {e}")

    def import_produkte_csv(self):
        pfad = filedialog.askopenfilename(title="Produkte CSV wählen", filetypes=[("CSV-Dateien", "*.csv*")])
        if not pfad: return
        ensure_utf8_csv(pfad)
        
        try:
            importierte_produkte = []
            with open(pfad, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                if not set(['Bezeichnung', 'EinzelpreisNetto', 'Steuersatz']).issubset(reader.fieldnames or []):
                    return messagebox.showwarning("Falsches Format", "Die Kopfzeile der CSV-Datei entspricht nicht dem geforderten Format.")
                for row in reader:
                    importierte_produkte.append(row)
                    
            if not importierte_produkte:
                return messagebox.showwarning("Fehler", "Die Datei ist leer oder ungültig.")

            self.produkte_liste.extend(importierte_produkte)
            speichere_alle_produkte(self.p_config.get("produkte_csv", "produkte.csv"), self.produkte_liste)
            messagebox.showinfo("Import erfolgreich", f"{len(importierte_produkte)} Produkte wurden erfolgreich angehängt!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Import: {e}")
