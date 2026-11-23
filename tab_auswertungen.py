"""
tab_auswertungen.py
-------------------
Logik und Aufbau der Reiter "Ausgang" und "Eingang" (Journale und Auswertungen).
"""
import os
import re
import csv
from datetime import datetime
import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

from config import *
from utils import *
from crud import *
from audit import write_audit_log
from gui_utils import create_tooltip, setup_auto_scrollbar, update_scrollable_visibility


class TabAuswertungenMixin:

    def generate_eingang_auswertung(self):
        folder = self.p_config.get("eingangsjournal_ordner", "")
        year = self.combo_eingang_jahr.get()
        month = self.combo_eingang_monat.get()

        # Firmennamen für den PDF-Kopf auslesen
        f_daten = lade_firma(self.p_config.get('firma_csv', ''))
        firma_name = f_daten.get('FirmaName', self.p_config.get("profil_name", "Unbekannte Firma"))

        from eingangsrechnung import create_journal_pdf

        # PDF generieren lassen
        pdf_path = create_journal_pdf(folder, year, month, firma_name)

        if not pdf_path:
            zeit_str = year if month == "Alle Monate" else f"{month}.{year}"
            return self.show_info("Info", f"Für {zeit_str} wurden keine Daten gefunden.")

        # PDF sofort öffnen
        try:
            os.startfile(pdf_path)
        except Exception:
            self.show_info("Fertig", f"Eingangsjournal erstellt:\n{pdf_path}")

    def build_ausgang_tab(self):
        f = ctk.CTkFrame(self.tab_ausgang)
        f.pack(pady=30, padx=20, fill="x")

        ctk.CTkLabel(f, text="Ausgangsrechnungen (Journal)", font=("Helvetica", 16, "bold")).pack(pady=10)

        f_ord = ctk.CTkFrame(f, fg_color="transparent")
        f_ord.pack(pady=(10, 5), fill="x", padx=10)
        ctk.CTkLabel(f_ord, text="Journal-Ordner:", width=150).pack(side="left")

        self.entry_ausw_ordner = ctk.CTkEntry(f_ord, width=300)
        self.entry_ausw_ordner.pack(side="left", padx=10, expand=True, fill="x")
        self.entry_ausw_ordner.insert(0, self.p_config.get("auswertungen_ordner", "aausw"))

        self.create_button(f_ord, text="📂", width=40, command=lambda: self.browse_path_for_entry(self.entry_ausw_ordner, is_dir=True, on_change=self.update_ausw_jahre)).pack(side="left")
        self.entry_ausw_ordner.bind('<FocusOut>', lambda e: self.update_ausw_jahre())

        f_zeit = ctk.CTkFrame(f, fg_color="transparent")
        f_zeit.pack(pady=5, fill="x", padx=10)
        ctk.CTkLabel(f_zeit, text="Zeitraum (Monat / Jahr):", width=150).pack(side="left")

        self.combo_ausw_monat = ctk.CTkComboBox(f_zeit, values=["Alle Monate"] + [f"{i:02d}" for i in range(1, 13)], width=120)
        self.combo_ausw_monat.pack(side="left", padx=(10, 5))
        self.combo_ausw_monat.set(datetime.now().strftime("%m"))

        self.combo_ausw_jahr = ctk.CTkComboBox(f_zeit, values=[], width=120)
        self.combo_ausw_jahr.pack(side="left", padx=5)

        # Zeile 1: PDF und CSV
        f_btns1 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns1.pack(pady=(20, 5), fill="x", padx=10)

        btn_a_pdf = self.create_button(f_btns1, text="📄 Journal als PDF erzeugen & öffnen", command=self.generate_auswertung, fg_color="#b85c00", hover_color="#8f4700")
        btn_a_pdf.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_a_pdf, "Erstellt eine übersichtliche PDF-Tabelle Ihrer Ausgangsrechnungen\nfür die eigenen Akten oder den Druck.")

        btn_a_csv = self.create_button(f_btns1, text="📊 Journal als CSV exportieren & öffnen", command=self.generate_auswertung_csv, fg_color="#1f538d", hover_color="#14375d")
        btn_a_csv.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_a_csv, "Exportiert die Daten im CSV-Format, ideal für die weitere\nVerarbeitung in Microsoft Excel.")

        # Zeile 2: DATEV und Audit
        f_btns2 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns2.pack(pady=(5, 20), fill="x", padx=10)

        btn_a_datev = self.create_button(f_btns2, text="📈 DATEV-Export erzeugen", command=self.generate_auswertung_datev, fg_color="#107C41", hover_color="#0b5c30")
        btn_a_datev.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_a_datev, "Erstellt eine spezielle DATEV-ASCII-Datei für den Steuerberater.\nNimmt automatisch das nötige Steuer-Splitting vor.")

        btn_a_audit = self.create_button(f_btns2, text="🛡️ Audit-Log PDF", command=lambda: self.generate_audit_pdf("Ausgang"), fg_color="#333", hover_color="#555")
        btn_a_audit.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_a_audit, "Erstellt das Revisions-Protokoll (GoBD Audit-Log)\nder Ausgangsrechnungen als PDF-Datei für das Jahr.")

        f_btns3 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns3.pack(pady=(5, 20), fill="x", padx=10)

        btn_dash = self.create_button(f_btns3, text="📈 Visuelles Business-Dashboard öffnen", command=self.open_dashboard_popup, fg_color="#1f538d", hover_color="#14375d")
        btn_dash.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_dash, "Öffnet ein interaktives Grafik-Dashboard mit monatlichem Umsatzverlauf,\nTop-5-Kunden und einer Gegenüberstellung von Umsatzsteuer und Vorsteuer.")

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

        # Zeile 1: PDF und CSV
        f_btns_e1 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns_e1.pack(pady=(5, 5), fill="x", padx=10)

        btn_e_pdf = self.create_button(f_btns_e1, text="📄 Eingangsjournal als PDF", command=self.generate_eingang_auswertung, fg_color="#b85c00", hover_color="#8f4700")
        btn_e_pdf.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_e_pdf, "Erstellt eine PDF-Tabelle mit direkten, klickbaren Links\nzu den archivierten Originalbelegen.")

        btn_e_csv = self.create_button(f_btns_e1, text="📊 Eingangsjournal als CSV", command=self.generate_eingang_auswertung_csv, fg_color="#1f538d", hover_color="#14375d")
        btn_e_csv.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_e_csv, "Exportiert die Eingangsdaten im CSV-Format für Excel.")

        # Zeile 2: DATEV und Audit
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

        # --- Such- und Storno-/Löschbereich für bereits erfasste Eingangsrechnungen ---
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

            # Quadratische Aktionsbuttons (34x34) links am Anfang der Zeile,
            # damit sie bei langem Text oder kleinem Fenster nie verdeckt werden.
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
        if not self.ask_yes_no("Eingangsrechnung stornieren / löschen", msg, default="no"):
            return
        audit_bemerkung = ""
        if self.p_config.get("audit_reason_required", False):
            d_audit = ctk.CTkInputDialog(text=f"Bitte geben Sie den Grund für die Löschung/Storno von ER-Nr. '{er_nr}' an:", title="GoBD: Begründung erforderlich")
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

    def update_ausw_jahre(self):
        if not hasattr(self, 'entry_ausw_ordner'):
            return
        ordner = self.entry_ausw_ordner.get().strip()
        jahre = set()
        if os.path.exists(ordner):
            for d in os.listdir(ordner):
                if os.path.isdir(os.path.join(ordner, d)) and re.match(r'^\d{4}$', d):
                    jahre.add(d)
            for f in os.listdir(ordner):
                m = re.match(r'^re(\d{4})\d{2}\.csv$', f.lower())
                if m:
                    jahre.add(m.group(1))
        jahre_liste = sorted(list(jahre), reverse=True) if jahre else [datetime.now().strftime("%Y")]
        self.combo_ausw_jahr.configure(values=jahre_liste)
        if self.combo_ausw_jahr.get() not in jahre_liste:
            self.combo_ausw_jahr.set(jahre_liste[0])

    def browse_path_for_entry(self, entry_widget, is_dir=False, on_change=None):
        path = filedialog.askdirectory() if is_dir else filedialog.askopenfilename()
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)
            if on_change:
                on_change()

    def generate_auswertung(self):
        ordner = self.entry_ausw_ordner.get().strip()
        jahr = self.combo_ausw_jahr.get()
        monat = self.combo_ausw_monat.get()
        if not os.path.exists(ordner):
            return self.show_warning("Fehler", "Der Auswertungs-Ordner existiert nicht.")

        such_muster = [f"re{jahr}{m:02d}.csv" for m in range(1, 13)] if monat == "Alle Monate" else [f"re{jahr}{monat}.csv"]
        zeit_str = f"{jahr}" if monat == "Alle Monate" else f"{monat}.{jahr}"

        gefundene = []
        for datei in such_muster:
            pfad = os.path.join(ordner, jahr, datei) if os.path.exists(os.path.join(ordner, jahr, datei)) else os.path.join(ordner, datei)
            if os.path.exists(pfad):
                with open(pfad, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    if not reader.fieldnames:
                        continue
                    for row in reader:
                        gefundene.append(row)

        if not gefundene:
            return self.show_info("Info", f"Für {zeit_str} wurden keine Daten gefunden.")

        firma_name = lade_firma(self.p_config.get('firma_csv', 'firma.csv')).get('FirmaName', 'Unbekannte Firma')
        jahr_ordner = os.path.join(ordner, jahr)
        os.makedirs(jahr_ordner, exist_ok=True)
        pdf_pfad = os.path.join(jahr_ordner, f"Journal_{zeit_str.replace('.', '_')}.pdf")

        try:
            c_dummy = canvas.Canvas(BytesIO(), pagesize=landscape(A4))
            breite, hoehe = landscape(A4)

            def render_journal(c_obj, is_final=False, total_pages=1):
                page_num = 1

                def draw_header():
                    c_obj.setFont("Helvetica-Bold", 16)
                    c_obj.drawString(40, hoehe - 50, f"Rechnungsjournal - {zeit_str} - {firma_name}")
                    c_obj.setFont("Helvetica-Bold", 10)
                    c_obj.drawString(40, hoehe - 80, "Datum")
                    c_obj.drawString(100, hoehe - 80, "Rechnungs-Nr.")
                    c_obj.drawString(220, hoehe - 80, "Empfänger")
                    c_obj.drawRightString(500, hoehe - 80, "Netto")
                    c_obj.drawRightString(580, hoehe - 80, "19% USt.")
                    c_obj.drawRightString(660, hoehe - 80, "7% USt.")
                    c_obj.drawRightString(740, hoehe - 80, "0% USt.")
                    c_obj.drawRightString(820, hoehe - 80, "Brutto")
                    c_obj.line(40, hoehe - 85, 820, hoehe - 85)
                    return hoehe - 105

                def draw_footer():
                    c_obj.setFont("Helvetica", 9)
                    c_obj.drawString(40, 20, f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr")
                    if total_pages > 1:
                        c_obj.drawRightString(820, 20, f"Seite {page_num} / {total_pages}")

                y = draw_header()
                if is_final:
                    draw_footer()
                c_obj.setFont("Helvetica", 10)

                sum_n = sum_19 = sum_7 = sum_0 = sum_b = 0.0
                for r in gefundene:
                    if y < 60:
                        c_obj.showPage()
                        page_num += 1
                        y = draw_header()
                        if is_final:
                            draw_footer()
                        c_obj.setFont("Helvetica", 10)

                    n = safe_float(r.get('Netto', 0))
                    m19 = safe_float(r.get('MwSt_19', 0))
                    m7 = safe_float(r.get('MwSt_7', 0))
                    m0 = safe_float(r.get('MwSt_0', 0))
                    b = safe_float(r.get('Brutto', 0))
                    sum_n += n
                    sum_19 += m19
                    sum_7 += m7
                    sum_0 += m0
                    sum_b += b

                    c_obj.drawString(40, y, str(r.get('Datum', '')))
                    c_obj.drawString(100, y, str(r.get('Rechnungsnummer', '')))
                    empf = str(r.get('Empfaenger', ''))
                    c_obj.drawString(220, y, empf[:22] + "..." if len(empf) > 25 else empf)
                    c_obj.drawRightString(500, y, f_curr(n))
                    c_obj.drawRightString(580, y, f_curr(m19))
                    c_obj.drawRightString(660, y, f_curr(m7))
                    c_obj.drawRightString(740, y, f_curr(m0))
                    c_obj.drawRightString(820, y, f_curr(b))
                    y -= 15

                c_obj.line(40, y + 10, 820, y + 10)
                y -= 10
                c_obj.setFont("Helvetica-Bold", 10)
                c_obj.drawString(40, y, "GESAMTSUMMEN:")
                c_obj.drawRightString(500, y, f_curr(sum_n))
                c_obj.drawRightString(580, y, f_curr(sum_19))
                c_obj.drawRightString(660, y, f_curr(sum_7))
                c_obj.drawRightString(740, y, f_curr(sum_0))
                c_obj.drawRightString(820, y, f_curr(sum_b))
                return page_num

            t_pages = render_journal(c_dummy)
            c = canvas.Canvas(pdf_pfad, pagesize=landscape(A4))
            render_journal(c, is_final=True, total_pages=t_pages)
            c.save()

            try:
                os.startfile(pdf_pfad)
            except Exception:
                self.show_info("Fertig", f"Journal erfolgreich erstellt unter:\n{pdf_pfad}")

        except PermissionError:
            self.show_error("Zugriff verweigert", f"Das PDF konnte nicht überschrieben werden, da es bereits in einem anderen Programm (z. B. Acrobat Reader) geöffnet ist:\n\n{pdf_pfad}\n\nBitte schließen Sie das PDF-Dokument und versuchen Sie es erneut.")
        except Exception as e:
            self.show_error("Fehler", f"Ein technischer Fehler ist aufgetreten:\n{str(e)}")

    def generate_auswertung_csv(self):
        ordner = self.entry_ausw_ordner.get().strip()
        jahr = self.combo_ausw_jahr.get()
        monat = self.combo_ausw_monat.get()
        if not os.path.exists(ordner):
            return self.show_warning("Fehler", "Der Auswertungs-Ordner existiert nicht.")

        such_muster = [f"re{jahr}{m:02d}.csv" for m in range(1, 13)] if monat == "Alle Monate" else [f"re{jahr}{monat}.csv"]
        zeit_str = f"{jahr}" if monat == "Alle Monate" else f"{monat}.{jahr}"

        gefundene = []
        header = ["Rechnungsnummer", "Datum", "Empfaenger", "Netto", "MwSt_19", "MwSt_7", "MwSt_0", "Brutto"]

        for datei in such_muster:
            pfad = os.path.join(ordner, jahr, datei) if os.path.exists(os.path.join(ordner, jahr, datei)) else os.path.join(ordner, datei)
            if os.path.exists(pfad):
                with open(pfad, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    if reader.fieldnames:
                        header = reader.fieldnames
                    for row in reader:
                        gefundene.append(row)

        if not gefundene:
            return self.show_info("Info", f"Für {zeit_str} wurden keine Daten gefunden.")

        jahr_ordner = os.path.join(ordner, jahr)
        os.makedirs(jahr_ordner, exist_ok=True)
        csv_export_pfad = os.path.join(jahr_ordner, f"Journal_Export_{zeit_str.replace('.', '_')}.csv")

        with open(csv_export_pfad, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=header, delimiter=';')
            writer.writeheader()
            writer.writerows(gefundene)

        try:
            os.startfile(csv_export_pfad)
        except Exception:
            self.show_info("Fertig", f"CSV erstellt: {csv_export_pfad}")

    def generate_eingang_auswertung_csv(self):
        folder = self.p_config.get("eingangsjournal_ordner", "")
        year = self.combo_eingang_jahr.get()
        month = self.combo_eingang_monat.get()

        targets = [f"er{year}{m:02d}.csv" for m in range(1, 13)] if month == "Alle Monate" else [f"er{year}{month}.csv"]
        zeit_str = year if month == "Alle Monate" else f"{month}.{year}"

        gefundene = []
        header = []
        for fname in targets:
            p1 = os.path.join(folder, year, fname)
            p2 = os.path.join(folder, fname)
            pfad = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
            if pfad:
                with open(pfad, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    if reader.fieldnames and not header:
                        header = reader.fieldnames
                    for row in reader:
                        gefundene.append(row)

        if not gefundene:
            return self.show_info("Info", f"Für {zeit_str} wurden keine Daten gefunden.")

        jahr_ordner = os.path.join(folder, year)
        os.makedirs(jahr_ordner, exist_ok=True)
        csv_export_pfad = os.path.join(jahr_ordner, f"Eingangsjournal_Export_{zeit_str.replace('.', '_')}.csv")

        with open(csv_export_pfad, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=header, delimiter=';')
            writer.writeheader()
            writer.writerows(gefundene)

        try:
            os.startfile(csv_export_pfad)
        except Exception:
            self.show_info("Fertig", f"CSV erstellt: {csv_export_pfad}")

    def generate_auswertung_datev(self):
        ordner = self.entry_ausw_ordner.get().strip()
        jahr = self.combo_ausw_jahr.get()
        monat = self.combo_ausw_monat.get()
        if not os.path.exists(ordner):
            return self.show_warning("Fehler", "Der Auswertungs-Ordner existiert nicht.")

        such_muster = [f"re{jahr}{m:02d}.csv" for m in range(1, 13)] if monat == "Alle Monate" else [f"re{jahr}{monat}.csv"]
        zeit_str = f"{jahr}" if monat == "Alle Monate" else f"{monat}.{jahr}"

        gefundene = []
        for datei in such_muster:
            pfad = os.path.join(ordner, jahr, datei) if os.path.exists(os.path.join(ordner, jahr, datei)) else os.path.join(ordner, datei)
            if os.path.exists(pfad):
                with open(pfad, 'r', encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f, delimiter=';'):
                        gefundene.append(row)

        if not gefundene:
            return self.show_info("Info", f"Für {zeit_str} wurden keine Daten gefunden.")

        jahr_ordner = os.path.join(ordner, jahr)
        os.makedirs(jahr_ordner, exist_ok=True)
        csv_export_pfad = os.path.join(jahr_ordner, f"DATEV_Ausgang_{zeit_str.replace('.', '_')}.csv")

        # DATEV ASCII Header
        header = ["Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "Konto", "Gegenkonto (BU-Schlüssel)", "Belegdatum", "Belegfeld 1", "Buchungstext"]

        with open(csv_export_pfad, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(header)

            for r in gefundene:
                netto = safe_float(r.get('Netto', 0))
                mwst19 = safe_float(r.get('MwSt_19', 0))
                mwst7 = safe_float(r.get('MwSt_7', 0))

                # Rückrechnung der Einzel-Bruttobeträge pro Steuersatz
                netto_19 = round(mwst19 / 0.19, 2) if mwst19 else 0.0
                brutto_19 = netto_19 + mwst19

                netto_7 = round(mwst7 / 0.07, 2) if mwst7 else 0.0
                brutto_7 = netto_7 + mwst7

                netto_0 = round(netto - netto_19 - netto_7, 2)
                brutto_0 = netto_0

                date_str = r.get('Datum', '')
                date_datev = date_str[:2] + date_str[3:5] if len(date_str) >= 5 else ""
                beleg_nr = r.get('Rechnungsnummer', '')[:36]
                buchungstext = r.get('Empfaenger', '')[:60]
                debitor = self.p_config.get("datev_debitor", "10000")

                # Zeilen schreiben (S/H = H, da Erlöskonto im Haben bebucht wird)
                if brutto_19 > 0:
                    writer.writerow([f"{brutto_19:.2f}".replace('.', ','), "H", self.p_config.get("datev_erloese_19", "8400"), debitor, date_datev, beleg_nr, buchungstext])
                if brutto_7 > 0:
                    writer.writerow([f"{brutto_7:.2f}".replace('.', ','), "H", self.p_config.get("datev_erloese_7", "8300"), debitor, date_datev, beleg_nr, buchungstext])
                if brutto_0 > 0:
                    writer.writerow([f"{brutto_0:.2f}".replace('.', ','), "H", self.p_config.get("datev_erloese_0", "8200"), debitor, date_datev, beleg_nr, buchungstext])

        try:
            os.startfile(csv_export_pfad)
        except Exception:
            self.show_info("Fertig", f"DATEV-Export erstellt: {csv_export_pfad}")

    def generate_eingang_auswertung_datev(self):
        from eingangsrechnung import extract_account_number

        folder = self.p_config.get("eingangsjournal_ordner", "")
        year = self.combo_eingang_jahr.get()
        month = self.combo_eingang_monat.get()

        targets = [f"er{year}{m:02d}.csv" for m in range(1, 13)] if month == "Alle Monate" else [f"er{year}{month}.csv"]
        zeit_str = year if month == "Alle Monate" else f"{month}.{year}"

        gefundene = []
        for fname in targets:
            p1 = os.path.join(folder, year, fname)
            p2 = os.path.join(folder, fname)
            pfad = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
            if pfad:
                with open(pfad, 'r', encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f, delimiter=';'):
                        gefundene.append(row)

        if not gefundene:
            return self.show_info("Info", f"Für {zeit_str} wurden keine Daten gefunden.")

        jahr_ordner = os.path.join(folder, year)
        os.makedirs(jahr_ordner, exist_ok=True)
        csv_export_pfad = os.path.join(jahr_ordner, f"DATEV_Eingang_{zeit_str.replace('.', '_')}.csv")

        header = ["Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "Konto", "Gegenkonto (BU-Schlüssel)", "Belegdatum", "Belegfeld 1", "Buchungstext"]

        with open(csv_export_pfad, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(header)

            for r in gefundene:
                netto = safe_float(r.get('Netto', 0))
                mwst19 = safe_float(r.get('MwSt_19', 0))
                mwst7 = safe_float(r.get('MwSt_7', 0))

                netto_19 = round(mwst19 / 0.19, 2) if mwst19 else 0.0
                brutto_19 = netto_19 + mwst19

                netto_7 = round(mwst7 / 0.07, 2) if mwst7 else 0.0
                brutto_7 = netto_7 + mwst7

                netto_0 = round(netto - netto_19 - netto_7, 2)
                brutto_0 = netto_0

                date_str = r.get('Rechnungsdatum', '')
                date_datev = date_str[:2] + date_str[3:5] if len(date_str) >= 5 else ""
                beleg_nr = r.get('Externe Rechnungsnummer', '')[:36]
                buchungstext = r.get('Lieferant', '')[:60]
                kreditor = self.p_config.get("datev_kreditor", "70000")
                erfasstes_konto = extract_account_number(r.get('Konto', ''))

                # Zeilen schreiben (S/H = S, da Aufwandskonto im Soll bebucht wird)
                if brutto_19 > 0:
                    konto_19 = erfasstes_konto or self.p_config.get("datev_aufwand_19", "3400")
                    writer.writerow([f"{brutto_19:.2f}".replace('.', ','), "S", konto_19, kreditor, date_datev, beleg_nr, buchungstext])
                if brutto_7 > 0:
                    konto_7 = erfasstes_konto or self.p_config.get("datev_aufwand_7", "3300")
                    writer.writerow([f"{brutto_7:.2f}".replace('.', ','), "S", konto_7, kreditor, date_datev, beleg_nr, buchungstext])
                if brutto_0 > 0:
                    konto_0 = erfasstes_konto or self.p_config.get("datev_aufwand_0", "3200")
                    writer.writerow([f"{brutto_0:.2f}".replace('.', ','), "S", konto_0, kreditor, date_datev, beleg_nr, buchungstext])

        try:
            os.startfile(csv_export_pfad)
        except Exception:
            self.show_info("Fertig", f"DATEV-Export erstellt: {csv_export_pfad}")

    def generate_audit_pdf(self, bereich):
        base_data_path = self.config.get("base_data_path", "")
        if not base_data_path:
            return self.show_warning("Fehler", "Kein Daten-Grundpfad definiert.")

        firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_"))

        if bereich == "Ausgang":
            jahr = self.combo_ausw_jahr.get()
        else:
            jahr = self.combo_eingang_jahr.get()

        audit_csv = os.path.join(firm_dir, "audit", jahr, f"audit_{bereich}_{jahr}.csv")
        if not os.path.exists(audit_csv):
            return self.show_info("Info", f"Für das Jahr {jahr} existiert noch kein Audit-Log ({bereich}).")

        gefundene = []
        try:
            with open(audit_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    gefundene.append(row)
        except Exception as e:
            return self.show_error("Fehler", f"Fehler beim Lesen des Audit-Logs: {e}")

        if not gefundene:
            return self.show_info("Info", "Das Audit-Log ist leer.")

        firma_name = self.p_config.get("profil_name", "Unbekannte Firma")
        pdf_pfad = os.path.join(firm_dir, "audit", jahr, f"AuditLog_{bereich}_{jahr}.pdf")

        try:
            breite, hoehe = landscape(A4)

            def render_journal(c_obj, is_final=False, total_pages=1):
                page_num = 1

                def draw_header():
                    c_obj.setFont("Helvetica-Bold", 15)
                    c_obj.drawString(35, hoehe - 45, f"GoBD Audit-Log ({bereich}) - {jahr} - {firma_name}")
                    c_obj.setFont("Helvetica-Bold", 9)
                    y_h = hoehe - 75
                    c_obj.drawString(35, y_h, "Zeitstempel")
                    c_obj.drawString(130, y_h, "Arbeitsplatz")
                    c_obj.drawString(220, y_h, "Modus")
                    c_obj.drawString(280, y_h, "Aktion")
                    c_obj.drawString(350, y_h, "BelegNr")
                    c_obj.drawString(450, y_h, "Bemerkung / Begründung")
                    c_obj.line(35, y_h - 5, 815, y_h - 5)
                    return y_h - 20

                def draw_footer():
                    c_obj.setFont("Helvetica", 8.5)
                    c_obj.drawString(35, 20, f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr")
                    if total_pages > 1:
                        c_obj.drawRightString(815, 20, f"Seite {page_num} / {total_pages}")

                y = draw_header()
                if is_final:
                    draw_footer()
                c_obj.setFont("Helvetica", 9)

                for r in gefundene:
                    if y < 40:
                        c_obj.showPage()
                        page_num += 1
                        y = draw_header()
                        if is_final:
                            draw_footer()
                        c_obj.setFont("Helvetica", 9)

                    c_obj.drawString(35, y, r.get("Zeitstempel", ""))
                    c_obj.drawString(130, y, str(r.get("Arbeitsplatz", ""))[:15])
                    c_obj.drawString(220, y, str(r.get("Modus", "")))
                    c_obj.drawString(280, y, str(r.get("Aktion", "")))
                    c_obj.drawString(350, y, str(r.get("BelegNr", "")))

                    bem = str(r.get("Bemerkung", ""))
                    if len(bem) > 75:
                        bem = bem[:72] + "..."
                    c_obj.drawString(450, y, bem)
                    y -= 15

                return page_num

            c_dummy = canvas.Canvas(BytesIO(), pagesize=landscape(A4))
            t_pages = render_journal(c_dummy)

            c = canvas.Canvas(pdf_pfad, pagesize=landscape(A4))
            render_journal(c, is_final=True, total_pages=t_pages)
            c.save()

            try:
                os.startfile(pdf_pfad)
            except Exception:
                self.show_info("Fertig", f"Audit-Log PDF erstellt:\n{pdf_pfad}")
        except PermissionError:
            self.show_error("Zugriff verweigert", "Das PDF ist in einem anderen Programm geöffnet. Bitte schließen.")
        except Exception as e:
            self.show_error("Fehler", f"Ein Fehler ist aufgetreten:\n{str(e)}")