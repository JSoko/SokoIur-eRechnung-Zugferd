"""
tab_erfassen.py
---------------
Logik und Aufbau des Reiters "Erfassen" (Eingangsrechnungen prüfen).
"""
import os
import re
import sys
import shutil
import subprocess
import tempfile
from decimal import Decimal
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk
import tkinter.messagebox as messagebox

from config import *
from utils import *
from crud import *
from audit import write_audit_log
from gui_utils import create_tooltip, setup_auto_scrollbar, update_scrollable_visibility


class TabErfassenMixin:
    def build_erfassen_tab(self):
        if not hasattr(self, 'skipped_incoming_files'):
            self.skipped_incoming_files = set()

        f = ctk.CTkFrame(self.tab_erfassen)
        f.pack(pady=15, padx=20, fill="both", expand=True)

        ctk.CTkLabel(f, text="Eingangsrechnungen erfassen", font=("Helvetica", 16, "bold")).pack(pady=(12, 4))

        ctk.CTkLabel(
            f,
            text="Die formelle und rechnerische Prüfung ist eine automatisierte Plausibilitätsprüfung und keine steuerliche oder rechtliche Freigabe.",
            text_color="orange", wraplength=780, justify="center"
        ).pack(pady=4)

        # Aktionsleiste mit kompakten Breiten, damit alle Buttons auch bei schmalen Fenstern sichtbar bleiben
        btn_bar = ctk.CTkFrame(f, fg_color="transparent")
        btn_bar.pack(fill="x", padx=10, pady=8)

        btn_next_in = self.create_button(
            btn_bar,
            text="📥 Nächste",
            command=self.process_next_incoming,
            fg_color="#1f538d",
            hover_color="#14375d",
            height=34,
            width=155,
        )
        btn_next_in.pack(side="left", padx=3)
        create_tooltip(
            btn_next_in,
            "Prüft die oberste Datei im Eingangsordner auf gesetzliche \nVorgaben und startet den Erfassungsprozess.",
        )

        btn_ref_in = self.create_button(
            btn_bar,
            text="🔄 Aktualisieren",
            command=self.refresh_incoming_list,
            fg_color="#444",
            hover_color="#666",
            height=34,
            width=135,
        )
        btn_ref_in.pack(side="left", padx=3)
        create_tooltip(btn_ref_in, "Sucht nach neu hinzugefügten Dateien im Eingangsordner.")

        btn_open_in = self.create_button(
            btn_bar,
            text="📂 Ordner",
            command=self.open_incoming_folder,
            fg_color="#444",
            hover_color="#666",
            height=34,
            width=110,
        )
        btn_open_in.pack(side="left", padx=3)
        create_tooltip(btn_open_in, "Öffnet den Eingangsordner (reneu) der aktiven Firma im Windows-Explorer.")

        btn_find_in = self.create_button(
            btn_bar,
            text="📄 Datei suchen",
            command=self.select_and_copy_incoming_file,
            fg_color="#444",
            hover_color="#666",
            height=34,
            width=130,
        )
        btn_find_in.pack(side="left", padx=3)
        create_tooltip(
            btn_find_in,
            "Sucht eine oder mehrere Belegdateien aus und kopiert sie\nin den Eingangsordner (reneu) der aktiven Firma.",
        )

        btn_drop_helper = self.create_button(
            btn_bar,
            text="📥 Drop-Helper",
            command=self.launch_drop_helper,
            fg_color="#0f766e",
            hover_color="#115e59",
            height=34,
            width=130,
        )
        btn_drop_helper.pack(side="left", padx=3)
        create_tooltip(
            btn_drop_helper,
            "Startet das eigenständige Drag-&-Drop-Fenster für die aktuell gewählte Firma.",
        )

        ctk.CTkLabel(f, text="Wartende Belege im Eingangsordner:", font=("Helvetica", 13, "bold")).pack(pady=(8, 2))
        self.incoming_scroll = ctk.CTkScrollableFrame(f, height=220)
        self.incoming_scroll.pack(fill="both", expand=True, padx=20, pady=5)
        setup_auto_scrollbar(self.incoming_scroll)

        ctk.CTkLabel(
            f,
            text="Nach der Erfassung wird das Original im Jahresordner „rebearb/<Jahr>“ archiviert; die nummerierte Archivkopie wird unter „rchn/<Jahr>“ gespeichert.",
            wraplength=750, justify="center", text_color="gray"
        ).pack(pady=6)

        self.refresh_incoming_list()

    def launch_drop_helper(self):
        """Startet das eigenständige Drop-Helper-Programm im Kontext der aktiven Firma."""
        profil_name = ""
        if hasattr(self, "p_config") and isinstance(self.p_config, dict):
            profil_name = str(self.p_config.get("profil_name", "")).strip()
        profil_index = int(getattr(self, "config", {}).get("active_profile_index", -1))

        args = []
        if profil_name:
            args.extend(["--profil", profil_name])
        if profil_index >= 0:
            args.extend(["--profil-index", str(profil_index)])

        try:
            if getattr(sys, "frozen", False):
                app_dir = os.path.dirname(sys.executable)
                helper_exe = os.path.join(app_dir, "SokoIur_eRechnung_DropHelper.exe")
                if not os.path.isfile(helper_exe):
                    return self.show_warning(
                        "Drop-Helper fehlt",
                        f"Die Datei 'SokoIur_eRechnung_DropHelper.exe' wurde im Programmverzeichnis nicht gefunden:\n{app_dir}",
                    )
                subprocess.Popen([helper_exe, *args], cwd=app_dir)
            else:
                src_dir = os.path.abspath(os.path.dirname(__file__))
                helper_py = os.path.join(src_dir, "drop_helper.py")
                if not os.path.isfile(helper_py):
                    return self.show_warning(
                        "Drop-Helper fehlt",
                        f"Die Datei 'drop_helper.py' wurde nicht gefunden:\n{helper_py}",
                    )
                subprocess.Popen([sys.executable, helper_py, *args], cwd=src_dir)
        except Exception as e:
            self.show_error("Start fehlgeschlagen", f"Der Drop-Helper konnte nicht gestartet werden:\n{e}")

    def select_and_copy_incoming_file(self):
        """Öffnet einen Dateiauswahldialog und kopiert gewählte Belege in den Eingangsordner (reneu)."""
        target_dir = self.p_config.get("eingangsordner", "")
        if not target_dir or not os.path.isdir(target_dir):
            return self.show_warning("Eingangsordner fehlt", f"Der Eingangsordner existiert nicht:\n{target_dir}")

        paths = filedialog.askopenfilenames(
            title="Belegdatei(en) für Eingangsordner auswählen",
            filetypes=[
                ("Rechnungen & Belege", "*.pdf *.xml *.jpg *.jpeg *.png *.tif *.tiff"),
                ("PDF-Dateien", "*.pdf"),
                ("XML-Dateien", "*.xml"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if not paths:
            return

        copied = 0
        for src in paths:
            if not src or not os.path.isfile(src):
                continue
            fname = os.path.basename(src)
            dst = os.path.join(target_dir, fname)
            if os.path.abspath(src) == os.path.abspath(dst):
                continue
            if os.path.exists(dst):
                stem, ext = os.path.splitext(fname)
                dst = os.path.join(target_dir, f"{stem}_{datetime.now().strftime('%H%M%S_%f')}{ext}")
            shutil.copy2(src, dst)
            copied += 1

        if copied > 0:
            self.refresh_incoming_list()
            self.show_info("Übernommen", f"{copied} Datei(en) wurden in den Eingangsordner kopiert:\n{target_dir}")

    def open_incoming_folder(self):
        folder = self.p_config.get('eingangsordner', '')
        if folder and os.path.isdir(folder):
            try:
                os.startfile(folder)
            except Exception:
                subprocess.Popen(['explorer', folder])
        else:
            self.show_warning("Ordner fehlt", f"Der Ordner existiert noch nicht:\n{folder}")

    def _open_copy_in_temp(self, path):
        """Kopiert den Beleg aus dem Eingangsordner nach Temp und öffnet dort die Kopie."""
        if not path or not os.path.exists(path):
            return self.show_warning("Datei fehlt", f"Die Datei wurde nicht gefunden:\n{path}")

        try:
            temp_view_dir = os.path.join(tempfile.gettempdir(), "SokoIur_eRechnung_Ansicht")
            os.makedirs(temp_view_dir, exist_ok=True)

            base_name = os.path.basename(path)
            name_ohne_ext, ext = os.path.splitext(base_name)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_copy_path = os.path.join(temp_view_dir, f"{name_ohne_ext}_{ts}{ext}")

            shutil.copy2(path, temp_copy_path)
            os.startfile(temp_copy_path)
        except Exception as e:
            self.show_error("Fehler", f"Kopie in Temp konnte nicht geöffnet werden:\n{e}")

    def _open_file_external(self, path):
        if os.path.exists(path):
            self._open_copy_in_temp(path)

    def _remove_duplicate_source_file(self, path):
        """Entfernt eine als Duplikat erkannte Datei aus reneu (oder verschiebt sie nach rebearb)."""
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            wait = self.p_config.get('eingang_loesch_warteliste', []) or []
            abs_p = os.path.abspath(path)
            if abs_p not in [os.path.abspath(x) for x in wait]:
                wait.append(path)
                self.p_config['eingang_loesch_warteliste'] = wait
                speichere_config(self.config)
        self.refresh_incoming_list()

    def refresh_incoming_list(self):
        if not hasattr(self, 'incoming_scroll') or not self.incoming_scroll.winfo_exists():
            return
        from eingangsrechnung import check_duplicate_incoming, load_all_journal_entries

        for w in self.incoming_scroll.winfo_children():
            w.destroy()

        folder = self.p_config.get('eingangsordner', '')

        self._retry_incoming_deletions()
        if not folder or not os.path.isdir(folder):
            ctk.CTkLabel(self.incoming_scroll, text="Eingangsordner noch nicht angelegt.", text_color="gray").pack(pady=15)
            update_scrollable_visibility(self.incoming_scroll)
            return

        waiting_list = self.p_config.get('eingang_loesch_warteliste', []) or []
        norm_wait = {os.path.abspath(p) for p in waiting_list if p}

        all_files = sorted([
            os.path.join(folder, x) for x in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, x)) and not x.startswith('.')
        ])
        files = [f for f in all_files if os.path.abspath(f) not in norm_wait]

        if hasattr(self, 'skipped_incoming_files'):
            self.skipped_incoming_files.intersection_update(files)

        if not files:
            hinweis = "Keine offenen Eingangsrechnungen im Ordner vorhanden."
            if len(all_files) > len(files):
                hinweis += f" ({len(all_files) - len(files)} bereits erfasste Datei(en) warten auf automatische Löschung nach Schließen des PDF-Viewers)."
            ctk.CTkLabel(self.incoming_scroll, text=hinweis, text_color="gray", wraplength=680).pack(pady=15)
            update_scrollable_visibility(self.incoming_scroll)
            return

        journal_folder = self.p_config.get('eingangsjournal_ordner', '')
        alle_journale = load_all_journal_entries(journal_folder)

        btn_size = 34

        for idx, fpath in enumerate(files):
            row = ctk.CTkFrame(self.incoming_scroll)
            row.pack(fill="x", pady=2, padx=4)
            fname = os.path.basename(fpath)
            is_skipped = fpath in getattr(self, 'skipped_incoming_files', set())

            is_dup, dup_reason, dup_rec = check_duplicate_incoming(
                fpath, journal_folder, waiting_list, entries=alle_journale
            )

            status_tag = ""
            lbl_color = None
            if is_dup:
                er_id = dup_rec.get("Interne ER-Nr.", "") if dup_rec else ""
                status_tag = f" [BEREITS ERFASST: {er_id}]"
                lbl_color = "#d9534f"
            elif is_skipped:
                status_tag = " (Zurückgestellt)"

            # Quadratische Buttons zuerst links platzieren, damit sie bei schmalen Fenstern nie verdeckt werden
            act_box = ctk.CTkFrame(row, fg_color="transparent")
            act_box.pack(side="left", padx=(6, 4), pady=3)

            btn_check = self.create_button(
                act_box, text="✔", width=btn_size, height=btn_size,
                fg_color="#1f538d", hover_color="#14375d",
                command=lambda p=fpath: self.process_next_incoming(specific_path=p)
            )
            btn_check.pack(side="left", padx=2)
            create_tooltip(
                btn_check,
                f"Beleg '{fname}' prüfen und erfassen\n"
                f"Startet die formelle/rechnerische Prüfung bzw. die Erfassungsmaske."
            )

            btn_open = self.create_button(
                act_box, text="👁", width=btn_size, height=btn_size,
                fg_color="#555", hover_color="#777",
                command=lambda p=fpath: self._open_file_external(p)
            )
            btn_open.pack(side="left", padx=2)
            create_tooltip(
                btn_open,
                f"Temp-Kopie von '{fname}' öffnen\n"
                f"Die Originaldatei im Eingangsordner bleibt dabei ungesperrt."
            )

            if is_dup:
                er_id = dup_rec.get("Interne ER-Nr.", "") if dup_rec else ""
                btn_dup = self.create_button(
                    act_box, text="🗑", width=btn_size, height=btn_size,
                    fg_color="#b30000", hover_color="#800000",
                    command=lambda p=fpath: self._remove_duplicate_source_file(p)
                )
                btn_dup.pack(side="left", padx=2)
                create_tooltip(
                    btn_dup,
                    f"Duplikat '{fname}' aus dem Eingangsordner entfernen\n"
                    f"Bereits erfasst unter {er_id} ({dup_reason})."
                )

            lbl_kwargs = {"text": f"{idx+1}. {fname}{status_tag}", "anchor": "w"}
            if lbl_color:
                lbl_kwargs["text_color"] = lbl_color
            ctk.CTkLabel(row, **lbl_kwargs).pack(side="left", padx=6, pady=4, fill="x", expand=True)

        update_scrollable_visibility(self.incoming_scroll)

    def process_next_incoming(self, specific_path=None):
        from eingangsrechnung import (
            detect_invoice,
            parse_einvoice,
            error_notice,
            check_duplicate_incoming,
            extract_invoice_data_from_pdf,
        )
        folder = self.p_config.get('eingangsordner', '')
        if not os.path.isdir(folder):
            return self.show_warning('Eingangsordner fehlt', f'Der Eingangsordner existiert nicht:\n{folder}')

        self._retry_incoming_deletions()
        waiting_list = self.p_config.get('eingang_loesch_warteliste', []) or []
        norm_wait = {os.path.abspath(p) for p in waiting_list if p}

        files = sorted([
            os.path.join(folder, x) for x in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, x)) and not x.startswith('.') and os.path.abspath(os.path.join(folder, x)) not in norm_wait
        ])
        if not files:
            self.refresh_incoming_list()
            return self.show_info('Keine Eingangsrechnungen', f'Im Ordner\n{folder}\nsind keine unbearbeiteten Eingangsrechnungen vorhanden.')

        if specific_path and os.path.exists(specific_path):
            path = specific_path
        else:
            unskipped = [f for f in files if f not in getattr(self, 'skipped_incoming_files', set())]
            if not unskipped:
                self.skipped_incoming_files.clear()
                unskipped = files
            path = unskipped[0]

        journal_folder = self.p_config.get('eingangsjournal_ordner', '')

        is_dup, dup_msg, _ = check_duplicate_incoming(path, journal_folder, waiting_list)
        if is_dup:
            if self.ask_yes_no(
                "Bereits erfasste Rechnung erkannt",
                f"Erneute Erfassung blockiert:\n\n{dup_msg}\n\n"
                f"Datei im Eingangsordner: {os.path.basename(path)}\n\n"
                f"Soll diese doppelt vorhandene Datei jetzt aus dem Eingangsordner (reneu) entfernt werden?"
            ):
                self._remove_duplicate_source_file(path)
            else:
                self.skipped_incoming_files.add(path)
                self.refresh_incoming_list()
            return

        kind, xml, detail = detect_invoice(path)
        if kind in ('ZUGFeRD', 'XRechnung'):
            data, errors = parse_einvoice(xml, kind)
            is_dup_content, dup_msg_content, _ = check_duplicate_incoming(path, journal_folder, waiting_list, invoice_data=data)
            if is_dup_content:
                if self.ask_yes_no(
                    "Bereits erfasste Rechnung erkannt",
                    f"Erneute Erfassung blockiert:\n\n{dup_msg_content}\n\n"
                    f"Datei im Eingangsordner: {os.path.basename(path)}\n\n"
                    f"Soll diese doppelt vorhandene Datei jetzt aus dem Eingangsordner (reneu) entfernt werden?"
                ):
                    self._remove_duplicate_source_file(path)
                else:
                    self.skipped_incoming_files.add(path)
                    self.refresh_incoming_list()
                return

            if errors:
                subject, body = error_notice(data, errors)
                self._show_invoice_error(path, kind, data, subject, body)
                return
            self._show_einvoice_confirmation(path, kind, data, xml)
        else:
            prefill_data = None
            ocr_notes = []
            if os.path.splitext(path)[1].lower() == ".pdf":
                prefill_data, ocr_notes = extract_invoice_data_from_pdf(path)
            self._show_other_invoice_form(path, detail, prefill=prefill_data, ocr_notes=ocr_notes)

    def _retry_incoming_deletions(self):
        waiting = self.p_config.get('eingang_loesch_warteliste', []) or []
        left = []
        for path in waiting:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                left.append(path)
        if left != waiting:
            self.p_config['eingang_loesch_warteliste'] = left
            speichere_config(self.config)

    def _show_invoice_error(self, path, kind, data, subject, body):
        d = ctk.CTkToplevel(self)
        d.title('Formelle Prüfung nicht bestanden')
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d)
        self.center_window(d, 760, 620)
        d.transient(self)
        d.grab_set()

        ctk.CTkLabel(
            d, text=f'{kind}-Rechnung ({os.path.basename(path)}): Prüfung nicht bestanden',
            font=('Helvetica', 14, 'bold'), text_color='#b30000'
        ).pack(pady=10)

        info_text = (
            f"Aussteller: {data.get('supplier') or 'nicht auslesbar'} | "
            f"E-Mail: {data.get('supplier_email') or 'nicht auslesbar'}\n"
            f"Rechnungsnummer: {data.get('number') or 'nicht auslesbar'} | "
            f"Rechnungsdatum: {data.get('date') or 'nicht auslesbar'}"
        )
        ctk.CTkLabel(d, text=info_text, justify='left').pack(padx=20, anchor='w')

        ctk.CTkLabel(d, text='Kopierbarer Betreff:').pack(padx=20, pady=(10, 0), anchor='w')
        e = ctk.CTkEntry(d)
        e.insert(0, subject)
        e.pack(fill='x', padx=20)

        ctk.CTkLabel(d, text='Kopierbarer Hinweis an den Rechnungsaussteller:').pack(padx=20, pady=(10, 0), anchor='w')
        t = ctk.CTkTextbox(d, height=220)
        t.insert('1.0', body)
        t.pack(fill='both', expand=True, padx=20, pady=4)

        bf = ctk.CTkFrame(d, fg_color='transparent')
        bf.pack(pady=12)

        def skip_and_close():
            self.skipped_incoming_files.add(path)
            d.destroy()
            self.refresh_incoming_list()

        def force_manual():
            d.destroy()
            self._show_other_invoice_form(path, detail="Trotz XML-Prüffehler manuell erfassen", prefill=data)

        self.create_button(bf, text='👁 Datei öffnen', width=130, fg_color='#555', command=lambda: self._open_file_external(path)).pack(side='left', padx=6)
        self.create_button(bf, text='⏭ Überspringen (Später)', width=180, fg_color='#666', command=skip_and_close).pack(side='left', padx=6)
        self.create_button(bf, text='⚠️ Trotzdem manuell erfassen', width=210, fg_color='#b85c00', command=force_manual).pack(side='left', padx=6)

    def _show_einvoice_confirmation(self, path, kind, data, xml):
        from eingangsrechnung import _money, suggest_aufwandskonto, get_aufwandskonto_options
        d = ctk.CTkToplevel(self)
        d.title('Eingangsrechnung prüfen und erfassen')
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d)
        self.center_window(d, 680, 700)
        d.transient(self)
        d.grab_set()

        p_cfg = getattr(self, "p_config", {})
        konto_options = get_aufwandskonto_options(p_cfg)
        konto_vorschlag = suggest_aufwandskonto(data, p_cfg)
        if konto_vorschlag not in konto_options:
            konto_options.insert(0, konto_vorschlag)

        ctk.CTkLabel(
            d, text=f'Gültige {kind}-Rechnung – Zusammenfassung',
            font=('Helvetica', 15, 'bold'), text_color='#208000'
        ).pack(pady=12)

        anschrift_lief = ", ".join(
            part for part in [
                data.get('supplier_street', '').strip(),
                f"{data.get('supplier_zip', '').strip()} {data.get('supplier_city', '').strip()}".strip(),
            ] if part
        )

        lines = [
            f"Quelldatei: {os.path.basename(path)}",
            f"Rechnungsaussteller: {data.get('supplier', '')}",
            f"Anschrift Aussteller: {anschrift_lief or '-'}",
            f"Rechnungsempfänger: {data.get('buyer', '') or '-'}",
            f"USt-IdNr. / StNr.: {data.get('supplier_tax_id', '') or '-'}",
            f"Rechnungsnummer: {data.get('number', '')}",
            f"Rechnungsdatum: {data.get('date', '')}",
            f"Leistungs-/Lieferdatum: {data.get('delivery_date', '') or '-'}",
            f"Fälligkeitsdatum: {data.get('due_date', '') or '-'}",
            f"IBAN / Währung: {data.get('iban', '') or '-'} | {data.get('currency', 'EUR')}",
            f"Land / Reverse Charge: {data.get('supplier_country', '-') or '-'} | {data.get('reverse_charge', 'Nein')}",
            f"Netto: {_money(data.get('net', '0'))} {data.get('currency', 'EUR')}",
            f"Umsatzsteuer: {_money(data.get('tax', '0'))} {data.get('currency', 'EUR')}",
            f"Brutto: {_money(data.get('gross', '0'))} {data.get('currency', 'EUR')}",
        ]
        ctk.CTkLabel(d, text='\n'.join(lines), justify='left').pack(padx=35, anchor='w')

        def on_rc_einvoice_change(wahl):
            if wahl in ("EU", "Drittland"):
                sim_zero = {"taxes": {}, "tax": "0.00", "net": data.get("net", "10.00")}
                combo_konto_in.set(suggest_aufwandskonto(sim_zero, p_cfg))
            else:
                combo_konto_in.set(suggest_aufwandskonto(data, p_cfg))

        combo_rc_in = self.create_input(
            d, "Reverse Charge", is_combo=True,
            combo_values=["Nein", "EU", "Drittland"], command=on_rc_einvoice_change
        )
        combo_rc_in.set(data.get("reverse_charge", "Nein"))

        combo_konto_in = self.create_input(
            d, "Aufwandskonto", is_combo=True, combo_values=konto_options
        )
        combo_konto_in.set(konto_vorschlag)

        var = ctk.BooleanVar(value=bool(self.p_config.get('xrechnung_leseabschrift', True)))
        if kind == 'XRechnung':
            ctk.CTkCheckBox(d, text='Lesbare PDF-Leseabschrift im Archiv erstellen', variable=var).pack(pady=10)

        def yes():
            data["reverse_charge"] = combo_rc_in.get()
            data["account"] = combo_konto_in.get().strip()
            if kind == 'XRechnung':
                self.p_config['xrechnung_leseabschrift'] = bool(var.get())
                speichere_config(self.config)
            d.destroy()
            self._archive_incoming(path, kind, data, xml, bool(var.get()) if kind == 'XRechnung' else False, True)

        def skip():
            self.skipped_incoming_files.add(path)
            d.destroy()
            self.refresh_incoming_list()

        bf = ctk.CTkFrame(d, fg_color='transparent')
        bf.pack(pady=16)
        self.create_button(bf, text='👁 Beleg ansehen', command=lambda: self._open_file_external(path), width=140, fg_color='#555').pack(side='left', padx=6)
        self.create_button(bf, text='Nein – zurückstellen', command=skip, width=160, fg_color='#666').pack(side='left', padx=6)
        self.create_button(bf, text='Ja – jetzt erfassen', command=yes, width=200, fg_color='#208000').pack(side='left', padx=6)

    def _show_other_invoice_form(self, path, detail='', prefill=None, ocr_notes=None):
        from eingangsrechnung import (
            _d,
            normalize_date_de,
            check_duplicate_incoming,
            suggest_aufwandskonto,
            get_aufwandskonto_options,
        )

        d = ctk.CTkToplevel(self)
        d.title('Sonstige Eingangsrechnung erfassen')
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(d)
        self.center_window(d, 660, 860)
        d.transient(self)
        d.grab_set()

        ctk.CTkLabel(
            d, text='Erfassung einer Rechnung (Manuelle Ergänzung)', font=('Helvetica', 14, 'bold')
        ).pack(pady=(12, 4))
        ctk.CTkLabel(
            d, text=f"Datei: {os.path.basename(path)} ({detail})", text_color="gray"
        ).pack(pady=(0, 6))

        if os.path.splitext(path)[1].lower() == ".pdf":
            warn_box = ctk.CTkFrame(
                d, fg_color="#4a2c00", border_width=1, border_color="#f59e0b", corner_radius=6
            )
            warn_box.pack(fill="x", padx=20, pady=(4, 8))

            warn_text = (
                "⚠️ ACHTUNG – AUTOMATISCHE PDF-ERKENNUNG:\n"
                "Die vorbelegten Felder wurden aus dem PDF ausgelesen und können fehlerhaft oder unvollständig sein. "
                "Bitte überprüfen Sie ALLE Werte (Lieferant, Rechnungsnummer, Datum, Steuersatz und Beträge) "
                "unbedingt anhand des Originalbelegs vor dem Speichern!"
            )
            if ocr_notes:
                warn_text += "\nHinweis: " + " | ".join(ocr_notes)

            ctk.CTkLabel(
                warn_box,
                text=warn_text,
                text_color="#fde68a",
                justify="left",
                wraplength=590,
                font=("Helvetica", 11, "bold"),
            ).pack(padx=12, pady=8, anchor="w")

        self.create_button(
            d,
            text="👁 Originaldatei zur Ansicht öffnen",
            width=240,
            fg_color="#555",
            command=lambda: self._open_file_external(path),
        ).pack(pady=4)

        kind = ctk.StringVar(value='PDF-Rechnung')
        ff = ctk.CTkFrame(d, fg_color='transparent')
        ff.pack(pady=6)
        for x in ('PDF-Rechnung', 'Gescannte Papierrechnung', 'Sonstiges'):
            ctk.CTkRadioButton(ff, text=x, variable=kind, value=x).pack(side='left', padx=8)

        entries = {}
        fields = [
            ('Lieferant *', 'supplier'),
            ('Externe Rechnungs-Nr. *', 'number'),
            ('Rechnungsdatum (TT.MM.JJJJ) *', 'date'),
            ('Nettobetrag (€)', 'net'),
            ('Umsatzsteuer (€)', 'tax'),
            ('Bruttobetrag (€)', 'gross'),
        ]
        for label, key in fields:
            entries[key] = self.create_input(d, label)

        combo_vat = self.create_input(d, "Steuersatz (%)", is_combo=True, combo_values=["19", "7", "0"])
        combo_vat.set("19")

        entry_country = self.create_input(d, "Lieferanten-Land (z.B. DE, US, LU)")
        entry_country.delete(0, 'end')
        entry_country.insert(0, prefill.get("supplier_country", "DE") if prefill else "DE")

        entry_tax_id = self.create_input(d, "Lieferant USt-IdNr.")
        if prefill and prefill.get("supplier_tax_id"):
            entry_tax_id.delete(0, 'end')
            entry_tax_id.insert(0, str(prefill.get("supplier_tax_id")))

        p_cfg = getattr(self, "p_config", {})
        konto_options = get_aufwandskonto_options(p_cfg)
        combo_konto_manual = self.create_input(
            d, "Aufwandskonto", is_combo=True, combo_values=konto_options
        )

        def _update_konto_vorschlag(*_args):
            rc_v = combo_rc_manual.get()
            vat_v = "0" if rc_v in ("EU", "Drittland") else combo_vat.get()
            sim_data = {
                "taxes": {vat_v: "1.00"} if vat_v not in ("0", "0.0") else {},
                "tax": "0.00" if vat_v in ("0", "0.0") else "1.00",
                "net": "10.00",
            }
            combo_konto_manual.set(suggest_aufwandskonto(sim_data, p_cfg))

        def on_rc_in_change(wahl):
            if wahl in ("EU", "Drittland"):
                combo_vat.set("0")
            _update_konto_vorschlag()

        combo_rc_manual = self.create_input(
            d,
            "Reverse Charge",
            is_combo=True,
            combo_values=["Nein", "EU", "Drittland"],
            command=on_rc_in_change,
        )
        combo_rc_manual.set(prefill.get("reverse_charge", "Nein") if prefill else "Nein")
        combo_vat.configure(command=lambda _v: _update_konto_vorschlag())

        if prefill:
            for k in ('supplier', 'number', 'date', 'net', 'tax', 'gross'):
                if prefill.get(k):
                    entries[k].delete(0, 'end')
                    entries[k].insert(0, str(prefill.get(k)))
        else:
            entries['date'].delete(0, 'end')
            entries['date'].insert(0, datetime.now().strftime('%d.%m.%Y'))

        _update_konto_vorschlag()

        checked = ctk.CTkCheckBox(
            d, text='Ich habe geprüft, dass diese Rechnung zum Vorsteuerabzug berechtigt'
        )
        checked.pack(pady=10)

        ctk.CTkLabel(
            d,
            text='Hinweis: Mindestens Netto oder Brutto eingeben. Fehlende Beträge werden anhand des gewählten Steuersatzes berechnet.',
            text_color='orange',
            wraplength=540,
            justify='center',
        ).pack(pady=4)

        def save():
            supplier = entries['supplier'].get().strip()
            number = entries['number'].get().strip()
            raw_date = entries['date'].get().strip()
            norm_date = normalize_date_de(raw_date)

            if not supplier:
                return self.show_warning('Angabe fehlt', 'Bitte geben Sie den Namen des Lieferanten ein.', parent=d)
            if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', norm_date):
                return self.show_warning(
                    'Datumsformat',
                    'Bitte geben Sie ein gültiges Rechnungsdatum ein (z. B. 15.03.2026).',
                    parent=d,
                )
            rc_val = combo_rc_manual.get()
            tax_id_val = entry_tax_id.get().strip()

            if rc_val == "EU" and not tax_id_val:
                return self.show_warning(
                    'USt-IdNr. fehlt',
                    'Bei einer EU-Reverse-Charge-Rechnung muss die USt-IdNr. des Lieferanten angegeben werden.',
                    parent=d,
                )
            net_str = entries['net'].get().strip()
            tax_str = entries['tax'].get().strip()
            gross_str = entries['gross'].get().strip()

            net = _d(net_str) if net_str else Decimal('0.00')
            tax = _d(tax_str) if tax_str else Decimal('0.00')
            gross = _d(gross_str) if gross_str else Decimal('0.00')

            rate_dec = _d(combo_vat.get(), '19.00')
            rate_factor = rate_dec / Decimal('100.00')

            if not net_str and not gross_str:
                return self.show_warning('Angabe fehlt', 'Bitte mindestens Netto oder Brutto eingeben.', parent=d)

            if net_str and not tax_str and not gross_str:
                tax = (net * rate_factor).quantize(Decimal('0.01'))
                gross = net + tax
            elif net_str and tax_str and not gross_str:
                gross = net + tax
            elif gross_str and not net_str and not tax_str:
                net = (gross / (Decimal('1.00') + rate_factor)).quantize(Decimal('0.01'))
                tax = gross - net
            elif gross_str and tax_str and not net_str:
                net = gross - tax
            elif net_str and gross_str and not tax_str:
                tax = gross - net

            if abs((net + tax) - gross) > Decimal('0.05'):
                return self.show_warning(
                    'Rechenfehler',
                    f'Netto ({net} €) + Steuer ({tax} €) stimmt nicht mit Brutto ({gross} €) überein!',
                    parent=d,
                )

            rate_key = str(int(rate_dec)) if rate_dec == int(rate_dec) else str(rate_dec)
            taxes_dict = {rate_key: tax} if tax != Decimal('0.00') else {}

            data = {
                'supplier': supplier,
                'supplier_country': entry_country.get().strip().upper() or 'DE',
                'supplier_tax_id': tax_id_val,
                'reverse_charge': rc_val,
                'account': combo_konto_manual.get().strip(),
                'number': number or 'ohne Nr.',
                'date': norm_date,
                'net': str(net),
                'tax': str(tax),
                'gross': str(gross),
                'taxes': taxes_dict,
                'delivery_date': '',
            }

            is_dup, dup_msg, _ = check_duplicate_incoming(
                path,
                self.p_config.get('eingangsjournal_ordner', ''),
                self.p_config.get('eingang_loesch_warteliste', []),
                invoice_data=data,
            )
            if is_dup:
                return self.show_error(
                    'Duplikat erkannt',
                    f'Diese Rechnung kann nicht erneut erfasst werden:\n\n{dup_msg}',
                    parent=d,
                )

            d.destroy()
            self._archive_incoming(path, kind.get(), data, None, False, bool(checked.get()))

        def skip():
            self.skipped_incoming_files.add(path)
            d.destroy()
            self.refresh_incoming_list()

        bf = ctk.CTkFrame(d, fg_color='transparent')
        bf.pack(pady=14)
        self.create_button(
            bf, text='Abbrechen / Zurückstellen', command=skip, fg_color='#666', width=180
        ).pack(side='left', padx=6)
        self.create_button(
            bf, text='Als Eingangsrechnung erfassen', command=save, fg_color='#208000', width=220
        ).pack(side='left', padx=6)

    def _archive_incoming(self, path, kind, data, xml, make_pdf, vat_checked):
        from eingangsrechnung import (
            next_number, write_journal, make_readable_pdf, _d, _money,
            normalize_date_de, file_sha256, check_duplicate_incoming
        )

        is_dup, dup_msg, _ = check_duplicate_incoming(
            path,
            self.p_config.get('eingangsjournal_ordner', ''),
            self.p_config.get('eingang_loesch_warteliste', []),
            invoice_data=data
        )
        if is_dup:
            self.show_error("Bereits erfasst", f"Erfassung abgebrochen, da die Rechnung bereits existiert:\n\n{dup_msg}")
            self.refresh_incoming_list()
            return

        f_hash = file_sha256(path)
        today_str = datetime.now().strftime('%d.%m.%Y')
        invoice_date = normalize_date_de(data.get('date', '')) or today_str
        year = invoice_date[-4:] if re.match(r'^\d{2}\.\d{2}\.\d{4}$', invoice_date) else str(datetime.now().year)

        nr = next_number(self.p_config.get('letzte_eingangsrechnungsnummer', ''), year)

        work = os.path.join(self.p_config['bearbeitete_eingangsrechnungen_ordner'], year)
        arch = os.path.join(self.p_config['eingangsrechnungen_ordner'], year)
        os.makedirs(work, exist_ok=True)
        os.makedirs(arch, exist_ok=True)

        ext = os.path.splitext(path)[1].lower() or '.dat'
        archive_main = os.path.join(arch, nr + ext)

        base_name = os.path.basename(path)
        work_target = os.path.join(work, base_name)
        if os.path.exists(work_target):
            work_target = os.path.join(work, f"{nr}_{base_name}")

        try:
            shutil.move(path, work_target)
        except Exception:
            shutil.copy2(path, work_target)
            wait = self.p_config.get('eingang_loesch_warteliste', []) or []
            if path not in wait:
                wait.append(path)
                self.p_config['eingang_loesch_warteliste'] = wait

        shutil.copy2(work_target if os.path.exists(work_target) else path, archive_main)

        if make_pdf:
            readable = os.path.join(arch, nr + '_Leseabschrift.pdf')
            try:
                make_readable_pdf(data, readable)
            except Exception as e:
                print(f"Leseabschrift konnte nicht erzeugt werden: {e}")

        taxes = data.get('taxes', {}) or {}
        t19 = _d(taxes.get('19', taxes.get('19.0', taxes.get('19.00', '0'))))
        t7 = _d(taxes.get('7', taxes.get('7.0', taxes.get('7.00', '0'))))
        other = _d(data.get('tax')) - t19 - t7

        record = {
            'Interne ER-Nr.': nr,
            'Eingangsdatum': today_str,
            'Rechnungsdatum': invoice_date,
            'Lieferant': data.get('supplier', ''),
            'Lieferant_Land': data.get('supplier_country', ''),
            'Lieferant_UStId': data.get('supplier_tax_id', ''),
            'Externe Rechnungsnummer': data.get('number', ''),
            'Format': kind,
            'Reverse_Charge': data.get('reverse_charge', 'Nein'),
            'Konto': data.get('account', ''),
            'Netto': _money(data.get('net')),
            'MwSt_19': _money(t19),
            'MwSt_7': _money(t7),
            'MwSt_sonstige': _money(other),
            'Brutto': _money(data.get('gross')),
            'Vorsteuer geprüft': 'Ja' if vat_checked else 'Nein',
            'Quelldatei': os.path.basename(path),
            'Archivdatei': archive_main,
            'Dateihash': f_hash,
        }

        write_journal(self.p_config['eingangsjournal_ordner'], record)
        self.p_config['letzte_eingangsrechnungsnummer'] = nr
        speichere_config(self.config)

        base_data_path = self.config.get("base_data_path", "")
        if base_data_path:
            firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_"))
            write_audit_log(firm_dir, "Eingang", "Erstellt", nr, f"Lieferant: {data.get('supplier', '')}", "GUI")

        if hasattr(self, 'lbl_letzte_er_nr'):
            self.lbl_letzte_er_nr.configure(text=nr)
        if hasattr(self, 'combo_eingang_jahr'):
            ej_path = self.p_config.get("eingangsjournal_ordner", "")
            if os.path.isdir(ej_path):
                years = sorted([x for x in os.listdir(ej_path) if re.fullmatch(r"\d{4}", x)], reverse=True)
                if years:
                    self.combo_eingang_jahr.configure(values=years)
                    self.combo_eingang_jahr.set(year if year in years else years[0])
        if hasattr(self, 'refresh_eingang_journal_ui'):
            self.refresh_eingang_journal_ui()

        self.skipped_incoming_files.discard(path)
        self.refresh_incoming_list()

        self.show_info(
            'Eingangsrechnung erfasst',
            f'Die Eingangsrechnung {nr} wurde erfolgreich erfasst und archiviert.\n\nArchiv: {archive_main}'
        )