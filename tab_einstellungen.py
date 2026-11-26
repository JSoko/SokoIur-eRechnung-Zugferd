

"""
tab_einstellungen.py
--------------------
Logik und Aufbau des Reiters "Einstellungen / Konfig."
"""
import os
import sys
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
            self.show_info("Sicherung", "Bitte wählen Sie ein Verzeichnis aus, in dem Ihre Backups dauerhaft gespeichert werden sollen.")
            backup_dir = filedialog.askdirectory(title="Backup-Verzeichnis wählen")
            if not backup_dir:
                return
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
        if not base_data_path:
            return
        firm_dir = os.path.join(base_data_path, safe_prof_name)

        if not os.path.exists(firm_dir):
            return self.show_error("Fehler", "Firmenverzeichnis nicht gefunden!")

        try:
            # 3. ZIP-Archiv erstellen (Lock-Dateien ausschließen)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(firm_dir):
                    for file in files:
                        if file.endswith(".lock"):
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, firm_dir)
                        zipf.write(file_path, arcname)

            self.show_info("Erfolg", f"Backup erfolgreich erstellt:\n{zip_path}")
        except Exception as e:
            self.show_error("Fehler", f"Fehler beim Erstellen des Backups:\n{e}")

    def restore_profile_data(self):
        import zipfile
        import shutil
        from config import get_default_profile

        backup_dir = self.config.get("backup_dir", os.path.expanduser("~"))
        zip_path = filedialog.askopenfilename(
            title="Backup-Archiv (ZIP) auswählen",
            initialdir=backup_dir,
            filetypes=[("ZIP-Archive", "*.zip")]
        )
        if not zip_path:
            return

        # 1. Auswahlfenster: Geöffnete oder neue Firma?
        d_choice = ctk.CTkToplevel(self)
        d_choice.title("Restore Ziel")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d_choice)
        self.center_window(d_choice, 480, 200)
        d_choice.transient(self)
        d_choice.grab_set()

        ctk.CTkLabel(d_choice, text="Wohin sollen die Backup-Daten importiert werden?", font=("Helvetica", 14, "bold")).pack(pady=20)
        result = {"choice": None}

        def choose_current():
            if self.ask_yes_no("Warnung", "ACHTUNG: Alle bestehenden Daten der GEÖFFNETEN Firma werden überschrieben!\nFortfahren?", parent=d_choice):
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
        if not result["choice"]:
            return

        base_data_path = self.config.get("base_data_path", "")
        if not base_data_path:
            return

        if result["choice"] == "current":
            firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_"))
            try:
                # Verzeichnis leeren (außer Locks)
                for item in os.listdir(firm_dir):
                    if item.endswith(".lock"):
                        continue
                    item_path = os.path.join(firm_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)

                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(firm_dir)

                self.refresh_all_ui()
                self.show_info("Restore", "Daten wurden erfolgreich in die geöffnete Firma importiert.")
            except Exception as e:
                self.show_error("Fehler", f"Fehler beim Restore: {e}")

        elif result["choice"] == "new":
            d_name = ctk.CTkInputDialog(text="Name der NEUEN Firma für den Import:", title="Neue Firma")
            if hasattr(self, "apply_window_icon"):
                self.apply_window_icon(d_name)
            new_name = d_name.get_input()
            if not new_name:
                return

            for p in self.config["profiles"]:
                if p["profil_name"].lower() == new_name.lower():
                    return self.show_error("Fehler", "Eine Firma mit diesem Namen existiert bereits!")

            safe_new_name = new_name.replace(" ", "_")
            new_firm_dir = os.path.join(base_data_path, safe_new_name)

            if os.path.exists(new_firm_dir):
                return self.show_error("Fehler", "Der Ordner existiert bereits im Dateisystem!")

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
                if len(self.config["profiles"]) >= 3 and hasattr(self, "license_mgr"):
                    self.license_mgr.record_pro_feature_use("Mehr-Firmen-Betrieb (ab dem 3. Firmenprofil)")
                self.show_info("Restore", f"Daten wurden erfolgreich in die neue Firma '{new_name}' importiert.")
            except Exception as e:
                self.show_error("Fehler", f"Fehler beim Erstellen der Firma: {e}")

    def get_available_years(self):
        ausg_ordner = self.p_config.get("ausgabe_ordner", "Rechnungen_PDF")
        jahre = set()
        if os.path.exists(ausg_ordner):
            for d in os.listdir(ausg_ordner):
                if os.path.isdir(os.path.join(ausg_ordner, d)) and re.match(r'^\d{4}$', d):
                    jahre.add(d)
        curr = datetime.now().year
        jahre.add(str(curr))
        jahre.add(str(curr + 1))
        return sorted(list(jahre), reverse=True)

    def on_settings_jahr_change(self, wahl):
        ausg_ordner = self.p_config.get("ausgabe_ordner", "Rechnungen_PDF")
        ausw_ordner = self.p_config.get("auswertungen_ordner", "Auswertungen")
        jahr_ausg = os.path.join(ausg_ordner, wahl)
        jahr_ausw = os.path.join(ausw_ordner, wahl)

        if not os.path.exists(jahr_ausg) or not os.path.exists(jahr_ausw):
            if self.ask_yes_no("Ordner anlegen", f"Die Ordner für das Jahr {wahl} existieren noch nicht.\nSollen sie jetzt angelegt werden?"):
                os.makedirs(jahr_ausg, exist_ok=True)
                os.makedirs(jahr_ausw, exist_ok=True)
                self.p_config["aktuelles_rechnungsjahr"] = wahl
                speichere_config(self.config)
                self.show_info("Erfolg", f"Ordner für {wahl} angelegt.")
            else:
                self.combo_jahr.set(self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year)))
        else:
            self.p_config["aktuelles_rechnungsjahr"] = wahl
            speichere_config(self.config)

    def edit_letzte_nr(self):
        d = ctk.CTkInputDialog(text="Neue Rechnungsnummer eingeben:", title="Rechnungsnummer korrigieren")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d)
        val = d.get_input()
        if val and val.strip():
            neue_nr = val.strip()
            self.p_config["letzte_rechnungsnummer"] = neue_nr
            speichere_config(self.config)
            self.lbl_letzte_nr.configure(text=neue_nr)

            naechste = berechne_naechste_rechnungsnummer(neue_nr)
            self.entry_r_nr.delete(0, 'end')
            self.entry_r_nr.insert(0, naechste)

            if hasattr(self, 'entry_cli'):
                prof_name = self.p_config.get("profil_name", "")
                cmd = f'SokoIur_eRechnung.exe --auto --profil "{prof_name}" --renr "{naechste}" --rechnung "%TEMP%\\rechnung.csv" --kopie "%USERPROFILE%\\Documents"'
                self.entry_cli.configure(state="normal")
                self.entry_cli.delete(0, 'end')
                self.entry_cli.insert(0, cmd)
                self.entry_cli.configure(state="readonly")

    def edit_letzte_eingangs_nr(self):
        d = ctk.CTkInputDialog(
            text="Neue letzte Eingangsrechnungsnummer eingeben (z. B. ER260000 oder ER2600000):",
            title="Eingangsrechnungsnummer korrigieren"
        )
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d)
        val = d.get_input()
        if val and val.strip():
            neue_nr = val.strip().upper()
            if not re.match(r"^ER\d{6,}$", neue_nr):
                return self.show_warning(
                    "Ungültiges Format",
                    "Bitte geben Sie die Nummer im Format ER + 2-stelliges Jahr + mindestens 4-stelliger Zähler ein (z. B. ER260000 oder ER2600000)."
                )
            self.p_config["letzte_eingangsrechnungsnummer"] = neue_nr
            speichere_config(self.config)
            if hasattr(self, "lbl_letzte_er_nr"):
                self.lbl_letzte_er_nr.configure(text=neue_nr)

    def choose_briefbogen(self):
        import shutil
        import os
        from tkinter import filedialog
        import tkinter.messagebox as messagebox

        target_path = self.p_config.get("briefbogen_pdf", "")

        if not target_path or not os.path.exists(os.path.dirname(target_path)):
            return self.show_warning(
                "Fehler",
                "Der Zielordner für diese Firma existiert noch nicht.\n\nBitte klicken Sie unten erst auf 'Struktur anlegen & Pfade speichern'."
            )

        source_path = filedialog.askopenfilename(
            title="Briefbogen (PDF) auswählen",
            filetypes=[("PDF-Dateien", "*.pdf")]
        )

        if source_path:
            try:
                shutil.copy2(source_path, target_path)
                self.show_info(
                    "Erfolg",
                    f"Der Briefbogen wurde erfolgreich kopiert und für die aktive Firma hinterlegt unter:\n\n{target_path}"
                )
            except Exception as e:
                self.show_error("Fehler", f"Fehler beim Kopieren des Briefbogens:\n{str(e)}")

    def build_settings_tab(self):
        from config import get_appdata_dir

        scroll_main = ctk.CTkScrollableFrame(self.tab_settings)
        scroll_main.pack(fill="both", expand=True, padx=10, pady=5)

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

        f_prof_btns2 = ctk.CTkFrame(f_prof_card, fg_color="transparent")
        f_prof_btns2.pack(fill="x", padx=15, pady=(0, 15))

        btn_backup = self.create_button(f_prof_btns2, text="💾 Firmendaten backup", width=150, command=self.backup_profile_data, fg_color="#1f538d", hover_color="#14375d")
        btn_backup.pack(side="left", padx=(0, 10))

        btn_restore = self.create_button(f_prof_btns2, text="📂 Firmendaten restore", width=150, command=self.restore_profile_data, fg_color="#444", hover_color="#666")
        btn_restore.pack(side="left", padx=10)

        btn_lizenz = self.create_button(f_prof_btns2, text="🔑 Lizenz & Registrierung", width=175, command=self.license_mgr.open_license_dialog, fg_color="#0f766e", hover_color="#115e59")
        btn_lizenz.pack(side="left", padx=10)
        create_tooltip(btn_lizenz, "Lizenzstatus anzeigen sowie 1-Monats- oder 12-Monats-Schlüssel\neingeben bzw. aus einer Lizenzdatei einlesen (100 % lokal).")

        def toggle_default_lz_heute():
            self.p_config["default_lz_heute"] = bool(self.chk_default_lz_heute.get())
            speichere_config(self.config)
            if hasattr(self, "entry_lz_kopf") and self.entry_lz_kopf.winfo_exists():
                if self.p_config["default_lz_heute"] and not self.entry_lz_kopf.get().strip():
                    self.entry_lz_kopf.insert(0, datetime.now().strftime("%Y-%m-%d"))
                elif not self.p_config["default_lz_heute"] and self.entry_lz_kopf.get().strip() == datetime.now().strftime("%Y-%m-%d"):
                    self.entry_lz_kopf.delete(0, "end")
                if hasattr(self, "check_live_validation"):
                    self.check_live_validation()

        def toggle_default_ihr_zeichen():
            self.p_config["default_ihr_zeichen_dash"] = bool(self.chk_default_ihr_zeichen_dash.get())
            speichere_config(self.config)
            if hasattr(self, "entry_k_az") and self.entry_k_az.winfo_exists():
                if self.p_config["default_ihr_zeichen_dash"] and not self.entry_k_az.get().strip():
                    self.entry_k_az.insert(0, "-")
                elif not self.p_config["default_ihr_zeichen_dash"] and self.entry_k_az.get().strip() == "-":
                    self.entry_k_az.delete(0, "end")
                if hasattr(self, "check_live_validation"):
                    self.check_live_validation()

        def toggle_briefkopf_rechte_spalte():
            self.p_config["briefkopf_rechte_spalte"] = bool(self.chk_briefkopf_rechte_spalte.get())
            speichere_config(self.config)

        f_prof_checks = ctk.CTkFrame(f_prof_card, fg_color="transparent")
        f_prof_checks.pack(fill="x", padx=15, pady=(0, 8))

        self.chk_default_lz_heute = ctk.CTkCheckBox(
            f_prof_checks,
            text="Leistungszeitraum standardmäßig heute",
            command=toggle_default_lz_heute,
        )
        self.chk_default_lz_heute.pack(anchor="w", pady=(0, 4))
        if self.p_config.get("default_lz_heute", False):
            self.chk_default_lz_heute.select()
        else:
            self.chk_default_lz_heute.deselect()

        self.chk_default_ihr_zeichen_dash = ctk.CTkCheckBox(
            f_prof_checks,
            text="Ihr Zeichen standardmäßig -",
            command=toggle_default_ihr_zeichen,
        )
        self.chk_default_ihr_zeichen_dash.pack(anchor="w", pady=(0, 4))
        if self.p_config.get("default_ihr_zeichen_dash", False):
            self.chk_default_ihr_zeichen_dash.select()
        else:
            self.chk_default_ihr_zeichen_dash.deselect()

        self.chk_briefkopf_rechte_spalte = ctk.CTkCheckBox(
            f_prof_checks,
            text="Briefkopf mit rechter Spalte",
            command=toggle_briefkopf_rechte_spalte,
        )
        self.chk_briefkopf_rechte_spalte.pack(anchor="w")
        if self.p_config.get("briefkopf_rechte_spalte", True):
            self.chk_briefkopf_rechte_spalte.select()
        else:
            self.chk_briefkopf_rechte_spalte.deselect()

        ctk.CTkButton(
            f_prof_card,
            text="👥 Kunden & Artikel visuell verwalten",
            font=("Helvetica", 14, "bold"),
            fg_color="#1f538d",
            height=35,
            command=self.open_verwaltung_popup
        ).pack(fill="x", padx=15, pady=(5, 15))

        # --- KARTE 2: Stammdaten & Datenbanken ---
        f_stamm_card = ctk.CTkFrame(scroll_main, fg_color=card_fg, corner_radius=10)
        f_stamm_card.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(f_stamm_card, text="📁 Stammdaten & Datenbanken", font=("Helvetica", 15, "bold")).pack(anchor="w", padx=15, pady=(10, 5))

        f_stamm_r1 = ctk.CTkFrame(f_stamm_card, fg_color="transparent")
        f_stamm_r1.pack(fill="x", padx=15, pady=5)
        self.create_button(f_stamm_r1, text="🏢 Firmendaten", command=self.open_firma_manager, fg_color="#444", hover_color="#666").pack(side="left", padx=(0, 10))

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
        self.lbl_letzte_er_nr = ctk.CTkLabel(f_num_grid, text=self.p_config.get("letzte_eingangsrechnungsnummer", "") or "Noch keine", width=150, anchor="w")
        self.lbl_letzte_er_nr.grid(row=2, column=1, pady=5, sticky="w")
        self.create_button(f_num_grid, text="✏️ Korrigieren", width=100, command=self.edit_letzte_eingangs_nr).grid(row=2, column=2, padx=10, pady=5, sticky="w")

        def on_email_methode_change(wahl):
            self.p_config["email_versand_methode"] = wahl
            speichere_config(self.config)

        f_mail_methode = ctk.CTkFrame(f_num_grid, fg_color="transparent")
        f_mail_methode.grid(row=5, column=0, columnspan=3, pady=(10, 5), sticky="w")

        ctk.CTkLabel(f_mail_methode, text="E-Mail-Versand Client:", width=180, anchor="w").pack(side="left")
        combo_mail_methode = ctk.CTkComboBox(
            f_mail_methode,
            values=["Keine", "Outlook", "Thunderbird"],
            command=on_email_methode_change,
            width=160
        )
        combo_mail_methode.set(self.p_config.get("email_versand_methode", "Keine"))
        combo_mail_methode.pack(side="left", padx=10)
        create_tooltip(combo_mail_methode, "Wählen Sie aus, ob Rechnungen automatisch über Outlook,\nThunderbird oder klassisch per mailto + Explorer (Drag & Drop) versendet werden.")

        def save_tb_pfad():
            self.p_config["thunderbird_pfad"] = entry_tb.get().strip()
            speichere_config(self.config)
            self.show_info("Gespeichert", "Thunderbird-Pfad wurde aktualisiert.")

        f_tb_path = ctk.CTkFrame(f_num_grid, fg_color="transparent")
        f_tb_path.grid(row=6, column=0, columnspan=3, pady=(5, 10), sticky="w")

        ctk.CTkLabel(f_tb_path, text="Thunderbird .exe Pfad:", width=180, anchor="w").pack(side="left")
        entry_tb = ctk.CTkEntry(f_tb_path, width=280)
        entry_tb.pack(side="left", padx=10)
        entry_tb.insert(0, self.p_config.get("thunderbird_pfad", r"C:\Program Files\Mozilla Thunderbird\thunderbird.exe"))

        def browse_tb():
            p = filedialog.askopenfilename(title="thunderbird.exe auswählen", filetypes=[("Executable", "*.exe")])
            if p:
                entry_tb.delete(0, "end")
                entry_tb.insert(0, p)
                save_tb_pfad()

        self.create_button(f_tb_path, text="📁", width=35, command=browse_tb).pack(side="left")
        self.create_button(f_tb_path, text="Speichern", width=80, command=save_tb_pfad, fg_color="#1f538d").pack(side="left", padx=5)
        create_tooltip(entry_tb, "Pfad zur thunderbird.exe (z.B. C:\\Program Files\\Mozilla Thunderbird\\thunderbird.exe)")

        f_mail_txt = ctk.CTkFrame(f_num_grid, fg_color="transparent")
        f_mail_txt.grid(row=7, column=0, columnspan=3, pady=(10, 10), sticky="w")

        ctk.CTkLabel(f_mail_txt, text="Standard E-Mail Text (Body):", width=180, anchor="w").pack(anchor="w", pady=(0, 2))
        entry_mail_body = ctk.CTkTextbox(f_mail_txt, width=420, height=80)
        entry_mail_body.pack(anchor="w", pady=(0, 5))
        entry_mail_body.insert("0.0", self.p_config.get("email_body", "Sehr geehrte Damen und Herren,\n\nanbei übersenden wir e-Rechnung mit der Bitte um Ausgleich."))

        ctk.CTkLabel(f_mail_txt, text="E-Mail Footer / Signatur:", width=180, anchor="w").pack(anchor="w", pady=(5, 2))
        entry_mail_footer = ctk.CTkTextbox(f_mail_txt, width=420, height=60)
        entry_mail_footer.pack(anchor="w", pady=(0, 5))
        entry_mail_footer.insert("0.0", self.p_config.get("email_footer", ""))

        def save_mail_text_config():
            self.p_config["email_body"] = entry_mail_body.get("0.0", "end").strip()
            self.p_config["email_footer"] = entry_mail_footer.get("0.0", "end").strip()
            speichere_config(self.config)
            self.show_info("Gespeichert", "E-Mail Text und Footer wurden aktualisiert.")

        self.create_button(f_mail_txt, text="E-Mail-Texte speichern", width=160, command=save_mail_text_config, fg_color="#1f538d").pack(anchor="w", pady=5)
        create_tooltip(entry_mail_body, "Der Standardtext, der beim automatischen E-Mail-Versand verwendet wird.")
        create_tooltip(entry_mail_footer, "Ihre Signatur, die automatisch unter den E-Mail-Text gesetzt wird.")

        def toggle_xrechnung_leseabschrift():
            self.p_config["xrechnung_leseabschrift"] = bool(self.chk_xrechnung_leseabschrift.get())
            speichere_config(self.config)

        def toggle_audit_reason():
            self.p_config["audit_reason_required"] = bool(self.chk_audit_reason.get())
            speichere_config(self.config)

        self.chk_xrechnung_leseabschrift = ctk.CTkCheckBox(f_num_grid, text="Bei XRechnungen standardmäßig PDF-Leseabschrift erzeugen", command=toggle_xrechnung_leseabschrift)
        self.chk_xrechnung_leseabschrift.grid(row=3, column=0, columnspan=3, pady=(15, 5), sticky="w")
        create_tooltip(self.chk_xrechnung_leseabschrift, "XRechnungen sind reine XML-Dateien.\nDiese Option erzeugt zusätzlich ein menschlich\nlesbares PDF-Dokument für Ihr Ausgangsarchiv.")
        if self.p_config.get("xrechnung_leseabschrift", True):
            self.chk_xrechnung_leseabschrift.select()
        else:
            self.chk_xrechnung_leseabschrift.deselect()

        self.chk_audit_reason = ctk.CTkCheckBox(f_num_grid, text="GoBD: Begründungszwang bei Änderung/Löschung von Rechnungen (Audit-Log)", command=toggle_audit_reason)
        self.chk_audit_reason.grid(row=4, column=0, columnspan=3, pady=(5, 5), sticky="w")
        create_tooltip(self.chk_audit_reason, "Erfordert die Eingabe eines Grundes, wenn eine Rechnung\nüberschrieben oder im Journal gelöscht wird.\nWichtig für die GoBD-Konformität.")
        if self.p_config.get("audit_reason_required", False):
            self.chk_audit_reason.select()
        else:
            self.chk_audit_reason.deselect()

        def toggle_bg_update():
            enabled = bool(self.chk_bg_update.get())
            self.config["background_update_check"] = enabled
            speichere_config(self.config)
            if enabled and hasattr(self, "schedule_background_update_check") and not getattr(self, "_bg_update_scheduled", False):
                self._bg_update_scheduled = True
                self.after(65000, self.schedule_background_update_check)

        self.chk_bg_update = ctk.CTkCheckBox(
            f_num_grid,
            text="Im Hintergrund nach Updates suchen",
            command=toggle_bg_update,
        )
        self.chk_bg_update.grid(row=8, column=0, columnspan=3, pady=(5, 5), sticky="w")
        create_tooltip(
            self.chk_bg_update,
            "Prüft frühestens 1 Minute nach Programmstart im Hintergrund, ob heute\n"
            "bereits eine Instanz im Netzwerk nach Updates gesucht hat. Wenn nein,\n"
            "wird der Updateserver geprüft und eine neuere Version nur ins\n"
            "Netzwerkverzeichnis geladen (ohne sofortige Installation).",
        )
        if self.config.get("background_update_check", False):
            self.chk_bg_update.select()
        else:
            self.chk_bg_update.deselect()

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

        self.create_button(f_base, text="💾 Pfade anlegen & speichern", command=self.save_settings, fg_color="#1f538d", hover_color="#14375d").pack(side="left", padx=(10, 0))

        ctk.CTkLabel(f_path_card, text="Aktive Pfade der aktuellen Firma (schreibgeschützt):", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 0))

        f_pfade = ctk.CTkFrame(f_path_card, fg_color="transparent")
        f_pfade.pack(fill="x", padx=15, pady=(5, 15))

        base_data_path = self.config.get("base_data_path", "")
        firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_")) if base_data_path else ""
        audit_dir = os.path.join(firm_dir, "audit") if firm_dir else "Nicht gesetzt"

        program_dir = os.path.abspath(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__))

        pfade_liste = [
            ("Programmpfad", program_dir),
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
                    self.show_error("Fehler", f"Fehler beim Öffnen:\n{e}")
            else:
                self.show_warning("Ordner fehlt", f"Dieser Ordner wurde noch nicht automatisch angelegt:\n{path_to_open}")

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
            return self.show_warning("Fehler", "Bitte einen Grundpfad angeben.")

        self.config["base_data_path"] = base_path

        firm_folder = self.p_config["profil_name"].replace(" ", "_")
        firm_dir = os.path.join(base_path, firm_folder)
        ausw_dir = os.path.join(firm_dir, "aausw")
        are_dir = os.path.join(firm_dir, "are")
        arecsv_dir = os.path.join(firm_dir, "arecsv")

        os.makedirs(ausw_dir, exist_ok=True)
        os.makedirs(are_dir, exist_ok=True)
        os.makedirs(arecsv_dir, exist_ok=True)
        reneu_dir = os.path.join(firm_dir, "reneu")
        rebearb_dir = os.path.join(firm_dir, "rebearb")
        rchn_dir = os.path.join(firm_dir, "rchn")
        einj_dir = os.path.join(firm_dir, "eausw")
        for incoming_dir in (reneu_dir, rebearb_dir, rchn_dir, einj_dir):
            os.makedirs(incoming_dir, exist_ok=True)

        self.p_config["auswertungen_ordner"] = ausw_dir
        self.p_config["ausgabe_ordner"] = are_dir
        self.p_config["eingangsordner"] = reneu_dir
        self.p_config["bearbeitete_eingangsrechnungen_ordner"] = rebearb_dir
        self.p_config["eingangsrechnungen_ordner"] = rchn_dir
        self.p_config["eingangsjournal_ordner"] = einj_dir
        self.p_config["xrechnung_leseabschrift"] = bool(self.chk_xrechnung_leseabschrift.get())
        self.p_config["audit_reason_required"] = bool(self.chk_audit_reason.get())
        dateien = ["firma.csv", "rechnung.csv", "briefbogen.pdf", "zusatz.csv", "gruss.csv", "vor_gruss.csv", "header.csv", "einleitung.csv", "kunden.csv", "produkte.csv"]

        for datei in dateien:
            key_name = datei.replace(".", "_")
            self.p_config[key_name] = os.path.join(firm_dir, datei)

        speichere_config(self.config)
        self.show_info("Gespeichert", f"Die Ordnerstruktur wurde in\n{firm_dir}\nangelegt und gespeichert!")

    def open_firma_manager(self):
        d_edit = ctk.CTkToplevel(self)
        d_edit.title("Firmendaten bearbeiten")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d_edit)
        self.center_window(d_edit, 520, 610)
        d_edit.transient(self)
        d_edit.grab_set()

        pfad_firma = self.p_config.get("firma_csv", "firma.csv")
        f_daten = lade_firma(pfad_firma)

        MAX_ABSENDER_LEN = 75

        e_name = self.create_input(d_edit, "Firma Name")
        e_name.insert(0, f_daten.get('FirmaName', ''))

        # Extra Erfassungsfeld für kompakte Absenderzeile im Briefumschlag-Sichtfenster
        f_abs = ctk.CTkFrame(d_edit, fg_color="transparent")
        f_abs.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(f_abs, text="Absender (Fenster)", width=120, anchor="w").pack(side="left")
        e_absender = ctk.CTkEntry(
            f_abs,
            placeholder_text="Optional: Kurzname für Briefumschlag-Sichtfenster (leer = Firma Name)"
        )
        e_absender.pack(side="left", fill="x", expand=True, padx=(10, 5))
        e_absender.insert(0, (f_daten.get('Absenderzeile', '') or '')[:MAX_ABSENDER_LEN])

        lbl_abs_count = ctk.CTkLabel(f_abs, text=f"0/{MAX_ABSENDER_LEN}", width=48, anchor="e", text_color="gray")
        lbl_abs_count.pack(side="right")

        def _enforce_absender_limit(_event=None):
            val = e_absender.get()
            if len(val) > MAX_ABSENDER_LEN:
                pos = e_absender.index("insert")
                e_absender.delete(0, "end")
                e_absender.insert(0, val[:MAX_ABSENDER_LEN])
                try:
                    e_absender.icursor(min(pos, MAX_ABSENDER_LEN))
                except Exception:
                    pass
                val = e_absender.get()
            lbl_abs_count.configure(
                text=f"{len(val)}/{MAX_ABSENDER_LEN}",
                text_color="#b85c00" if len(val) >= MAX_ABSENDER_LEN - 5 else "gray"
            )

        e_absender.bind("<KeyRelease>", _enforce_absender_limit)
        _enforce_absender_limit()
        create_tooltip(
            e_absender,
            "Kompakter Absendername für die kleine Adresszeile über der Empfängeranschrift\n"
            "im Briefumschlag-Sichtfenster (max. 75 Zeichen inkl. Straße, PLZ & Ort).\n"
            "Wenn leer, wird automatisch 'Firma Name' verwendet."
        )

        e_str = self.create_input(d_edit, "Straße")
        e_str.insert(0, f_daten.get('Strasse', ''))
        e_plz = self.create_input(d_edit, "PLZ")
        e_plz.insert(0, f_daten.get('PLZ', ''))
        e_ort = self.create_input(d_edit, "Ort")
        e_ort.insert(0, f_daten.get('Ort', ''))
        e_land = self.create_input(d_edit, "Land (z.B. DE)")
        e_land.insert(0, f_daten.get('Land', 'DE'))
        e_ustid = self.create_input(d_edit, "USt-Id")
        e_ustid.insert(0, f_daten.get('UStId', ''))
        e_stnr = self.create_input(d_edit, "Steuernummer")
        e_stnr.insert(0, f_daten.get('Steuernummer', ''))
        e_bank = self.create_input(d_edit, "Bank Name")
        e_bank.insert(0, f_daten.get('BankName', ''))
        e_iban = self.create_input(d_edit, "IBAN")
        e_iban.insert(0, f_daten.get('IBAN', ''))
        e_bic = self.create_input(d_edit, "BIC")
        e_bic.insert(0, f_daten.get('BIC', ''))
        e_inhaber = self.create_input(d_edit, "Kontoinhaber")
        e_inhaber.insert(0, f_daten.get('Kontoinhaber', ''))

        f_giro = ctk.CTkFrame(d_edit, fg_color="transparent")
        f_giro.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(f_giro, text="", width=120).pack(side="left")
        chk_giro = ctk.CTkCheckBox(f_giro, text="Girocode (QR-Code) auf Rechnung andrucken")
        chk_giro.pack(side="left", padx=(10, 0))
        if str(f_daten.get('Girocode', '1')).lower() in ['true', '1', 'ja', 'yes']:
            chk_giro.select()
        else:
            chk_giro.deselect()

        f_falz = ctk.CTkFrame(d_edit, fg_color="transparent")
        f_falz.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(f_falz, text="", width=120).pack(side="left")
        chk_falz = ctk.CTkCheckBox(f_falz, text="Falz- und Lochmarken (DIN Lang) andrucken")
        chk_falz.pack(side="left", padx=(10, 0))
        if str(f_daten.get('Falzmarken', '1')).lower() in ['true', '1', 'ja', 'yes']:
            chk_falz.select()
        else:
            chk_falz.deselect()

        e_mail = self.create_input(d_edit, "Email")
        e_mail.insert(0, f_daten.get('Email', ''))
        e_tel = self.create_input(d_edit, "Telefon")
        e_tel.insert(0, f_daten.get('Telefon', ''))

        def save():
            name, plz, ort, iban = e_name.get().strip(), e_plz.get().strip(), e_ort.get().strip(), e_iban.get().strip()
            ustid, stnr = e_ustid.get().strip(), e_stnr.get().strip()
            absender_kurz = e_absender.get().strip()[:MAX_ABSENDER_LEN]
            if not name or not plz or not ort or not iban or (not ustid and not stnr):
                return self.show_warning("Fehler", "Zwingend: Name, PLZ, Ort, IBAN, USt-Id ODER Steuernummer", parent=d_edit)

            speichere_firma(pfad_firma, {
                'FirmaName': name,
                'Absenderzeile': absender_kurz,
                'Strasse': e_str.get().strip(),
                'PLZ': plz,
                'Ort': ort,
                'Land': e_land.get().strip(),
                'UStId': ustid,
                'Steuernummer': stnr,
                'BankName': e_bank.get().strip(),
                'IBAN': iban,
                'BIC': e_bic.get().strip(),
                'Kontoinhaber': e_inhaber.get().strip(),
                'Girocode': '1' if chk_giro.get() else '0',
                'Falzmarken': '1' if chk_falz.get() else '0',
                'Email': e_mail.get().strip(),
                'Telefon': e_tel.get().strip()
            })
            self.show_info("Gespeichert", "Firmendaten wurden aktualisiert!", parent=d_edit)
            d_edit.destroy()

        self.create_button(d_edit, text="Speichern", command=save).pack(pady=20)

    def open_datev_manager(self):
        d_edit = ctk.CTkToplevel(self)
        d_edit.title("DATEV & Buchhaltung konfigurieren")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d_edit)
        self.center_window(d_edit, 500, 520)
        d_edit.transient(self)
        d_edit.grab_set()

        f_skr = ctk.CTkFrame(d_edit, fg_color="transparent")
        f_skr.pack(fill="x", padx=10, pady=(10, 20))
        ctk.CTkLabel(f_skr, text="Kontenrahmen:", width=120, anchor="w").pack(side="left")

        def on_skr_change(wahl):
            if self.ask_yes_no("Standardkonten laden", f"Möchten Sie die typischen DATEV-Standardkonten für {wahl} laden?\n\n(Ihre manuellen Eingaben werden überschrieben)", parent=d_edit):
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
            self.show_info("Gespeichert", "DATEV-Kontenrahmen aktualisiert!")

        self.create_button(d_edit, text="Speichern", command=save).pack(pady=20)

    def clear_profile_data(self):
        warnung = (
            "ACHTUNG: Dies löscht unwiderruflich ALLE erfassten Rechnungen, Journale und PDFs der aktiven Firma!\n"
            "Stammdaten (Firmendaten, Kunden, Produkte, Briefbogen) und Textvorlagen bleiben erhalten.\n\n"
            "Bitte geben Sie 'LEEREN' ein, um fortzufahren:"
        )
        d_pwd = ctk.CTkInputDialog(text=warnung, title="Sicherheitsabfrage")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d_pwd)
        pwd = d_pwd.get_input()
        if pwd == "LEEREN":
            try:
                rechnung_pfad = self.p_config.get("rechnung_csv", "")
                if os.path.exists(rechnung_pfad):
                    header = "Rechnungsnummer;Rechnungsdatum;Faelligkeitsdatum;KundeName;KundeStrasse;KundePLZ;KundeOrt;KundeLand;KundeEmail;KundeEndpoint;KundeEndpointScheme;KundeNr;Aktenzeichen;KundeAktenzeichen;LeistungszeitraumKopf;Ratenzahlung;PosNr;Menge;Einheit;Bezeichnung;EinzelpreisNetto;Steuersatz;Zusatztext;LeistungszeitraumPos"
                    with open(rechnung_pfad, 'w', encoding='utf-8-sig') as f:
                        f.write(header + "\n")

                self.p_config["letzte_rechnungsnummer"] = ""
                self.p_config["letzte_eingangsrechnungsnummer"] = ""
                speichere_config(self.config)

                ordner_keys = ["ausgabe_ordner", "auswertungen_ordner", "eingangsordner", "bearbeitete_eingangsrechnungen_ordner", "eingangsrechnungen_ordner", "eingangsjournal_ordner"]
                for key in ordner_keys:
                    ordner = self.p_config.get(key, "")
                    if ordner and os.path.exists(ordner):
                        for filename in os.listdir(ordner):
                            file_path = os.path.join(ordner, filename)
                            try:
                                if os.path.isdir(file_path):
                                    shutil.rmtree(file_path)
                                else:
                                    os.unlink(file_path)
                            except:
                                pass

                are_dir = self.p_config.get("ausgabe_ordner", "")
                if are_dir:
                    arecsv_dir = os.path.join(os.path.dirname(are_dir), "arecsv")
                    if os.path.exists(arecsv_dir):
                        for filename in os.listdir(arecsv_dir):
                            file_path = os.path.join(arecsv_dir, filename)
                            try:
                                if os.path.isdir(file_path):
                                    shutil.rmtree(file_path)
                                else:
                                    os.unlink(file_path)
                            except:
                                pass

                self.refresh_all_ui()
                self.show_info("Erfolg", "Alle Rechnungsdaten und Journale der Firma wurden erfolgreich geleert.")
            except Exception as e:
                self.show_error("Fehler", f"Fehler beim Leeren der Daten: {e}")
        elif pwd is not None:
            self.show_error("Fehler", "Falsche Eingabe! Vorgang abgebrochen.")

    def import_kunden_csv(self):
        pfad = filedialog.askopenfilename(title="Kunden CSV wählen", filetypes=[("CSV-Dateien", "*.csv*")])
        if not pfad:
            return
        ensure_utf8_csv(pfad)

        try:
            importierte_kunden = []
            with open(pfad, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                if not set(['Name', 'Strasse', 'PLZ_Ort', 'Land']).issubset(reader.fieldnames or []):
                    return self.show_warning("Falsches Format", "Die Kopfzeile der CSV-Datei entspricht nicht dem geforderten Format.")
                for row in reader:
                    importierte_kunden.append(row)

            if not importierte_kunden:
                return self.show_warning("Fehler", "Die Datei ist leer oder ungültig.")

            bestehende_kunden = self.kunden_liste
            aktualisiert = 0
            neu = 0

            for imp_k in importierte_kunden:
                k_nr = imp_k.get('KundeNr', '').strip()
                matched = False
                if k_nr:
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
            self.show_info("Import erfolgreich", f"Kunden importiert!\n\nNeu angelegt: {neu}\nAktualisiert (überschrieben): {aktualisiert}")
        except Exception as e:
            self.show_error("Fehler", f"Fehler beim Import: {e}")

    def import_produkte_csv(self):
        pfad = filedialog.askopenfilename(title="Produkte CSV wählen", filetypes=[("CSV-Dateien", "*.csv*")])
        if not pfad:
            return
        ensure_utf8_csv(pfad)

        try:
            importierte_produkte = []
            with open(pfad, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                if not set(['Bezeichnung', 'EinzelpreisNetto', 'Steuersatz']).issubset(reader.fieldnames or []):
                    return self.show_warning("Falsches Format", "Die Kopfzeile der CSV-Datei entspricht nicht dem geforderten Format.")
                for row in reader:
                    importierte_produkte.append(row)

            if not importierte_produkte:
                return self.show_warning("Fehler", "Die Datei ist leer oder ungültig.")

            self.produkte_liste.extend(importierte_produkte)
            speichere_alle_produkte(self.p_config.get("produkte_csv", "produkte.csv"), self.produkte_liste)
            self.show_info("Import erfolgreich", f"{len(importierte_produkte)} Produkte wurden erfolgreich angehängt!")
        except Exception as e:
            self.show_error("Fehler", f"Fehler beim Import: {e}")



