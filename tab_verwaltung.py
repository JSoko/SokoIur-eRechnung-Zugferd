
"""
tab_verwaltung.py
-----------------
Popup-Logik für die Stammdatenverwaltung (Kunden & Produkte).
"""
import csv
import os
from tkinter import filedialog
import customtkinter as ctk
from tkinter import ttk
import tkinter.messagebox as messagebox
from config import *
from utils import *
from crud import (
    lade_kunden,
    speichere_alle_kunden,
    speichere_kunde,
    loesche_kunde,
    lade_produkte,
    speichere_alle_produkte,
    speichere_produkt,
    loesche_produkt,
)


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

        self.seg_btn = ctk.CTkSegmentedButton(
            f_top,
            values=["Kunden", "Produkte"],
            variable=self.vw_mode,
            command=self.vw_switch_mode,
        )
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
        ctk.CTkEntry(
            f_left, textvariable=self.vw_search_var, placeholder_text="🔍 Suchen..."
        ).pack(fill="x", padx=10, pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", "#1f538d")])

        self.vw_tree = ttk.Treeview(f_left, columns=("Name",), show="headings")
        self.vw_tree.heading("Name", text="Eintrag")
        self.vw_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.vw_tree.bind("<<TreeviewSelect>>", self.vw_on_select)

        self.vw_form_frame = ctk.CTkScrollableFrame(self.f_right, fg_color="transparent")
        self.vw_form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        f_actions = ctk.CTkFrame(self.f_right, fg_color="transparent")
        f_actions.pack(fill="x", side="bottom", padx=10, pady=10)

        ctk.CTkButton(f_actions, text="➕ Neu", width=80, command=self.vw_clear_form).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            f_actions, text="💾 Speichern", width=120, command=self.vw_save_entry
        ).pack(side="left", padx=5)

        self.btn_vw_csv_import = ctk.CTkButton(
            f_actions,
            text="📥 CSV-Importieren",
            width=135,
            fg_color="#1f538d",
            hover_color="#14375d",
            command=self.vw_on_csv_import_click,
        )
        self.btn_vw_csv_import.pack(side="left", padx=5)

        ctk.CTkButton(
            f_actions,
            text="🗑️ Löschen",
            width=80,
            fg_color="#b30000",
            hover_color="#800000",
            command=self.vw_delete_entry,
        ).pack(side="right", padx=5)

        self.vw_entries = {}
        self.vw_switch_mode("Kunden")

    def vw_on_csv_import_click(self):
        if self.vw_mode.get() == "Produkte":
            self.vw_import_produkte_csv()
        else:
            self.vw_import_kunden_csv()

    def vw_switch_mode(self, mode):
        self.vw_search_var.set("")
        self.vw_clear_form()
        for widget in self.vw_form_frame.winfo_children():
            widget.destroy()
        self.vw_entries.clear()

        if hasattr(self, "btn_vw_csv_import") and self.btn_vw_csv_import.winfo_exists():
            self.btn_vw_csv_import.pack(side="left", padx=5)

        if mode == "Kunden":
            fields = [
                "Name",
                "Strasse",
                "PLZ_Ort",
                "Land",
                "KundeNr",
                "UStId",
                "Aktenzeichen",
                "KundeAktenzeichen",
                "Endpoint",
                "EndpointScheme",
            ]
            for field in fields:
                self.vw_entries[field] = self.create_input(self.vw_form_frame, field + ":")
        else:
            # Produkte: Menge wird ausgeblendet, Einheit und Steuersatz werden Dropdowns
            self.vw_entries["Bezeichnung"] = self.create_input(
                self.vw_form_frame, "Bezeichnung:"
            )
            self.vw_entries["Einheit"] = self.create_input(
                self.vw_form_frame,
                "Einheit:",
                is_combo=True,
                combo_values=EINHEITEN_LISTE,
            )
            self.vw_entries["EinzelpreisNetto"] = self.create_input(
                self.vw_form_frame, "Einzelpreis Netto:"
            )
            self.vw_entries["Steuersatz"] = self.create_input(
                self.vw_form_frame,
                "Steuersatz (%):",
                is_combo=True,
                combo_values=["19", "7", "0"],
            )

        self.vw_refresh_list()

    def vw_refresh_list(self):
        for item in self.vw_tree.get_children():
            self.vw_tree.delete(item)
        search_q = self.vw_search_var.get().lower()
        mode = self.vw_mode.get()
        data = self.kunden_liste if mode == "Kunden" else self.produkte_liste
        key = "Name" if mode == "Kunden" else "Bezeichnung"

        for record in data:
            val = record.get(key, "")
            if search_q in val.lower():
                self.vw_tree.insert("", "end", values=(val,), tags=(val,))

    def vw_on_select(self, event):
        selected = self.vw_tree.selection()
        if not selected:
            return
        val = self.vw_tree.item(selected[0])["values"][0]
        mode = self.vw_mode.get()
        data = self.kunden_liste if mode == "Kunden" else self.produkte_liste
        key = "Name" if mode == "Kunden" else "Bezeichnung"

        self.vw_clear_form()
        for record in data:
            if record.get(key, "") == val:
                if mode == "Kunden":
                    self.vw_selected_original_kunde = dict(record)
                else:
                    self.vw_selected_original_kunde = None
                for k, entry in self.vw_entries.items():
                    rec_val = record.get(k, "")
                    # ComboBoxen benötigen .set(), normale Textfelder .insert()
                    if isinstance(entry, ctk.CTkComboBox):
                        entry.set(rec_val)
                    else:
                        entry.insert(0, rec_val)
                break

    def vw_clear_form(self):
        self.vw_selected_original_kunde = None
        for entry in self.vw_entries.values():
            if isinstance(entry, ctk.CTkComboBox):
                entry.set("")
            else:
                entry.delete(0, "end")

    def vw_save_entry(self):
        mode = self.vw_mode.get()
        primary_key = "Name" if mode == "Kunden" else "Bezeichnung"

        if not self.vw_entries[primary_key].get().strip():
            return self.show_warning(
                "Fehler",
                f"Das Feld '{primary_key}' darf nicht leer sein.",
                parent=self.vw_popup,
            )

        new_data = {k: entry.get().strip() for k, entry in self.vw_entries.items()}

        if mode == "Kunden":
            orig = getattr(self, "vw_selected_original_kunde", None)
            speichere_kunde(self.p_config.get("kunden_csv"), new_data, original_kunde=orig)
            self.vw_selected_original_kunde = dict(new_data)
        else:
            # Menge hart auf "1" setzen, damit die Produkte-CSV nicht beschädigt wird
            new_data["Menge"] = "1"
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

        if self.ask_yes_no(
            "Löschen", f"Soll '{val}' wirklich gelöscht werden?", parent=self.vw_popup
        ):
            if mode == "Kunden":
                loesche_kunde(self.p_config.get("kunden_csv"), val)
            else:
                loesche_produkt(self.p_config.get("produkte_csv"), val)

            self.refresh_all_ui()
            self.vw_clear_form()
            # NEU: Gelöschten Eintrag sofort aus der sichtbaren Tabelle entfernen
            self.vw_refresh_list()

    def _vw_detect_encoding_and_read(self, pfad: str):
        if not pfad or not os.path.isfile(pfad):
            return None, None, "Die ausgewählte Datei existiert nicht oder ist kein gültiger Dateipfad."

        try:
            if os.path.getsize(pfad) == 0:
                return None, None, "Die Datei ist leer (0 Bytes)."
        except OSError as e:
            return None, None, f"Dateigröße konnte nicht geprüft werden: {e}"

        try:
            with open(pfad, "rb") as fb:
                raw = fb.read()
        except OSError as e:
            return None, None, f"Datei konnte nicht gelesen werden: {e}"

        if b"\x00" in raw:
            return None, None, "Die Datei enthält Null-Bytes und ist keine gültige CSV-Textdatei."

        # 1. UTF-8 (mit/ohne BOM) prüfen
        for enc in ("utf-8-sig", "utf-8"):
            try:
                text = raw.decode(enc, errors="strict")
                return text, enc, None
            except UnicodeDecodeError:
                continue

        # 2. DOS/OEM (cp850 / cp437) vs. Windows-1252 (ANSI) erkennen:
        # In cp850 sind deutsche Umlaute/ß: 0x81=ü, 0x84=ä, 0x8E=Ä, 0x94=ö, 0x99=Ö, 0x9A=Ü, 0xE1=ß
        # In cp1252 sind 0x81/0x8D/0x8F/0x90/0x9D undefiniert und 0x84/0x94 Anführungszeichen (” = 0x94)
        cp850_umlaut_bytes = {0x81, 0x84, 0x8E, 0x94, 0x99, 0x9A, 0xE1}
        cp1252_umlaut_bytes = {0xC4, 0xD6, 0xDC, 0xDF, 0xE4, 0xF6, 0xFC}

        cp850_hits = sum(1 for b in raw if b in cp850_umlaut_bytes)
        cp1252_hits = sum(1 for b in raw if b in cp1252_umlaut_bytes)

        cp1252_ok = True
        try:
            raw.decode("cp1252", errors="strict")
        except UnicodeDecodeError:
            cp1252_ok = False

        if (not cp1252_ok or cp850_hits > cp1252_hits) and cp850_hits > 0:
            try:
                return raw.decode("cp850", errors="strict"), "cp850 (DOS/OEM)", None
            except UnicodeDecodeError:
                pass

        for enc in ("cp1252", "cp850", "latin-1"):
            try:
                return raw.decode(enc, errors="strict"), enc, None
            except UnicodeDecodeError:
                continue

        return None, None, "Der Zeichensatz der Datei konnte nicht erkannt werden."

    def _vw_is_header_row(self, cols: list[str]) -> bool:
        if len(cols) != 7:
            return False
        norm = [c.strip().lower() for c in cols]
        return norm[0] in {"mitnum", "kdnr"} and norm[1:] == [
            "vorname",
            "name",
            "strasse",
            "plz",
            "ort",
            "email",
        ]

    def _vw_is_produkte_header_row(self, cols: list[str]) -> bool:
        norm = [c.strip().lower() for c in cols]
        if len(norm) == 5:
            return norm[:2] == ["bezeichnung", "menge"] and norm[3:] == ["einzelpreisnetto", "steuersatz"]
        if len(norm) == 3:
            return norm == ["bezeichnung", "einzelpreisnetto", "steuersatz"]
        return False

    def _vw_parse_produkt_row(self, cols: list[str]):
        """
        Parst eine 3- oder 5-spaltige Produktzeile.
        Rückgabe: (produkt_dict_or_None, fehlertext_or_None)
        """
        if len(cols) == 5:
            bez, menge, einheit, preis, steuer = [c.strip() for c in cols]
            menge_val = menge or "1"
            einheit_val = einheit or "C62"
        elif len(cols) == 3:
            bez, preis, steuer = [c.strip() for c in cols]
            menge_val = "1"
            einheit_val = "C62"
        else:
            return None, "Erwartet werden 3 Spalten (Bezeichnung;EinzelpreisNetto;Steuersatz) oder 5 Spalten (Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz)."

        if not bez:
            return None, "Bezeichnung fehlt."

        try:
            float(menge_val.replace(",", "."))
            float(preis.replace(",", "."))
            float(steuer.replace(",", "."))
        except ValueError:
            return None, f"Ungültiger Zahlenwert bei Artikel '{bez}' (Menge='{menge_val}', Preis='{preis}', Steuer='{steuer}')."

        return {
            "Bezeichnung": bez,
            "Menge": menge_val.replace(",", "."),
            "Einheit": einheit_val,
            "EinzelpreisNetto": preis.replace(",", "."),
            "Steuersatz": steuer.replace(",", "."),
        }, None

    def vw_import_produkte_csv(self):
        parent = self.vw_popup if hasattr(self, "vw_popup") and self.vw_popup.winfo_exists() else self

        last_dir = self.config.get("last_produkte_import_dir", "")
        if not last_dir or not os.path.isdir(last_dir):
            base_data = self.config.get("base_data_path", "")
            last_dir = (
                base_data
                if (base_data and os.path.isdir(base_data))
                else os.path.expanduser("~")
            )

        last_file = self.config.get("last_produkte_import_file", "")
        initial_file = os.path.basename(last_file) if last_file else ""

        dialog_kwargs = {
            "parent": parent,
            "title": "Produkte-CSV importieren",
            "initialdir": last_dir,
            "filetypes": [("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
        }
        if initial_file:
            dialog_kwargs["initialfile"] = initial_file

        pfad = filedialog.askopenfilename(**dialog_kwargs)
        if not pfad:
            return

        abs_pfad = os.path.abspath(pfad)
        self.config["last_produkte_import_dir"] = os.path.dirname(abs_pfad)
        self.config["last_produkte_import_file"] = os.path.basename(abs_pfad)
        try:
            speichere_config(self.config)
        except Exception:
            pass

        inhalt, enc_used, err_msg = self._vw_detect_encoding_and_read(abs_pfad)
        if err_msg or inhalt is None:
            return self.show_warning(
                "Import abgebrochen",
                f"Die Datei '{os.path.basename(abs_pfad)}' wurde nicht importiert.\n\nGrund:\n{err_msg}",
                parent=parent,
            )

        rows = [
            [cell.strip() for cell in r]
            for r in csv.reader(inhalt.splitlines(), delimiter=";")
            if any(cell.strip() for cell in r)
        ]

        if not rows:
            return self.show_warning(
                "Import abgebrochen",
                f"Die Datei '{os.path.basename(abs_pfad)}' ({enc_used}) enthält keine verwertbaren Zeilen.",
                parent=parent,
            )

        valid_col_counts = {3, 5}
        bad_rows = [i + 1 for i, r in enumerate(rows) if len(r) not in valid_col_counts]
        if len(bad_rows) == len(rows):
            return self.show_warning(
                "Import abgebrochen – Format passt nicht",
                "Mit dieser Datei können keine Produkte importiert werden.\n\n"
                "Erwartet wird eine mit Semikolon (;) getrennte CSV-Datei mit 5 Spalten:\n"
                "Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz\n"
                "oder 3 Spalten:\n"
                "Bezeichnung;EinzelpreisNetto;Steuersatz",
                parent=parent,
            )

        if bad_rows:
            return self.show_warning(
                "Import abgebrochen – Spaltenanzahl fehlerhaft",
                f"Folgende Zeile(n) enthalten weder 3 noch 5 Spalten (getrennt durch ';'):\n"
                f"Zeile(n): {', '.join(str(x) for x in bad_rows[:10])}\n\n"
                "Erwartetes Format:\n"
                "Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz\n"
                "oder\n"
                "Bezeichnung;EinzelpreisNetto;Steuersatz",
                parent=parent,
            )

        has_header = self._vw_is_produkte_header_row(rows[0])
        data_rows = rows[1:] if has_header else rows

        if not data_rows:
            return self.show_warning(
                "Import abgebrochen",
                "Die Datei enthält nur eine Beschreibungszeile und keine Produktdaten.",
                parent=parent,
            )

        parsed_produkte = []
        for idx, cols in enumerate(data_rows, start=(2 if has_header else 1)):
            prod_obj, parse_err = self._vw_parse_produkt_row(cols)
            if parse_err:
                return self.show_warning(
                    "Import abgebrochen – Fehlerhafte Produktzeile",
                    f"In Zeile {idx} ist ein Fehler aufgetreten:\n{parse_err}",
                    parent=parent,
                )
            parsed_produkte.append(prod_obj)

        produkte_pfad = self.p_config.get("produkte_csv", "produkte.csv")
        bestehende = lade_produkte(produkte_pfad)

        idx_by_bez = {}
        for idx, p in enumerate(bestehende):
            bez_key = str(p.get("Bezeichnung", "")).strip().lower()
            if bez_key and bez_key not in idx_by_bez:
                idx_by_bez[bez_key] = idx

        neu_count = 0
        aktualisiert_count = 0

        for eintrag in parsed_produkte:
            bez_key = eintrag["Bezeichnung"].strip().lower()
            if bez_key in idx_by_bez:
                bestehende[idx_by_bez[bez_key]] = eintrag
                aktualisiert_count += 1
            else:
                bestehende.append(eintrag)
                idx_by_bez[bez_key] = len(bestehende) - 1
                neu_count += 1

        try:
            speichere_alle_produkte(produkte_pfad, bestehende)
        except Exception as e:
            return self.show_error(
                "Fehler beim Speichern",
                f"Die Produktdaten konnten nicht gespeichert werden:\n{e}",
                parent=parent,
            )

        self.produkte_liste = bestehende
        self.vw_refresh_list()

        zeilen_modus = "Beschreibungszeile erkannt" if has_header else "Erste Zeile als Daten erkannt"
        self.show_info(
            "CSV-Import abgeschlossen",
            f"Datei: {os.path.basename(abs_pfad)}\n"
            f"Zeichensatz: {enc_used}\n"
            f"Modus: {zeilen_modus}\n\n"
            f"Neu angelegt: {neu_count}\n"
            f"Bestehende aktualisiert: {aktualisiert_count}",
            parent=parent,
        )

    def vw_import_kunden_csv(self):
        parent = self.vw_popup if hasattr(self, "vw_popup") and self.vw_popup.winfo_exists() else self

        last_dir = self.config.get("last_kunden_import_dir", "")
        if not last_dir or not os.path.isdir(last_dir):
            base_data = self.config.get("base_data_path", "")
            last_dir = (
                base_data
                if (base_data and os.path.isdir(base_data))
                else os.path.expanduser("~")
            )

        last_file = self.config.get("last_kunden_import_file", "")
        initial_file = os.path.basename(last_file) if last_file else ""

        dialog_kwargs = {
            "parent": parent,
            "title": "Kunden-CSV importieren",
            "initialdir": last_dir,
            "filetypes": [("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
        }
        if initial_file:
            dialog_kwargs["initialfile"] = initial_file

        pfad = filedialog.askopenfilename(**dialog_kwargs)
        if not pfad:
            return

        abs_pfad = os.path.abspath(pfad)
        self.config["last_kunden_import_dir"] = os.path.dirname(abs_pfad)
        self.config["last_kunden_import_file"] = os.path.basename(abs_pfad)
        try:
            speichere_config(self.config)
        except Exception:
            pass

        inhalt, enc_used, err_msg = self._vw_detect_encoding_and_read(abs_pfad)
        if err_msg or inhalt is None:
            return self.show_warning(
                "Import abgebrochen",
                f"Die Datei '{os.path.basename(abs_pfad)}' wurde nicht importiert.\n\nGrund:\n{err_msg}",
                parent=parent,
            )

        rows = [
            [cell.strip() for cell in r]
            for r in csv.reader(inhalt.splitlines(), delimiter=";")
            if any(cell.strip() for cell in r)
        ]

        if not rows:
            return self.show_warning(
                "Import abgebrochen",
                f"Die Datei '{os.path.basename(abs_pfad)}' ({enc_used}) enthält keine verwertbaren Zeilen.",
                parent=parent,
            )

        bad_rows = [i + 1 for i, r in enumerate(rows) if len(r) != 7]
        if len(bad_rows) == len(rows):
            return self.show_warning(
                "Import abgebrochen – Format passt nicht",
                "Mit dieser Datei kann nichts importiert werden.\n\n"
                "Erwartet wird eine mit Semikolon (;) getrennte CSV-Datei mit genau 7 Spalten:\n"
                "Mitnum;Vorname;Name;Strasse;Plz;Ort;Email\n"
                "oder\n"
                "Kdnr;Vorname;Name;Strasse;Plz;Ort;Email",
                parent=parent,
            )

        if bad_rows:
            return self.show_warning(
                "Import abgebrochen – Spaltenanzahl fehlerhaft",
                f"Folgende Zeile(n) enthalten nicht genau 7 Spalten (getrennt durch ';'):\n"
                f"Zeile(n): {', '.join(str(x) for x in bad_rows[:10])}\n\n"
                "Erwartetes Format:\n"
                "Mitnum;Vorname;Name;Strasse;Plz;Ort;Email\n"
                "oder\n"
                "Kdnr;Vorname;Name;Strasse;Plz;Ort;Email",
                parent=parent,
            )

        has_header = self._vw_is_header_row(rows[0])
        data_rows = rows[1:] if has_header else rows

        if not data_rows:
            return self.show_warning(
                "Import abgebrochen",
                "Die Datei enthält nur eine Beschreibungszeile und keine Kundendaten.",
                parent=parent,
            )

        kunden_pfad = self.p_config.get("kunden_csv", "kunden.csv")
        bestehende = lade_kunden(kunden_pfad)

        idx_by_nr = {}
        for idx, k in enumerate(bestehende):
            nr_key = str(k.get("KundeNr", "")).strip().lower()
            if nr_key and nr_key not in idx_by_nr:
                idx_by_nr[nr_key] = idx

        neu_count = 0
        ueberschrieben_count = 0
        uebersprungen_count = 0

        for cols in data_rows:
            kd_nr, vorname, nachname, strasse, plz, ort, email = [c.strip() for c in cols]

            name_komplett = f"{vorname} {nachname}".strip() if (vorname and nachname) else (nachname or vorname)
            plz_ort = f"{plz} {ort}".strip()

            if not kd_nr and not name_komplett:
                uebersprungen_count += 1
                continue

            eintrag = {
                "Name": name_komplett,
                "Strasse": strasse,
                "PLZ_Ort": plz_ort,
                "Land": "DE",
                "KundeNr": kd_nr,
                "Aktenzeichen": "",
                "KundeAktenzeichen": "",
                "Endpoint": email,
                "EndpointScheme": "",
            }

            nr_key = kd_nr.lower()
            if nr_key and nr_key in idx_by_nr:
                bestehende[idx_by_nr[nr_key]] = eintrag
                ueberschrieben_count += 1
            else:
                bestehende.append(eintrag)
                if nr_key:
                    idx_by_nr[nr_key] = len(bestehende) - 1
                neu_count += 1

        try:
            speichere_alle_kunden(kunden_pfad, bestehende)
        except Exception as e:
            return self.show_error(
                "Fehler beim Speichern",
                f"Die Kundendaten konnten nicht gespeichert werden:\n{e}",
                parent=parent,
            )

        self.kunden_liste = bestehende
        self.vw_refresh_list()

        zeilen_modus = "Beschreibungszeile erkannt" if has_header else "Erste Zeile als Daten erkannt"
        self.show_info(
            "CSV-Import abgeschlossen",
            f"Datei: {os.path.basename(abs_pfad)}\n"
            f"Zeichensatz: {enc_used}\n"
            f"Modus: {zeilen_modus}\n\n"
            f"Neu angelegt: {neu_count}\n"
            f"Bestehende überschrieben: {ueberschrieben_count}"
            + (f"\nLeere Zeilen übersprungen: {uebersprungen_count}" if uebersprungen_count else ""),
            parent=parent,
        )
