"""
tab_eingang_journal.py
----------------------
Logik und Aufbau des Reiters "Eingang" (Eingangsjournal & Verwaltung).
"""
import os
import re
from datetime import datetime
import customtkinter as ctk

from config import speichere_config
from audit import write_audit_log
from eingangsrechnung import load_all_journal_entries, create_journal_pdf, delete_journal_entry
from journal_service import (
    export_incoming_journal_csv,
    export_incoming_datev_csv,
    create_audit_log_pdf,
)
from gui_utils import create_tooltip, setup_auto_scrollbar, update_scrollable_visibility


class TabEingangJournalMixin:
    def generate_eingang_auswertung(self):
        folder = self.p_config.get("eingangsjournal_ordner", "")
        year = self.combo_eingang_jahr.get()
        month = self.combo_eingang_monat.get()

        f_daten = self._lade_firma_safe()
        firma_name = f_daten.get("FirmaName", self.p_config.get("profil_name", "Unbekannte Firma"))

        pdf_path = create_journal_pdf(folder, year, month, firma_name)
        if not pdf_path:
            zeit_str = year if month == "Alle Monate" else f"{month}.{year}"
            return self.show_info("Info", f"Für {zeit_str} wurden keine Daten gefunden.")

        try:
            os.startfile(pdf_path)
        except Exception:
            self.show_info("Fertig", f"Eingangsjournal erstellt:\n{pdf_path}")

    def _lade_firma_safe(self) -> dict:
        from crud import lade_firma
        return lade_firma(self.p_config.get("firma_csv", ""))

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

        f_btns_e1 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns_e1.pack(pady=(5, 5), fill="x", padx=10)

        btn_e_pdf = self.create_button(f_btns_e1, text="📄 Eingangsjournal als PDF", command=self.generate_eingang_auswertung, fg_color="#b85c00", hover_color="#8f4700")
        btn_e_pdf.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_e_pdf, "Erstellt eine PDF-Tabelle mit direkten, klickbaren Links\nzu den archivierten Originalbelegen.")

        btn_e_csv = self.create_button(f_btns_e1, text="📊 Eingangsjournal als CSV", command=self.generate_eingang_auswertung_csv, fg_color="#1f538d", hover_color="#14375d")
        btn_e_csv.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_e_csv, "Exportiert die Eingangsdaten im CSV-Format für Excel.")

        f_btns_e2 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns_e2.pack(pady=(5, 10), fill="x", padx=10)

        btn_e_datev = self.create_button(f_btns_e2, text="📈 DATEV-Export erzeugen", command=self.generate_eingang_auswertung_datev, fg_color="#107C41", hover_color="#0b5c30")
        btn_e_datev.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_e_datev, "Erstellt eine spezielle DATEV-ASCII-Datei für den Steuerberater.\nBucht automatisch auf die Vorsteuer-Aufwandskonten.")

        btn_e_audit = self.create_button(f_btns_e2, text="🛡️ Audit-Log PDF", command=lambda: self.generate_audit_pdf("Eingang"), fg_color="#333", hover_color="#555")
        btn_e_audit.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_e_audit, "Erstellt das Revisions-Protokoll (GoBD Audit-Log)\nder Eingangsrechnungen als PDF-Datei für das Jahr.")

        ctk.CTkLabel(
            f,
            text="Die Position „Datei öffnen“ im erzeugten PDF ist mit der archivierten Originalrechnung verlinkt. Die Funktion hängt vom verwendeten PDF-Viewer ab.",
            wraplength=720, justify="center", text_color="gray", font=("Helvetica", 11)
        ).pack(padx=15, pady=(0, 8))

        f_list = ctk.CTkFrame(self.tab_eingang)
        f_list.pack(pady=(5, 15), padx=20, fill="both", expand=True)

        f_search = ctk.CTkFrame(f_list, fg_color="transparent")
        f_search.pack(fill="x", padx=12, pady=(10, 5))
        ctk.CTkLabel(f_search, text="🔍 Journal durchsuchen:", font=("Helvetica", 13, "bold")).pack(side="left")
        self.entry_eingang_search = ctk.CTkEntry(
            f_search, placeholder_text="ER-Nr., Lieferant, externe RE-Nr., Konto, Datum oder Betrag..."
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
        setup_auto_scrollbar(self.eingang_journal_scroll)
        self.refresh_eingang_journal_ui()

    def refresh_eingang_journal_ui(self):
        if not hasattr(self, "eingang_journal_scroll") or not self.eingang_journal_scroll.winfo_exists():
            return

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
                    r.get("Konto", ""),
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
            update_scrollable_visibility(self.eingang_journal_scroll)
            return

        btn_size = 34

        for rec in filtered[:150]:
            row = ctk.CTkFrame(self.eingang_journal_scroll)
            row.pack(fill="x", pady=2, padx=4)
            er_nr = rec.get("Interne ER-Nr.", "")
            r_dat = rec.get("Rechnungsdatum", "")
            lief = rec.get("Lieferant", "")
            ext_nr = rec.get("Externe Rechnungsnummer", "")
            konto = rec.get("Konto", "").strip()
            brutto = rec.get("Brutto", "0,00")
            fmt = rec.get("Format", "")
            arch = rec.get("Archivdatei", "")

            act_box = ctk.CTkFrame(row, fg_color="transparent")
            act_box.pack(side="left", padx=(6, 4), pady=3)

            btn_storno = self.create_button(
                act_box, text="🗑", width=btn_size, height=btn_size,
                fg_color="#b30000", hover_color="#800000",
                command=lambda r_obj=rec: self.delete_incoming_entry_ui(r_obj)
            )
            btn_storno.pack(side="left", padx=2)
            create_tooltip(
                btn_storno,
                f"Eingangsrechnung {er_nr} stornieren / aus dem Journal löschen\n"
                f"Lieferant: {lief} | Externe RE-Nr.: {ext_nr} | Konto: {konto or '-'} | Brutto: {brutto} €\n"
                f"Entfernt auf Wunsch auch die Archivkopien, damit der Beleg neu erfasst werden kann."
            )

            if arch and os.path.isfile(arch):
                begleit_pdf = os.path.join(os.path.dirname(arch), f"{er_nr}_Begleit.pdf")
                open_fn = self._open_file_external if hasattr(self, "_open_file_external") else os.startfile

                if fmt == "XRechnung" and os.path.isfile(begleit_pdf):
                    btn_xml = self.create_button(
                        act_box, text="👁", width=btn_size, height=btn_size,
                        fg_color="#555", hover_color="#777",
                        command=lambda p=arch: open_fn(p)
                    )
                    btn_xml.pack(side="left", padx=2)
                    create_tooltip(
                        btn_xml,
                        f"Archivierte XRechnungs-XML-Datei zu {er_nr} öffnen\n"
                        f"Lieferant: {lief} | Externe RE-Nr.: {ext_nr}\n"
                        f"Datei: {os.path.basename(arch)}"
                    )

                    btn_begleit = self.create_button(
                        act_box, text="📄", width=btn_size, height=btn_size,
                        fg_color="#6b4c9a", hover_color="#52387a",
                        command=lambda p=begleit_pdf: open_fn(p)
                    )
                    btn_begleit.pack(side="left", padx=2)
                    create_tooltip(
                        btn_begleit,
                        f"Zugehöriges Begleit-PDF zur XRechnung {er_nr} öffnen\n"
                        f"Datei: {os.path.basename(begleit_pdf)}\n"
                        f"Hinweis: Rechtlich maßgeblich ist die XRechnungs-XML-Datei."
                    )
                else:
                    btn_beleg = self.create_button(
                        act_box, text="👁", width=btn_size, height=btn_size,
                        fg_color="#555", hover_color="#777",
                        command=lambda p=arch: open_fn(p)
                    )
                    btn_beleg.pack(side="left", padx=2)
                    create_tooltip(
                        btn_beleg,
                        f"Archivierten Beleg zu Eingangsrechnung {er_nr} öffnen\n"
                        f"Lieferant: {lief} | Externe RE-Nr.: {ext_nr} | Format: {fmt or 'Beleg'}\n"
                        f"Datei: {os.path.basename(arch)}"
                    )

            konto_info = f" | Konto: {konto}" if konto else ""
            txt = f"[{er_nr}] {r_dat} | {lief[:28]} | RE: {ext_nr}{konto_info} | Brutto: {brutto} € ({fmt})"
            lbl = ctk.CTkLabel(row, text=txt, anchor="w")
            lbl.pack(side="left", padx=6, pady=4, fill="x", expand=True)

        update_scrollable_visibility(self.eingang_journal_scroll)

    def delete_incoming_entry_ui(self, rec):
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
        if not self.ask_yes_no("Eingangsrechnung stornieren / löschen", msg, default="no"):
            return

        audit_bemerkung = ""
        if self.p_config.get("audit_reason_required", False):
            d_audit = ctk.CTkInputDialog(
                text=f"Bitte geben Sie den Grund für die Löschung/Storno von ER-Nr. '{er_nr}' an:",
                title="GoBD: Begründung erforderlich"
            )
            audit_bemerkung = d_audit.get_input()
            if not audit_bemerkung:
                return self.show_warning("Abbruch", "Löschen ohne Begründung wurde abgebrochen.")

        ok, res_msg = delete_journal_entry(
            self.p_config.get("eingangsjournal_ordner", ""),
            er_nr,
            delete_archive_files=True,
            rebearb_base_folder=self.p_config.get("bearbeitete_eingangsrechnungen_ordner", ""),
        )
        if ok:
            last_nr = self.p_config.get("letzte_eingangsrechnungsnummer", "").strip().upper()
            if last_nr == er_nr.strip().upper():
                m = re.match(r"^(ER\d{2})(\d+)$", last_nr)
                if m:
                    width = len(m.group(2))
                    num = int(m.group(2))
                    prev_nr = f"{m.group(1)}{num-1:0{width}d}" if num > 1 else ""
                    self.p_config["letzte_eingangsrechnungsnummer"] = prev_nr
                    speichere_config(self.config)
                    if hasattr(self, "lbl_letzte_er_nr"):
                        self.lbl_letzte_er_nr.configure(text=prev_nr or "Noch keine")

            self.refresh_eingang_journal_ui()
            if hasattr(self, "refresh_incoming_list"):
                self.refresh_incoming_list()
            base_data_path = self.config.get("base_data_path", "")
            if base_data_path:
                firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_"))
                write_audit_log(firm_dir, "Eingang", "Gelöscht", er_nr, audit_bemerkung, "GUI")
            self.show_info("Gelöscht", res_msg)
        else:
            self.show_error("Fehler", res_msg)

    def generate_eingang_auswertung_csv(self):
        folder = self.p_config.get("eingangsjournal_ordner", "")
        year = self.combo_eingang_jahr.get()
        month = self.combo_eingang_monat.get()
        csv_export_pfad, err = export_incoming_journal_csv(folder, year, month)
        if err:
            return self.show_info("Info", err)
        try:
            os.startfile(csv_export_pfad)
        except Exception:
            self.show_info("Fertig", f"CSV erstellt: {csv_export_pfad}")

    def generate_eingang_auswertung_datev(self):
        if hasattr(self, "license_mgr"):
            self.license_mgr.record_pro_feature_use("DATEV-Export (Eingang)")
        folder = self.p_config.get("eingangsjournal_ordner", "")
        year = self.combo_eingang_jahr.get()
        month = self.combo_eingang_monat.get()
        csv_export_pfad, err = export_incoming_datev_csv(folder, year, month, self.p_config)
        if err:
            return self.show_info("Info", err)
        try:
            os.startfile(csv_export_pfad)
        except Exception:
            self.show_info("Fertig", f"DATEV-Export erstellt: {csv_export_pfad}")

    def generate_audit_pdf(self, bereich):
        if hasattr(self, "license_mgr"):
            self.license_mgr.record_pro_feature_use(f"GoBD Audit-Log PDF ({bereich})")
        base_data_path = self.config.get("base_data_path", "")
        jahr = self.combo_ausw_jahr.get() if bereich == "Ausgang" else self.combo_eingang_jahr.get()
        firma_name = self.p_config.get("profil_name", "Unbekannte Firma")
        try:
            pdf_pfad, err = create_audit_log_pdf(base_data_path, firma_name, bereich, jahr)
            if err:
                return self.show_info("Info", err)
            try:
                os.startfile(pdf_pfad)
            except Exception:
                self.show_info("Fertig", f"Audit-Log PDF erstellt:\n{pdf_pfad}")
        except PermissionError:
            self.show_error("Zugriff verweigert", "Das PDF ist in einem anderen Programm geöffnet. Bitte schließen.")
        except Exception as e:
            self.show_error("Fehler", f"Ein Fehler ist aufgetreten:\n{str(e)}")
