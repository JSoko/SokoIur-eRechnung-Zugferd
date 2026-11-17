"""
tab_erfassen.py
---------------
Logik und Aufbau des Reiters "Erfassen" (Eingangsrechnungen prüfen).
"""
import os
import re
import shutil
import subprocess
from decimal import Decimal
from datetime import datetime
import customtkinter as ctk
import tkinter.messagebox as messagebox

from config import *
from utils import *
from crud import *
from audit import write_audit_log
from gui_utils import create_tooltip

class TabErfassenMixin:
    def build_erfassen_tab(self):
        if not hasattr(self, 'skipped_incoming_files'):
            self.skipped_incoming_files = set()

        f = ctk.CTkFrame(self.tab_erfassen)
        f.pack(pady=15, padx=20, fill="both", expand=True)

        ctk.CTkLabel(f, text="Eingangsrechnungen erfassen", font=("Helvetica", 16, "bold")).pack(pady=(12, 4))

        folder = self.p_config.get('eingangsordner', '')
        self.lbl_eingangsordner = ctk.CTkLabel(f, text=f"Eingangsordner (reneu): {folder}", wraplength=780, justify="center")
        self.lbl_eingangsordner.pack(padx=15, pady=2)

        ctk.CTkLabel(
            f,
            text="Die formelle und rechnerische Prüfung ist eine automatisierte Plausibilitätsprüfung und keine steuerliche oder rechtliche Freigabe.",
            text_color="orange", wraplength=780, justify="center"
        ).pack(pady=4)

        btn_bar = ctk.CTkFrame(f, fg_color="transparent")
        btn_bar.pack(pady=8)
        btn_next_in = self.create_button(btn_bar, text="📥 Nächste Eingangsrechnung prüfen", command=self.process_next_incoming, fg_color="#1f538d", hover_color="#14375d", height=36, width=260)
        btn_next_in.pack(side="left", padx=6)
        create_tooltip(btn_next_in, "Prüft die oberste Datei im Eingangsordner auf gesetzliche \nVorgaben und startet den Erfassungsprozess.")
        
        btn_ref_in = self.create_button(btn_bar, text="🔄 Liste aktualisieren", command=self.refresh_incoming_list, fg_color="#444", hover_color="#666", height=36, width=160)
        btn_ref_in.pack(side="left", padx=6)
        create_tooltip(btn_ref_in, "Sucht nach neu hinzugefügten Dateien im Eingangsordner.")
        
        btn_open_in = self.create_button(btn_bar, text="📂 Ordner öffnen", command=self.open_incoming_folder, fg_color="#444", hover_color="#666", height=36, width=140)
        btn_open_in.pack(side="left", padx=6)
        create_tooltip(btn_open_in, "Öffnet den Ordner (reneu) im Windows-Explorer, \num Dateien per Drag & Drop hineinzuziehen.")

        ctk.CTkLabel(f, text="Wartende Belege im Eingangsordner:", font=("Helvetica", 13, "bold")).pack(pady=(8, 2))
        self.incoming_scroll = ctk.CTkScrollableFrame(f, height=220)
        self.incoming_scroll.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkLabel(
            f,
            text="Nach der Erfassung wird das Original im Jahresordner „rebearb/<Jahr>“ archiviert; die nummerierte Archivkopie wird unter „rchn/<Jahr>“ gespeichert.",
            wraplength=750, justify="center", text_color="gray"
        ).pack(pady=6)

        self.refresh_incoming_list()

    def open_incoming_folder(self):
        folder = self.p_config.get('eingangsordner', '')
        if folder and os.path.isdir(folder):
            try:
                os.startfile(folder)
            except Exception:
                subprocess.Popen(['explorer', folder])
        else:
            messagebox.showwarning("Ordner fehlt", f"Der Ordner existiert noch nicht:\n{folder}")

    def _open_file_external(self, path):
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Datei konnte nicht geöffnet werden:\n{e}")

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
        if not hasattr(self, 'incoming_scroll'):
            return
        from eingangsrechnung import check_duplicate_incoming

        for w in self.incoming_scroll.winfo_children():
            w.destroy()

        self._retry_incoming_deletions()
        folder = self.p_config.get('eingangsordner', '')
        if not folder or not os.path.isdir(folder):
            ctk.CTkLabel(self.incoming_scroll, text="Eingangsordner noch nicht angelegt.", text_color="gray").pack(pady=15)
            return

        waiting_list = self.p_config.get('eingang_loesch_warteliste', []) or []
        norm_wait = {os.path.abspath(p) for p in waiting_list if p}

        # Dateien auf der Lösch-Warteliste werden direkt ausgeblendet, damit sie niemals doppelt erfasst werden
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
            return

        from eingangsrechnung import check_duplicate_incoming, load_all_journal_entries

        journal_folder = self.p_config.get('eingangsjournal_ordner', '')
        
        alle_journale = load_all_journal_entries(journal_folder)

        for idx, fpath in enumerate(files):
            row = ctk.CTkFrame(self.incoming_scroll)
            row.pack(fill="x", pady=2, padx=4)
            fname = os.path.basename(fpath)
            is_skipped = fpath in getattr(self, 'skipped_incoming_files', set())
            
            # NEU: Die Variable "alle_journale" per Parameter 'entries' übergeben
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

            lbl_kwargs = {"text": f"{idx+1}. {fname}{status_tag}", "anchor": "w"}
            if lbl_color:
                lbl_kwargs["text_color"] = lbl_color
            ctk.CTkLabel(row, **lbl_kwargs).pack(side="left", padx=10, pady=4, fill="x", expand=True)

            if is_dup:
                self.create_button(
                    row, text="🗑 Duplikat entfernen", width=140, fg_color="#b30000", hover_color="#800000",
                    command=lambda p=fpath: self._remove_duplicate_source_file(p)
                ).pack(side="right", padx=4, pady=4)

            self.create_button(
                row, text="👁 Öffnen", width=80, fg_color="#555", hover_color="#777",
                command=lambda p=fpath: self._open_file_external(p)
            ).pack(side="right", padx=4, pady=4)
            self.create_button(
                row, text="Prüfen", width=90, fg_color="#1f538d", hover_color="#14375d",
                command=lambda p=fpath: self.process_next_incoming(specific_path=p)
            ).pack(side="right", padx=4, pady=4)

    def process_next_incoming(self, specific_path=None):
        from eingangsrechnung import detect_invoice, parse_einvoice, error_notice, check_duplicate_incoming
        folder = self.p_config.get('eingangsordner', '')
        if not os.path.isdir(folder):
            return messagebox.showwarning('Eingangsordner fehlt', f'Der Eingangsordner existiert nicht:\n{folder}')

        self._retry_incoming_deletions()
        waiting_list = self.p_config.get('eingang_loesch_warteliste', []) or []
        norm_wait = {os.path.abspath(p) for p in waiting_list if p}

        files = sorted([
            os.path.join(folder, x) for x in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, x)) and not x.startswith('.') and os.path.abspath(os.path.join(folder, x)) not in norm_wait
        ])
        if not files:
            self.refresh_incoming_list()
            return messagebox.showinfo('Keine Eingangsrechnungen', f'Im Ordner\n{folder}\nsind keine unbearbeiteten Eingangsrechnungen vorhanden.')

        if specific_path and os.path.exists(specific_path):
            path = specific_path
        else:
            unskipped = [f for f in files if f not in getattr(self, 'skipped_incoming_files', set())]
            if not unskipped:
                self.skipped_incoming_files.clear()
                unskipped = files
            path = unskipped[0]

        journal_folder = self.p_config.get('eingangsjournal_ordner', '')

        # 1. Vorab-Duplikatsprüfung über Datei-Hash / Lösch-Warteliste
        is_dup, dup_msg, _ = check_duplicate_incoming(path, journal_folder, waiting_list)
        if is_dup:
            if messagebox.askyesno(
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
            # 2. Inhaltliche Duplikatsprüfung (Lieferant + Externe RE-Nr. + Bruttobetrag)
            is_dup_content, dup_msg_content, _ = check_duplicate_incoming(path, journal_folder, waiting_list, invoice_data=data)
            if is_dup_content:
                if messagebox.askyesno(
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
            self._show_other_invoice_form(path, detail)

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
        from eingangsrechnung import _money
        d = ctk.CTkToplevel(self)
        d.title('Eingangsrechnung prüfen und erfassen')
        self.center_window(d, 640, 560)
        d.transient(self)
        d.grab_set()

        ctk.CTkLabel(
            d, text=f'Gültige {kind}-Rechnung – Zusammenfassung',
            font=('Helvetica', 15, 'bold'), text_color='#208000'
        ).pack(pady=12)

        lines = [
            f"Quelldatei: {os.path.basename(path)}",
            f"Rechnungsaussteller: {data.get('supplier', '')}",
            f"Anschrift: {data.get('supplier_street', '')}, {data.get('supplier_zip', '')} {data.get('supplier_city', '')}".strip(", "),
            f"USt-IdNr. / StNr.: {data.get('supplier_tax_id', '')}",
            f"Rechnungsnummer: {data.get('number', '')}",
            f"Rechnungsdatum: {data.get('date', '')}",
            f"Leistungs-/Lieferdatum: {data.get('delivery_date', '') or '-'}",
            f"Fälligkeitsdatum: {data.get('due_date', '') or '-'}",
            f"Netto: {_money(data.get('net', '0'))} EUR",
            f"Umsatzsteuer: {_money(data.get('tax', '0'))} EUR",
            f"Brutto: {_money(data.get('gross', '0'))} EUR",
        ]
        ctk.CTkLabel(d, text='\n'.join(lines), justify='left').pack(padx=35, anchor='w')

        var = ctk.BooleanVar(value=bool(self.p_config.get('xrechnung_leseabschrift', True)))
        if kind == 'XRechnung':
            ctk.CTkCheckBox(d, text='Lesbare PDF-Leseabschrift im Archiv erstellen', variable=var).pack(pady=12)

        def yes():
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
        bf.pack(pady=20)
        self.create_button(bf, text='👁 Beleg ansehen', command=lambda: self._open_file_external(path), width=140, fg_color='#555').pack(side='left', padx=6)
        self.create_button(bf, text='Nein – zurückstellen', command=skip, width=160, fg_color='#666').pack(side='left', padx=6)
        self.create_button(bf, text='Ja – jetzt erfassen', command=yes, width=200, fg_color='#208000').pack(side='left', padx=6)

    def _show_other_invoice_form(self, path, detail='', prefill=None):
        from eingangsrechnung import _d, normalize_date_de, check_duplicate_incoming
        d = ctk.CTkToplevel(self)
        d.title('Sonstige Eingangsrechnung erfassen')
        self.center_window(d, 640, 680)
        d.transient(self)
        d.grab_set()

        ctk.CTkLabel(d, text='Erfassung einer Rechnung (Manuelle Ergänzung)', font=('Helvetica', 14, 'bold')).pack(pady=(12, 4))
        ctk.CTkLabel(d, text=f"Datei: {os.path.basename(path)} ({detail})", text_color="gray").pack(pady=(0, 8))

        self.create_button(d, text="👁 Originaldatei zur Ansicht öffnen", width=240, fg_color="#555", command=lambda: self._open_file_external(path)).pack(pady=4)

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

        if prefill:
            for k in ('supplier', 'number', 'date', 'net', 'tax', 'gross'):
                if prefill.get(k):
                    entries[k].insert(0, str(prefill.get(k)))
        else:
            entries['date'].insert(0, datetime.now().strftime('%d.%m.%Y'))

        checked = ctk.CTkCheckBox(d, text='Ich habe geprüft, dass diese Rechnung zum Vorsteuerabzug berechtigt')
        checked.pack(pady=10)

        ctk.CTkLabel(
            d,
            text='Hinweis: Mindestens Netto oder Brutto eingeben. Fehlende Beträge werden anhand des gewählten Steuersatzes berechnet.',
            text_color='orange', wraplength=540, justify='center'
        ).pack(pady=4)

        def save():
            supplier = entries['supplier'].get().strip()
            number = entries['number'].get().strip()
            raw_date = entries['date'].get().strip()
            norm_date = normalize_date_de(raw_date)

            if not supplier:
                return messagebox.showwarning('Angabe fehlt', 'Bitte geben Sie den Namen des Lieferanten ein.', parent=d)
            if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', norm_date):
                return messagebox.showwarning('Datumsformat', 'Bitte geben Sie ein gültiges Rechnungsdatum ein (z. B. 15.03.2026).', parent=d)

            net_str = entries['net'].get().strip()
            tax_str = entries['tax'].get().strip()
            gross_str = entries['gross'].get().strip()

            net = _d(net_str) if net_str else Decimal('0.00')
            tax = _d(tax_str) if tax_str else Decimal('0.00')
            gross = _d(gross_str) if gross_str else Decimal('0.00')

            rate_dec = _d(combo_vat.get(), '19.00')
            rate_factor = rate_dec / Decimal('100.00')

            if not net_str and not gross_str:
                return messagebox.showwarning('Angabe fehlt', 'Bitte mindestens Netto oder Brutto eingeben.', parent=d)

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
                return messagebox.showwarning(
                    'Rechenfehler',
                    f'Netto ({net} €) + Steuer ({tax} €) stimmt nicht mit Brutto ({gross} €) überein!',
                    parent=d
                )

            rate_key = str(int(rate_dec)) if rate_dec == int(rate_dec) else str(rate_dec)
            taxes_dict = {rate_key: tax} if tax != Decimal('0.00') else {}

            data = {
                'supplier': supplier,
                'number': number or 'ohne Nr.',
                'date': norm_date,
                'net': str(net),
                'tax': str(tax),
                'gross': str(gross),
                'taxes': taxes_dict,
                'delivery_date': ''
            }

            # Duplikatsprüfung vor dem Speichern
            is_dup, dup_msg, _ = check_duplicate_incoming(
                path,
                self.p_config.get('eingangsjournal_ordner', ''),
                self.p_config.get('eingang_loesch_warteliste', []),
                invoice_data=data
            )
            if is_dup:
                return messagebox.showerror(
                    'Duplikat erkannt',
                    f'Diese Rechnung kann nicht erneut erfasst werden:\n\n{dup_msg}',
                    parent=d
                )

            d.destroy()
            self._archive_incoming(path, kind.get(), data, None, False, bool(checked.get()))

        def skip():
            self.skipped_incoming_files.add(path)
            d.destroy()
            self.refresh_incoming_list()

        bf = ctk.CTkFrame(d, fg_color='transparent')
        bf.pack(pady=14)
        self.create_button(bf, text='Abbrechen / Zurückstellen', command=skip, fg_color='#666', width=180).pack(side='left', padx=6)
        self.create_button(bf, text='Als Eingangsrechnung erfassen', command=save, fg_color='#208000', width=220).pack(side='left', padx=6)

    def _archive_incoming(self, path, kind, data, xml, make_pdf, vat_checked):
        from eingangsrechnung import (
            next_number, write_journal, make_readable_pdf, _d, _money,
            normalize_date_de, file_sha256, check_duplicate_incoming
        )

        # Letzte Sicherheitsbarriere gegen doppelte Erfassung unmittelbar vor Nummernvergabe
        is_dup, dup_msg, _ = check_duplicate_incoming(
            path,
            self.p_config.get('eingangsjournal_ordner', ''),
            self.p_config.get('eingang_loesch_warteliste', []),
            invoice_data=data
        )
        if is_dup:
            messagebox.showerror("Bereits erfasst", f"Erfassung abgebrochen, da die Rechnung bereits existiert:\n\n{dup_msg}")
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
            'Externe Rechnungsnummer': data.get('number', ''),
            'Format': kind,
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

        messagebox.showinfo(
            'Eingangsrechnung erfasst',
            f'Die Eingangsrechnung {nr} wurde erfolgreich erfasst und archiviert.\n\nArchiv: {archive_main}'
        )
