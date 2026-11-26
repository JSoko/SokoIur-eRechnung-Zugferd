"""
tab_auswertungen.py
-------------------
Logik und Aufbau des Reiters "Ausgang" (Journal, Offene Posten & Auswertungen).
"""
import os
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk

from utils import safe_float, f_curr
from audit import write_audit_log
from journal_service import (
    is_invoice_paid,
    find_outgoing_invoice_pdf,
    get_available_outgoing_years,
    load_outgoing_journal_rows,
    set_outgoing_invoice_paid,
    create_outgoing_journal_pdf,
    export_outgoing_journal_csv,
    export_outgoing_datev_csv,
)
from gui_utils import create_tooltip, setup_auto_scrollbar, update_scrollable_visibility


class TabAuswertungenMixin:
    def build_ausgang_tab(self):
        f = ctk.CTkFrame(self.tab_ausgang)
        f.pack(pady=(15, 8), padx=20, fill="x")

        ctk.CTkLabel(f, text="Ausgangsrechnungen (Journal & Offene Posten)", font=("Helvetica", 16, "bold")).pack(pady=(10, 4))

        f_ord = ctk.CTkFrame(f, fg_color="transparent")
        f_ord.pack(pady=(6, 4), fill="x", padx=10)
        ctk.CTkLabel(f_ord, text="Journal-Ordner:", width=150, anchor="w").pack(side="left")

        self.entry_ausw_ordner = ctk.CTkEntry(f_ord, width=300)
        self.entry_ausw_ordner.pack(side="left", padx=10, expand=True, fill="x")
        self.entry_ausw_ordner.insert(0, self.p_config.get("auswertungen_ordner", "aausw"))

        self.create_button(
            f_ord, text="📂", width=40,
            command=lambda: self.browse_path_for_entry(
                self.entry_ausw_ordner,
                is_dir=True,
                on_change=lambda: (self.update_ausw_jahre(), self.refresh_ausgang_journal_ui())
            )
        ).pack(side="left")
        self.entry_ausw_ordner.bind("<FocusOut>", lambda e: (self.update_ausw_jahre(), self.refresh_ausgang_journal_ui()))

        f_zeit = ctk.CTkFrame(f, fg_color="transparent")
        f_zeit.pack(pady=4, fill="x", padx=10)
        ctk.CTkLabel(f_zeit, text="Zeitraum (Monat / Jahr):", width=150, anchor="w").pack(side="left")

        self.combo_ausw_monat = ctk.CTkComboBox(
            f_zeit,
            values=["Alle Monate"] + [f"{i:02d}" for i in range(1, 13)],
            width=120,
            command=lambda _: self.refresh_ausgang_journal_ui()
        )
        self.combo_ausw_monat.pack(side="left", padx=(10, 5))
        self.combo_ausw_monat.set(datetime.now().strftime("%m"))

        self.combo_ausw_jahr = ctk.CTkComboBox(
            f_zeit,
            values=[],
            width=120,
            command=lambda _: self.refresh_ausgang_journal_ui()
        )
        self.combo_ausw_jahr.pack(side="left", padx=5)

        f_btns1 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns1.pack(pady=(12, 4), fill="x", padx=10)

        btn_a_pdf = self.create_button(f_btns1, text="📄 Journal als PDF erzeugen & öffnen", command=self.generate_auswertung, fg_color="#b85c00", hover_color="#8f4700")
        btn_a_pdf.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_a_pdf, "Erstellt eine übersichtliche PDF-Tabelle Ihrer Ausgangsrechnungen\ninklusive Kennzeichnung (✔) der bezahlten Rechnungen.")

        btn_a_csv = self.create_button(f_btns1, text="📊 Journal als CSV exportieren & öffnen", command=self.generate_auswertung_csv, fg_color="#1f538d", hover_color="#14375d")
        btn_a_csv.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_a_csv, "Exportiert die Daten im CSV-Format, ideal für die weitere\nVerarbeitung in Microsoft Excel.")

        f_btns2 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns2.pack(pady=(4, 4), fill="x", padx=10)

        btn_a_datev = self.create_button(f_btns2, text="📈 DATEV-Export erzeugen", command=self.generate_auswertung_datev, fg_color="#107C41", hover_color="#0b5c30")
        btn_a_datev.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_a_datev, "Erstellt eine spezielle DATEV-ASCII-Datei für den Steuerberater.\nNimmt automatisch das nötige Steuer-Splitting vor.")

        btn_a_audit = self.create_button(f_btns2, text="🛡️ Audit-Log PDF", command=lambda: self.generate_audit_pdf("Ausgang"), fg_color="#333", hover_color="#555")
        btn_a_audit.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_a_audit, "Erstellt das Revisions-Protokoll (GoBD Audit-Log)\nder Ausgangsrechnungen als PDF-Datei für das Jahr.")

        f_btns3 = ctk.CTkFrame(f, fg_color="transparent")
        f_btns3.pack(pady=(4, 12), fill="x", padx=10)

        btn_dash = self.create_button(f_btns3, text="📈 Visuelles Business-Dashboard öffnen", command=self.open_dashboard_popup, fg_color="#1f538d", hover_color="#14375d")
        btn_dash.pack(side="left", fill="x", expand=True, padx=5)
        create_tooltip(btn_dash, "Öffnet ein interaktives Grafik-Dashboard mit monatlichem Umsatzverlauf,\nTop-5-Kunden und einer Gegenüberstellung von Umsatzsteuer und Vorsteuer.")

        f_list = ctk.CTkFrame(self.tab_ausgang)
        f_list.pack(pady=(4, 15), padx=20, fill="both", expand=True)

        f_search = ctk.CTkFrame(f_list, fg_color="transparent")
        f_search.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(f_search, text="🔍 Rechnungen:", font=("Helvetica", 13, "bold")).pack(side="left")
        self.entry_ausgang_search = ctk.CTkEntry(
            f_search, placeholder_text="RE-Nr., Empfänger, Datum oder Betrag..."
        )
        self.entry_ausgang_search.pack(side="left", fill="x", expand=True, padx=8)
        self.entry_ausgang_search.bind("<KeyRelease>", lambda e: self.refresh_ausgang_journal_ui())

        self.chk_ausgang_hide_paid = ctk.CTkCheckBox(
            f_search,
            text="Bezahlte ausblenden",
            command=self.refresh_ausgang_journal_ui
        )
        self.chk_ausgang_hide_paid.pack(side="left", padx=6)
        create_tooltip(self.chk_ausgang_hide_paid, "Blendet bereits als bezahlt markierte Rechnungen aus,\num nur noch offene Posten anzuzeigen.")

        self.create_button(
            f_search, text="🔄 Aktualisieren", width=110, fg_color="#444", hover_color="#666",
            command=self.refresh_ausgang_journal_ui
        ).pack(side="right")

        self.lbl_ausgang_summary = ctk.CTkLabel(
            f_list,
            text="",
            anchor="w",
            font=("Helvetica", 11, "bold"),
            text_color=("#1f538d", "#6cb2ff")
        )
        self.lbl_ausgang_summary.pack(fill="x", padx=14, pady=(0, 4))

        self.ausgang_journal_scroll = ctk.CTkScrollableFrame(f_list)
        self.ausgang_journal_scroll.pack(fill="both", expand=True, padx=12, pady=(2, 10))
        setup_auto_scrollbar(self.ausgang_journal_scroll)

        self.update_ausw_jahre()
        self.refresh_ausgang_journal_ui()

    def _open_outgoing_invoice_pdf(self, re_nr: str, datum_str: str = ""):
        ausgabe_ordner = self.p_config.get("ausgabe_ordner", "")
        akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        sel_jahr = self.combo_ausw_jahr.get() if hasattr(self, "combo_ausw_jahr") else akt_jahr
        pdf_path = find_outgoing_invoice_pdf(ausgabe_ordner, re_nr, datum_str, [sel_jahr, akt_jahr])
        if not pdf_path:
            return self.show_warning(
                "PDF nicht gefunden",
                f"Für die Rechnung '{re_nr}' wurde im Rechnungsordner\n"
                f"({ausgabe_ordner})\n"
                f"keine PDF-Datei gefunden."
            )
        try:
            os.startfile(pdf_path)
        except Exception as e:
            self.show_error("Fehler beim Öffnen", f"Die PDF-Datei konnte nicht geöffnet werden:\n{e}")

    def toggle_outgoing_paid_status(self, rec: dict):
        currently_paid = is_invoice_paid(rec)
        ok, err = set_outgoing_invoice_paid(rec, not currently_paid)
        if not ok:
            return self.show_error("Fehler", err)

        re_nr = str(rec.get("Rechnungsnummer", "")).strip()
        base_data_path = self.config.get("base_data_path", "")
        if base_data_path and re_nr:
            firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_"))
            aktion = "Bezahlt-Markierung entfernt" if currently_paid else "Als bezahlt markiert"
            write_audit_log(firm_dir, "Ausgang", aktion, re_nr, f"Empfänger: {rec.get('Empfaenger', '')}", "GUI")

        self.refresh_ausgang_journal_ui()

    def refresh_ausgang_journal_ui(self):
        if not hasattr(self, "ausgang_journal_scroll") or not self.ausgang_journal_scroll.winfo_exists():
            return

        for w in self.ausgang_journal_scroll.winfo_children():
            w.destroy()

        ordner = self.entry_ausw_ordner.get().strip() if hasattr(self, "entry_ausw_ordner") else self.p_config.get("auswertungen_ordner", "aausw")
        jahr = self.combo_ausw_jahr.get() if hasattr(self, "combo_ausw_jahr") else str(datetime.now().year)
        monat = self.combo_ausw_monat.get() if hasattr(self, "combo_ausw_monat") else "Alle Monate"

        alle_eintraege = list(reversed(load_outgoing_journal_rows(ordner, jahr, monat)))

        term = self.entry_ausgang_search.get().strip().lower() if hasattr(self, "entry_ausgang_search") else ""
        hide_paid = bool(self.chk_ausgang_hide_paid.get()) if hasattr(self, "chk_ausgang_hide_paid") else False

        sum_gesamt = 0.0
        sum_bezahlt = 0.0
        sum_offen = 0.0
        count_offen = 0
        count_bezahlt = 0

        gefiltert = []
        for r in alle_eintraege:
            brutto_val = safe_float(r.get("Brutto", 0))
            paid = is_invoice_paid(r)
            sum_gesamt += brutto_val
            if paid:
                sum_bezahlt += brutto_val
                count_bezahlt += 1
            else:
                sum_offen += brutto_val
                count_offen += 1

            if hide_paid and paid:
                continue

            if term:
                haystack = " ".join([
                    str(r.get("Rechnungsnummer", "")),
                    str(r.get("Datum", "")),
                    str(r.get("Empfaenger", "")),
                    str(r.get("Netto", "")),
                    str(r.get("Brutto", "")),
                    str(r.get("Bezahlt", "")),
                ]).lower()
                if term not in haystack:
                    continue

            gefiltert.append(r)

        if hasattr(self, "lbl_ausgang_summary") and self.lbl_ausgang_summary.winfo_exists():
            zeit_label = jahr if monat == "Alle Monate" else f"{monat}.{jahr}"
            self.lbl_ausgang_summary.configure(
                text=(
                    f"Zeitraum {zeit_label}:  Gesamt {f_curr(sum_gesamt)} ({len(alle_eintraege)} Belege)   |   "
                    f"Offen: {f_curr(sum_offen)} ({count_offen})   |   "
                    f"Bezahlt: {f_curr(sum_bezahlt)} ({count_bezahlt})"
                )
            )

        if not gefiltert:
            msg = (
                "Keine offenen Ausgangsrechnungen für diese Auswahl vorhanden."
                if hide_paid and alle_eintraege
                else "Keine Ausgangsrechnungen für diesen Zeitraum / Filter gefunden."
            )
            ctk.CTkLabel(self.ausgang_journal_scroll, text=msg, text_color="gray").pack(pady=20)
            update_scrollable_visibility(self.ausgang_journal_scroll)
            return

        faellig_tage = int(self.p_config.get("faelligkeit_tage", "29")) if str(self.p_config.get("faelligkeit_tage", "29")).isdigit() else 29
        heute = datetime.now().date()
        ausgabe_ordner = self.p_config.get("ausgabe_ordner", "")
        akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        btn_size = 34

        for rec in gefiltert[:200]:
            row = ctk.CTkFrame(self.ausgang_journal_scroll)
            row.pack(fill="x", pady=2, padx=4)

            re_nr = str(rec.get("Rechnungsnummer", "")).strip()
            datum_str = str(rec.get("Datum", "")).strip()
            empf = str(rec.get("Empfaenger", "")).strip()
            netto_str = str(rec.get("Netto", "0,00")).strip()
            brutto_str = str(rec.get("Brutto", "0,00")).strip()
            bezahlt_raw = str(rec.get("Bezahlt", "")).strip()
            paid = is_invoice_paid(rec)

            is_overdue = False
            if not paid and len(datum_str) == 10:
                try:
                    re_date = datetime.strptime(datum_str, "%d.%m.%Y").date()
                    if (heute - re_date).days > faellig_tage:
                        is_overdue = True
                except ValueError:
                    pass

            act_box = ctk.CTkFrame(row, fg_color="transparent")
            act_box.pack(side="left", padx=(6, 4), pady=3)

            btn_paid = self.create_button(
                act_box,
                text="✔" if paid else "€",
                width=btn_size,
                height=btn_size,
                fg_color="#208000" if paid else "#555555",
                hover_color="#176000" if paid else "#1f538d",
                command=lambda r_obj=rec: self.toggle_outgoing_paid_status(r_obj)
            )
            btn_paid.pack(side="left", padx=2)
            create_tooltip(
                btn_paid,
                f"Bezahlt-Markierung für {re_nr} wieder entfernen ({bezahlt_raw})"
                if paid
                else f"Rechnung {re_nr} als BEZAHLT kennzeichnen"
            )

            pdf_pfad = find_outgoing_invoice_pdf(ausgabe_ordner, re_nr, datum_str, [jahr, akt_jahr])
            btn_pdf = self.create_button(
                act_box,
                text="👁",
                width=btn_size,
                height=btn_size,
                fg_color="#1f538d" if pdf_pfad else "#3a3a3a",
                hover_color="#14375d" if pdf_pfad else "#4a4a4a",
                command=lambda nr=re_nr, dt=datum_str: self._open_outgoing_invoice_pdf(nr, dt)
            )
            btn_pdf.pack(side="left", padx=2)
            create_tooltip(
                btn_pdf,
                f"PDF-Rechnung zu {re_nr} öffnen\n({os.path.basename(pdf_pfad)})"
                if pdf_pfad
                else f"Keine PDF-Datei für {re_nr} im Rechnungsordner gefunden"
            )

            if paid:
                status_txt = f"✔ Bezahlt ({bezahlt_raw[4:-1]})" if bezahlt_raw.startswith("Ja (") and bezahlt_raw.endswith(")") else "✔ Bezahlt"
                lbl_color = ("#1e7e34", "#4ade80")
            elif is_overdue:
                status_txt = "⚠️ Überfällig"
                lbl_color = ("#b30000", "#f87171")
            else:
                status_txt = "⏳ Offen"
                lbl_color = None

            empf_kurz = empf[:30] + "..." if len(empf) > 33 else empf
            txt = f"[{re_nr}] {datum_str} | {empf_kurz} | Netto: {netto_str} € | Brutto: {brutto_str} € | {status_txt}"

            lbl_kwargs = {"text": txt, "anchor": "w", "cursor": "hand2"}
            if lbl_color:
                lbl_kwargs["text_color"] = lbl_color

            lbl = ctk.CTkLabel(row, **lbl_kwargs)
            lbl.pack(side="left", padx=6, pady=4, fill="x", expand=True)
            lbl.bind("<Button-1>", lambda e, nr=re_nr, dt=datum_str: self._open_outgoing_invoice_pdf(nr, dt))
            create_tooltip(lbl, f"Klicken, um die PDF-Rechnung {re_nr} im Rechnungsordner zu öffnen.")

        update_scrollable_visibility(self.ausgang_journal_scroll)

    def update_ausw_jahre(self):
        if not hasattr(self, "entry_ausw_ordner"):
            return
        jahre_liste = get_available_outgoing_years(self.entry_ausw_ordner.get().strip())
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
        firma_csv = self.p_config.get("firma_csv", "firma.csv")
        try:
            pdf_pfad, err = create_outgoing_journal_pdf(ordner, jahr, monat, firma_csv)
            if err:
                msg_type = "warning" if "existiert nicht" in err else "info"
                return self.show_warning("Fehler", err) if msg_type == "warning" else self.show_info("Info", err)
            try:
                os.startfile(pdf_pfad)
            except Exception:
                self.show_info("Fertig", f"Journal erfolgreich erstellt unter:\n{pdf_pfad}")
        except PermissionError:
            self.show_error(
                "Zugriff verweigert",
                f"Das PDF konnte nicht überschrieben werden, da es bereits in einem anderen Programm geöffnet ist:\n\n{jahr}"
            )
        except Exception as e:
            self.show_error("Fehler", f"Ein technischer Fehler ist aufgetreten:\n{str(e)}")

    def generate_auswertung_csv(self):
        ordner = self.entry_ausw_ordner.get().strip()
        jahr = self.combo_ausw_jahr.get()
        monat = self.combo_ausw_monat.get()
        csv_export_pfad, err = export_outgoing_journal_csv(ordner, jahr, monat)
        if err:
            return self.show_warning("Fehler", err) if "existiert nicht" in err else self.show_info("Info", err)
        try:
            os.startfile(csv_export_pfad)
        except Exception:
            self.show_info("Fertig", f"CSV erstellt: {csv_export_pfad}")

    def generate_auswertung_datev(self):
        if hasattr(self, "license_mgr"):
            self.license_mgr.record_pro_feature_use("DATEV-Export (Ausgang)")
        ordner = self.entry_ausw_ordner.get().strip()
        jahr = self.combo_ausw_jahr.get()
        monat = self.combo_ausw_monat.get()
        csv_export_pfad, err = export_outgoing_datev_csv(ordner, jahr, monat, self.p_config)
        if err:
            return self.show_warning("Fehler", err) if "existiert nicht" in err else self.show_info("Info", err)
        try:
            os.startfile(csv_export_pfad)
        except Exception:
            self.show_info("Fertig", f"DATEV-Export erstellt: {csv_export_pfad}")
