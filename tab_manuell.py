"""
tab_manuell.py
--------------
Logik und Aufbau des Reiters "Erstellen" (Manuelle Rechnungseingabe).
"""
import os
import re
import csv
import shutil
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import filedialog

from config import *
from utils import *
from crud import *
from audit import write_audit_log
from gui_utils import create_tooltip, setup_auto_scrollbar, update_scrollable_visibility


class TabManuellMixin:
    def open_produkt_search(self, entry_widget=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Artikel auswählen")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(dialog)
        self.center_window(dialog, 520, 480)
        dialog.transient(self)
        dialog.grab_set()

        f_search = ctk.CTkFrame(dialog, fg_color="transparent")
        f_search.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(f_search, text="Artikel-Filter:").pack(side="left")
        e_search = ctk.CTkEntry(f_search, placeholder_text="Bezeichnung filtern...")
        e_search.pack(side="left", fill="x", expand=True, padx=10)

        if entry_widget:
            bisheriger_text = entry_widget.get().strip()
            if bisheriger_text:
                e_search.insert(0, bisheriger_text)

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        setup_auto_scrollbar(scroll)

        def select_produkt(p):
            if entry_widget is not None:
                entry_widget.delete(0, "end")
                entry_widget.insert(0, p.get("Bezeichnung", ""))
            dialog.destroy()

        current_results = []

        def update_list(event=None):
            if event and event.keysym in ["Up", "Down", "Return", "Escape"]:
                return

            term = e_search.get().lower().strip()
            for w in scroll.winfo_children():
                w.destroy()

            sorted_prods = sorted(
                self.produkte_liste or [],
                key=lambda x: str(x.get("Bezeichnung", "")).strip().lower(),
            )

            if not term:
                results = sorted_prods
            else:
                starts = [p for p in sorted_prods if term in str(p.get("Bezeichnung", "")).lower() and str(p.get("Bezeichnung", "")).strip().lower().startswith(term)]
                contains = [p for p in sorted_prods if term in str(p.get("Bezeichnung", "")).lower() and p not in starts]
                results = starts + contains

            nonlocal current_results
            current_results = results[:100]
            btn_list = []

            for p in current_results:
                bez = p.get("Bezeichnung", "")
                preis = safe_float(p.get("EinzelpreisNetto", 0))
                ust = f_num(safe_float(p.get("Steuersatz", 19)))
                lbl = f"{bez}  |  {f_curr(preis)} netto ({ust}% USt.)"
                btn = ctk.CTkButton(
                    scroll,
                    text=lbl,
                    anchor="w",
                    fg_color="#444",
                    hover_color="#666",
                    command=lambda p_obj=p: select_produkt(p_obj),
                )
                btn.pack(fill="x", pady=2)
                btn_list.append(btn)

            if not current_results:
                ctk.CTkLabel(scroll, text="Keine passenden Artikel gefunden.", text_color="gray").pack(pady=15)
            elif len(results) > 100:
                ctk.CTkLabel(
                    scroll,
                    text=f"... und {len(results) - 100} weitere. Bitte Filter verfeinern.",
                    text_color="gray",
                ).pack(pady=5)

            for i, b in enumerate(btn_list):
                if i < len(btn_list) - 1:
                    b.bind("<Down>", lambda e, next_b=btn_list[i + 1]: next_b.focus_set())
                if i > 0:
                    b.bind("<Up>", lambda e, prev_b=btn_list[i - 1]: prev_b.focus_set())
                else:
                    b.bind("<Up>", lambda e: e_search.focus_set())
                b.bind("<Return>", lambda e, p_obj=current_results[i]: select_produkt(p_obj))

            update_scrollable_visibility(scroll)

        e_search.bind("<KeyRelease>", update_list)
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        def focus_first_result(event):
            for w in scroll.winfo_children():
                if isinstance(w, ctk.CTkButton):
                    w.focus_set()
                    return "break"

        e_search.bind("<Down>", focus_first_result)

        def on_enter_search(event):
            if len(current_results) == 1:
                select_produkt(current_results[0])
                return "break"
            if len(current_results) > 1:
                return focus_first_result(event)

        e_search.bind("<Return>", on_enter_search)
        dialog.bind("<Return>", on_enter_search)

        update_list()
        dialog.after(50, e_search.focus_set)

    def _warn(self, title, msg, parent=None):
        if hasattr(self, "show_warning"):
            return self.show_warning(title, msg, parent=parent)
        return messagebox.showwarning(title, msg, parent=parent)

    def _err(self, title, msg, parent=None):
        if hasattr(self, "show_error"):
            return self.show_error(title, msg, parent=parent)
        return messagebox.showerror(title, msg, parent=parent)

    def _yesno(self, title, msg, parent=None, default="yes"):
        if hasattr(self, "ask_yes_no"):
            return self.ask_yes_no(title, msg, parent=parent, default=default)
        return messagebox.askyesno(title, msg, parent=parent, default=default)

    def send_invoice_email(self):
        """Zentrale Methode für den E-Mail-Versand nach erfolgreicher PDF-Erstellung."""
        if not self.chk_email_versand.get():
            return

        import subprocess
        import urllib.parse
        buyer_endpoint = self.entry_k_endpoint.get().strip()
        if not buyer_endpoint or '@' not in buyer_endpoint:
            return

        try:
            r_nr = self.entry_r_nr.get().strip()
            az_val = self.entry_az.get().strip()
            k_az_val = self.entry_k_az.get().strip()

            betreff_teile = []
            if az_val:
                betreff_teile.append(f"Unser Zeichen: {az_val}")
            if k_az_val:
                betreff_teile.append(f"Ihr Zeichen: {k_az_val}")
            betreff_teile.append(f"Rechnung Nr. {r_nr}")

            subject = " - ".join(betreff_teile)
            body = (
                "Sehr geehrte Damen und Herren,\n\n"
                "anbei übersenden wir e-Rechnung mit der Bitte um Ausgleich."
            )

            # Pfad zur frisch generierten PDF-Datei im Jahresordner ermitteln
            akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
            ausgabe_basis = self.p_config.get('ausgabe_ordner', '')

            mögliche_pfade = [
                os.path.join(ausgabe_basis, akt_jahr, f"Rechnung_{r_nr}.pdf"),
                os.path.join(ausgabe_basis, akt_jahr, f"Rechnung_{r_nr}_Begleit.pdf"),
                os.path.join(ausgabe_basis, f"Rechnung_{r_nr}.pdf"),
                os.path.join(ausgabe_basis, f"Rechnung_{r_nr}_Begleit.pdf")
            ]

            abs_pdf = ""
            for pfad_kandidat in mögliche_pfade:
                if os.path.exists(pfad_kandidat):
                    abs_pdf = os.path.abspath(pfad_kandidat)
                    break

            if not abs_pdf:
                print("E-Mail-Versand abgebrochen: PDF-Datei wurde im Ausgabeordner nicht gefunden.")
                return

            methode = self.p_config.get("email_versand_methode", "Keine")
            gesendet = False

            if methode == "Outlook":
                try:
                    import win32com.client as win32
                    outlook = win32.Dispatch('outlook.application')
                    mail = outlook.CreateItem(0)
                    mail.To = buyer_endpoint
                    mail.Subject = subject
                    mail.Body = body
                    if os.path.exists(abs_pdf):
                        mail.Attachments.Add(abs_pdf)
                    mail.Display(True)
                    gesendet = True
                except Exception as e:
                    print(f"Outlook COM Fehler: {e}")

            elif methode == "Thunderbird":
                try:
                    # 1. Body und Footer aus den Firmeneinstellungen zusammenführen
                    konfig_body = self.p_config.get("email_body", "Sehr geehrte Damen und Herren,\n\nanbei übersenden wir e-Rechnung mit der Bitte um Ausgleich.")
                    konfig_footer = self.p_config.get("email_footer", "").strip()

                    body = konfig_body
                    if konfig_footer:
                        body += f"\n\n{konfig_footer}"

                    # 2. Thunderbird-Pfad ermitteln
                    tb_executable = self.p_config.get("thunderbird_pfad", "").strip().strip('"\'')
                    if not tb_executable or not os.path.exists(tb_executable):
                        for p in [
                            r"C:\Program Files\Mozilla Thunderbird\thunderbird.exe",
                            r"C:\Program Files (x86)\Mozilla Thunderbird\thunderbird.exe",
                            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Mozilla Thunderbird\thunderbird.exe")
                        ]:
                            if os.path.exists(p):
                                tb_executable = p
                                break

                    if tb_executable and os.path.exists(tb_executable) and os.path.exists(abs_pdf):
                        safe_pdf = os.path.abspath(abs_pdf)

                        # 3. Übergabe als saubere Parameter-Liste (ohne shell=True).
                        # Das verhindert, dass Zeilenumbrüche den Befehl abbrechen oder Pfade verschluckt werden!
                        compose_arg = f"to='{buyer_endpoint}',subject='{subject}',body='{body}',attachment='{safe_pdf}'"

                        subprocess.Popen([tb_executable, "-compose", compose_arg])
                        gesendet = True
                    else:
                        os.startfile(abs_pdf)
                        gesendet = True
                except Exception as e:
                    print(f"Thunderbird Compose Fehler: {e}")
                    gesendet = True

            # Fallback falls kein Client greift
            if not gesendet:
                mailto_url = f"mailto:{urllib.parse.quote(buyer_endpoint)}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                webbrowser.open(mailto_url)
                if os.path.exists(abs_pdf):
                    subprocess.Popen(['explorer', '/select,', abs_pdf])
        except Exception as e:
            print(f"Fehler beim E-Mail-Versand: {e}")

    def on_main_text_vorlage_change(self, wahl):
        vorlagen = self.p_config.get("text_vorlagen", {})
        if wahl in vorlagen:
            v = vorlagen[wahl]
            self.header_text = v.get("header", "")
            self.einleitung_text = v.get("einleitung", "")
            self.vor_gruss_text = v.get("vor_gruss", "")
            self.gruss_text = v.get("gruss", "")
            self.p_config["zahlungsbedingungen_default"] = v.get("zahlungsbedingungen", "")
            self.p_config["rechnungsvermerk_default"] = v.get("rechnungsvermerk", "")
            self.p_config["aktive_text_vorlage"] = wahl
            self.aktive_text_vorlage = wahl

            speichere_textdatei(self.p_config.get('header_csv'), self.header_text)
            speichere_textdatei(self.p_config.get('einleitung_csv'), self.einleitung_text)
            speichere_textdatei(self.p_config.get('vor_gruss_csv'), getattr(self, 'vor_gruss_text', ''))
            speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)
            speichere_config(self.config)

    def open_date_picker(self, entry_widget):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Leistungszeitraum wählen")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(dialog)
        self.center_window(dialog, 400, 250)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Datums- oder Zeitraumeingabe", font=("Helvetica", 14, "bold")).pack(pady=10)
        f_start = ctk.CTkFrame(dialog, fg_color="transparent")
        f_start.pack(pady=5)
        ctk.CTkLabel(f_start, text="Startdatum:", width=120).pack(side="left")
        e_start = ctk.CTkEntry(f_start, width=150)
        e_start.pack(side="left")

        f_end = ctk.CTkFrame(dialog, fg_color="transparent")
        f_end.pack(pady=5)
        ctk.CTkLabel(f_end, text="Enddatum (opt.):", width=120).pack(side="left")
        e_end = ctk.CTkEntry(f_end, width=150)
        e_end.pack(side="left")

        existing = entry_widget.get().strip()
        if "|" in existing:
            s, e = existing.split('|')
            e_start.insert(0, s)
            e_end.insert(0, e)
        else:
            e_start.insert(0, existing)

        def fill_today(widget):
            widget.delete(0, 'end')
            widget.insert(0, datetime.now().strftime("%Y-%m-%d"))

        f_btn = ctk.CTkFrame(dialog, fg_color="transparent")
        f_btn.pack(pady=10)
        self.create_button(f_btn, text="Start = Heute", width=110, command=lambda: fill_today(e_start)).pack(side="left", padx=5)
        self.create_button(f_btn, text="Ende = Heute", width=110, command=lambda: fill_today(e_end)).pack(side="left", padx=5)

        def save_date():
            s = parse_flexible_date(e_start.get())
            e = parse_flexible_date(e_end.get())
            try:
                if s:
                    datetime.strptime(s, "%Y-%m-%d")
                if e:
                    datetime.strptime(e, "%Y-%m-%d")
            except ValueError:
                return self._err("Fehler", "Datumsformat nicht erkannt!", parent=dialog)
            res = f"{s}|{e}" if (s and e) else (s or e)
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, res)
            dialog.destroy()

        self.create_button(dialog, text="Übernehmen", command=save_date).pack(pady=10)

    def choose_and_load_csv(self):
        akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        are_dir = self.p_config.get("ausgabe_ordner", "")

        if are_dir:
            start_dir = os.path.join(os.path.dirname(are_dir), "arecsv", akt_jahr)
        else:
            start_dir = os.path.dirname(self.p_config.get('rechnung_csv', ''))

        if not os.path.exists(start_dir):
            start_dir = os.path.dirname(self.p_config.get('rechnung_csv', ''))
            if not os.path.exists(start_dir):
                start_dir = os.getcwd()

        pfad = filedialog.askopenfilename(
            title="Rechnungs-CSV wählen",
            initialdir=start_dir,
            filetypes=[("CSV-Dateien", "*.csv*"), ("Alle Dateien", "*.*")]
        )
        if pfad:
            ensure_utf8_csv(pfad)
            self.load_manual_invoice(is_button_click=True, custom_path=pfad)

    def open_kunde_search(self, entry_widget=None, mode="name"):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Kunde suchen" if mode == "name" else "Nach Kundennummer suchen")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(dialog)
        self.center_window(dialog, 500, 500)
        dialog.transient(self)
        dialog.grab_set()

        f_search = ctk.CTkFrame(dialog, fg_color="transparent")
        f_search.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(f_search, text="Suchbegriff:").pack(side="left")
        e_search = ctk.CTkEntry(f_search, placeholder_text="Name, Nr. oder Ort...")
        e_search.pack(side="left", fill="x", expand=True, padx=10)

        if entry_widget:
            bisheriger_text = entry_widget.get().strip()
            if bisheriger_text:
                e_search.insert(0, bisheriger_text)

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        setup_auto_scrollbar(scroll)

        def select_kunde(k):
            self.entry_k_name.set(k.get('Name', ''))
            self.entry_k_strasse.delete(0, 'end')
            self.entry_k_strasse.insert(0, k.get('Strasse', ''))
            self.entry_k_plz_ort.delete(0, 'end')
            self.entry_k_plz_ort.insert(0, k.get('PLZ_Ort', ''))
            self.entry_k_nr.delete(0, 'end')
            self.entry_k_nr.insert(0, k.get('KundeNr', ''))
            self.entry_az.delete(0, 'end')
            self.entry_az.insert(0, k.get('Aktenzeichen', ''))
            self.entry_k_endpoint.delete(0, 'end')
            self.entry_k_endpoint.insert(0, k.get('Endpoint', k.get('Email', '')))
            self.entry_k_endpoint_scheme.delete(0, 'end')
            self.entry_k_endpoint_scheme.insert(0, k.get('EndpointScheme', ''))
            if k.get('UStId', '').strip():
                self.entry_k_ustid.delete(0, 'end')
                self.entry_k_ustid.insert(0, k.get('UStId', '').strip())
            dialog.destroy()
            self.check_live_validation()

        current_results = []

        def update_list(event=None):
            if event and event.keysym in ['Up', 'Down', 'Return', 'Escape']:
                return

            term = e_search.get().lower().strip()
            for w in scroll.winfo_children():
                w.destroy()

            results = []
            for k in self.kunden_liste:
                if not term:
                    if mode == "nr" and not k.get('KundeNr', '').strip():
                        continue
                    results.append(k)
                else:
                    if (
                        term in k.get('Name', '').lower()
                        or term in k.get('KundeNr', '').lower()
                        or term in k.get('PLZ_Ort', '').lower()
                    ):
                        results.append(k)

            nonlocal current_results
            current_results = results[:100]
            btn_list = []

            for k in current_results:
                lbl = f"[{k.get('KundeNr', '-')}] {k.get('Name', '')} | {k.get('PLZ_Ort', '')}"
                btn = ctk.CTkButton(scroll, text=lbl, anchor="w", fg_color="#444", hover_color="#666", command=lambda k_obj=k: select_kunde(k_obj))
                btn.pack(fill="x", pady=2)
                btn_list.append(btn)

            if len(results) > 100:
                ctk.CTkLabel(scroll, text=f"... und {len(results)-100} weitere. Bitte Suchbegriff verfeinern.", text_color="gray").pack(pady=5)

            for i, b in enumerate(btn_list):
                if i < len(btn_list) - 1:
                    b.bind('<Down>', lambda e, next_b=btn_list[i+1]: next_b.focus_set())
                if i > 0:
                    b.bind('<Up>', lambda e, prev_b=btn_list[i-1]: prev_b.focus_set())
                else:
                    b.bind('<Up>', lambda e: e_search.focus_set())
                b.bind('<Return>', lambda e, k_obj=current_results[i]: select_kunde(k_obj))

            update_scrollable_visibility(scroll)

        e_search.bind('<KeyRelease>', update_list)
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        def focus_first_result(event):
            children = scroll.winfo_children()
            for w in children:
                if isinstance(w, ctk.CTkButton):
                    w.focus_set()
                    break

        e_search.bind('<Down>', focus_first_result)

        def on_enter_search(event):
            if len(current_results) == 1:
                select_kunde(current_results[0])

        e_search.bind('<Return>', on_enter_search)
        dialog.bind('<Return>', on_enter_search)

        update_list()
        dialog.after(50, e_search.focus_set)

    def update_totals_ui(self):
        g_netto, g_steuer, g_brutto, steuer_gruppen = berechne_summen(self.positionen_liste)

        teile_einzel = [f"Netto {f_curr(g_netto)}"]

        for st, n_sum in sorted(steuer_gruppen.items()):
            s_wert = round_kaufm(n_sum * (st / 100.0))
            teile_einzel.append(f"{f_num(st)}% USt.: {f_curr(s_wert)}")

        teile_einzel.append(f"Brutto {f_curr(g_brutto)}")

        if hasattr(self, "lbl_totals_top") and self.lbl_totals_top.winfo_exists():
            avail_w = self.lbl_totals_top.winfo_width()
            if avail_w > 120:
                self.lbl_totals_top.configure(wraplength=avail_w)
            self.lbl_totals_top.configure(text=" | ".join(teile_einzel))

    def on_rc_change(self, wahl):
        if wahl in ("EU", "Drittland") and self.positionen_liste:
            if self._yesno("Steuersatz anpassen", f"Reverse Charge ({wahl}) gewählt.\nSollen alle vorhandenen Positionen auf 0% USt. umgestellt werden?"):
                for p in self.positionen_liste:
                    p['Steuersatz'] = '0'
                self.refresh_pos_list()
        self.check_live_validation()

    def build_manuell_tab(self):
        # Undo/Redo Stacks initialisieren
        if not hasattr(self, 'undo_stack'):
            self.undo_stack = []
        if not hasattr(self, 'redo_stack'):
            self.redo_stack = []
        if not hasattr(self, '_is_restoring'):
            self._is_restoring = False

        left_frame = ctk.CTkScrollableFrame(self.tab_manuell, width=370)
        left_frame.pack(side="left", fill="y", padx=(0, 0), pady=3)
        setup_auto_scrollbar(left_frame)

        right_frame = ctk.CTkFrame(self.tab_manuell)
        right_frame.pack(side="right", fill="both", expand=True, padx=(0, 0), pady=3)

        f_load_btns = ctk.CTkFrame(left_frame, fg_color="transparent")
        f_load_btns.pack(pady=(2, 2), padx=2, fill="x")

        btn_load = self.create_button(
            f_load_btns,
            text="Letzte Rechnung (ALT+L)",
            command=lambda: self.load_manual_invoice(is_button_click=True),
            fg_color="#444",
            hover_color="#666",
        )
        btn_load.pack(side="left", fill="x", expand=True, padx=(0, 4))
        create_tooltip(btn_load, "Lädt den zuletzt bearbeiteten Rechnungsentwurf der aktuellen Firma.")

        btn_choose = self.create_button(
            f_load_btns,
            text="Rechnung wählen",
            command=self.choose_and_load_csv,
            fg_color="#444",
            hover_color="#666",
        )
        btn_choose.pack(side="left", fill="x", expand=True, padx=(0, 0))
        create_tooltip(btn_choose, "Lädt eine alte Rechnung oder einen Entwurf aus einer CSV-Datei.")

        # Auswahlbox Textvorlage mit Button "Texteditor" links daneben direkt unter den Lade-Buttons
        f_txt_vorlage = ctk.CTkFrame(left_frame, fg_color="transparent")
        f_txt_vorlage.pack(fill="x", padx=10, pady=(2, 10))
        self.create_button(
            f_txt_vorlage,
            text="Texteditor",
            width=120,
            command=self.open_texte_popup,
        ).pack(side="left")
        vorlagen_namen = list(self.p_config.get("text_vorlagen", {"Standard": {}}).keys())
        self.combo_text_vorlage_main = ctk.CTkComboBox(
            f_txt_vorlage,
            values=vorlagen_namen,
            command=self.on_main_text_vorlage_change,
        )
        self.combo_text_vorlage_main.set(self.p_config.get("aktive_text_vorlage", "Standard"))
        self.combo_text_vorlage_main.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.entry_r_nr = self.create_input(left_frame, "Rechnungs-Nr.")
        self.entry_r_datum = self.create_input(left_frame, "Rechnungsdatum")
        self.entry_f_datum = self.create_input(left_frame, "Fälligkeit")

        self.entry_k_nr = self.create_input_with_button(left_frame, "Kunden-Nr. (opt.)", "🔍", lambda e: self.open_kunde_search(e, mode="nr"))
        self.entry_k_nr.bind('<Return>', lambda e: self.open_kunde_search(self.entry_k_nr, mode="nr"))
        self.entry_az = self.create_input(left_frame, "Unser Zeichen (opt.)")
        self.entry_k_az = self.create_input(left_frame, "Ihr Zeichen")
        self.entry_lz_kopf = self.create_input_with_button(left_frame, "Leistungszeitraum", "📅", self.open_date_picker)
        self.entry_k_name = self.create_input_with_button(left_frame, "Kunde Name", "🔍", lambda e: self.open_kunde_search(e, mode="name"))
        self.entry_k_name.bind('<Return>', lambda e: self.open_kunde_search(self.entry_k_name, mode="name"))
        self.entry_k_strasse = self.create_input(left_frame, "Kunde Straße")
        self.entry_k_plz_ort = self.create_input(left_frame, "PLZ Ort")
        self.entry_k_land = self.create_input(left_frame, "Land (z.B. DE, AT, US)")
        self.entry_k_land.insert(0, "DE")
        self.combo_rc = self.create_input(
            left_frame, "Reverse Charge", is_combo=True,
            combo_values=["Nein", "EU", "Drittland"], command=self.on_rc_change
        )
        self.combo_rc.set("Nein")
        self.entry_k_ustid = self.create_input(left_frame, "Kunde USt-IdNr.")
        self.entry_k_endpoint = self.create_input(left_frame, "E-Mail / Leitweg-ID")
        self.entry_k_endpoint_scheme = self.create_input(left_frame, "Endpoint-Schema (z. B. 0204)")

        f_left_checks = ctk.CTkFrame(left_frame, fg_color="transparent")
        f_left_checks.pack(fill="x", padx=10, pady=(6, 4))

        chk_kwargs = {
            "height": 20,
            "checkbox_width": 16,
            "checkbox_height": 16,
            "corner_radius": 4,
            "font": ("Helvetica", 12),
        }

        self.chk_kunde_speichern = ctk.CTkCheckBox(f_left_checks, text="Kundendaten speichern und aktualisieren", **chk_kwargs)
        self.chk_kunde_speichern.pack(anchor="w", pady=(0, 3))
        if self.p_config.get("keep_kunde_speichern", False):
            self.chk_kunde_speichern.select()
        create_tooltip(self.chk_kunde_speichern, "Kundendaten nach dem erfassen speichern bzw. aktualisieren")

        self.chk_email_versand = ctk.CTkCheckBox(f_left_checks, text="E-Mailversand bei Rechnungserstellung anstoßen", **chk_kwargs)
        self.chk_email_versand.pack(anchor="w", pady=(0, 3))
        if self.p_config.get("keep_email_versand", False):
            self.chk_email_versand.select()
        create_tooltip(self.chk_email_versand, "Bei Erstellen einer Rechnung deren E-Mailversand anstoßen")

        self.chk_raten = ctk.CTkCheckBox(f_left_checks, text="Dem Kunden Ratenzahlung anbieten", **chk_kwargs)
        self.chk_raten.pack(anchor="w")
        if self.p_config.get("keep_raten", False):
            self.chk_raten.select()
        create_tooltip(self.chk_raten, "Einen Hinweis auf mögliche Ratenzahlung in die Rechnung aufnehmen")

        # Live-Validierung an Eingabefelder binden (inkl. E-Mail / Leitweg-ID)
        for entry_widget in (
            self.entry_r_nr, self.entry_r_datum, self.entry_f_datum, self.entry_k_name,
            self.entry_k_strasse, self.entry_k_plz_ort, self.entry_k_land, self.entry_k_ustid,
            self.entry_k_endpoint, self.entry_k_az, self.entry_lz_kopf
        ):
            if hasattr(entry_widget, 'bind'):
                entry_widget.bind('<KeyRelease>', self.check_live_validation)

        self.after(100, self.check_live_validation)
        self.after(120, lambda: update_scrollable_visibility(left_frame))

        # Live-Hinweise rechts oberhalb der Netto-/Brutto-Zeile
        self.lbl_live_errors = ctk.CTkLabel(
            right_frame,
            text="",
            anchor="w",
            justify="left",
            font=("Helvetica", 13, "bold"),
            text_color="#b30000",
            fg_color=("#e6e6e6", "#3a3d42"),
            corner_radius=6,
            wraplength=480,
        )
        self.lbl_live_errors.pack(fill="x", padx=5, pady=(3, 2), ipadx=8, ipady=4)

        # Rechnungsergebnisse
        self.lbl_totals_top = ctk.CTkLabel(
            right_frame,
            text="Netto 0,00 € | Brutto 0,00 €",
            anchor="w",
            justify="left",
            wraplength=480,
            font=("Helvetica", 12, "bold"),
            text_color=("#1f538d", "#6cb2ff"),
        )
        self.lbl_totals_top.pack(fill="x", padx=5, pady=(2, 0))

        def _update_top_totals_wrap(event=None):
            if not right_frame.winfo_exists():
                return
            avail_w = right_frame.winfo_width() - 36
            if avail_w > 120:
                if hasattr(self, "lbl_totals_top") and self.lbl_totals_top.winfo_exists():
                    self.lbl_totals_top.configure(wraplength=avail_w)
                if hasattr(self, "lbl_live_errors") and self.lbl_live_errors.winfo_exists():
                    self.lbl_live_errors.configure(wraplength=avail_w)

        right_frame.bind("<Configure>", _update_top_totals_wrap, add="+")
        self.after(60, _update_top_totals_wrap)

        self.pos_scroll = ctk.CTkScrollableFrame(right_frame)
        self.pos_scroll.pack(fill="both", expand=True, padx=1, pady=1)
        setup_auto_scrollbar(self.pos_scroll)

        f_split_btns = ctk.CTkFrame(right_frame, fg_color="transparent")
        f_split_btns.pack(pady=1, fill="x", padx=2)
        f_split_btns.columnconfigure(0, weight=2, minsize=145)
        for col in range(1, 4):
            f_split_btns.columnconfigure(col, weight=1, minsize=50)

        btn_add_pos = self.create_button(f_split_btns, text="Pos.hinzufügen (+)", width=1, command=self.open_pos_popup)
        btn_add_pos.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        create_tooltip(btn_add_pos, "Eine Rechnungsposition hinzufügen")

        btn_test = self.create_button(f_split_btns, text="Testrechnung", width=1, fg_color="#6c757d", hover_color="#5a6268", command=self.generate_testrechnung)
        btn_test.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        create_tooltip(btn_test, "Erstellt eine Vorschau (PDF) im Temp-Ordner.\nVergibt keine Rechnungsnummer, erzeugt kein Journal und schließt das Programm nicht.")

        btn_papier = self.create_button(f_split_btns, text="Papier-PDF", width=1, fg_color="#FFF2A8", text_color="#3D3200", hover_color="#E6D77A", command=self.save_generate_papierrechnung_exit)
        btn_papier.grid(row=0, column=2, sticky="ew", padx=(5, 5))
        create_tooltip(btn_papier, "Erstellt ein reines Sicht-PDF ohne elektronische XML-Daten.\n(Nur als Übergangslösung empfohlen)")

        btn_xrech = self.create_button(f_split_btns, text="XRechnung", width=1, fg_color="#cccccc", text_color="#3D3200", hover_color="#ffffff", command=self.save_generate_xrechnung_exit)
        btn_xrech.grid(row=0, column=3, sticky="ew", padx=(5, 0))
        create_tooltip(btn_xrech, "Erzeugt eine XML-Datei für Behördenportale (Leitweg-ID erforderlich)\nund zusätzlich eine lesbare Leseabschrift (PDF) für Ihre Akten.")

        btn_zugferd = self.create_button(right_frame, text="Zugpferdrechnung erstellen & öffnen (Alt+P)", fg_color="#289102", hover_color="#5dc21c", command=self.save_generate_open_exit)
        btn_zugferd.pack(pady=2, fill="x", padx=2)
        create_tooltip(btn_zugferd, "Erzeugt eine ZUGFeRD Hybrid-PDF (PDF inkl. unsichtbarem XML).\nIdeal für Geschäftskunden (B2B) per E-Mail.")

        # Historie-Tracking an Eingabefelder binden
        kopf_felder = [
            self.entry_r_nr, self.entry_r_datum, self.entry_f_datum,
            self.entry_k_nr, self.entry_az, self.entry_k_az,
            self.entry_lz_kopf, self.entry_k_strasse,
            self.entry_k_plz_ort, self.entry_k_endpoint, self.entry_k_endpoint_scheme
        ]
        for entry in kopf_felder:
            if hasattr(entry, 'bind'):
                entry.bind('<FocusOut>', lambda e: self.save_state_to_history())
                entry.bind('<Return>', lambda e: self.save_state_to_history())
        if hasattr(self.entry_k_name, 'bind'):
            self.entry_k_name.bind('<FocusOut>', lambda e: self.save_state_to_history())

    def load_manual_invoice(self, is_button_click=False, silent=False, custom_path=None):
        rech_pfad = custom_path if custom_path else self.p_config.get('rechnung_csv', '')
        if not os.path.exists(rech_pfad):
            if not silent:
                self._warn("Fehler", f"Datei {rech_pfad} nicht gefunden.")
            return
        try:
            with open(rech_pfad, mode='r', encoding='utf-8-sig') as f:
                reader = list(csv.DictReader(f, delimiter=';'))
                if not reader:
                    if not silent:
                        self._warn("Fehler", "Die CSV-Datei ist leer.")
                    return

                kopf = reader[0]
                geladene_nr = kopf.get('Rechnungsnummer', '')

                if not is_button_click and self.config.get("cli_renr"):
                    geladene_nr = self.config.get("cli_renr")

                ziel_nr = geladene_nr

                if is_button_click and geladene_nr:
                    frage_text = f"Die Rechnungsnummer {geladene_nr} wurde geladen.\nUm eins erhöhen oder beibehalten?"
                    if hasattr(self, "_show_custom_dialog"):
                        erhoehen = bool(
                            self._show_custom_dialog(
                                "Rechnungsnummer",
                                frage_text,
                                kind="ask",
                                buttons=("Erhöhen", "Beibehalten"),
                                default_index=0,
                            )
                        )
                    else:
                        erhoehen = self._yesno("Rechnungsnummer", frage_text)

                    if erhoehen:
                        ziel_nr = berechne_naechste_rechnungsnummer(geladene_nr)

                self.entry_r_nr.delete(0, 'end')
                self.entry_r_nr.insert(0, ziel_nr)
                self.entry_r_datum.delete(0, 'end')
                self.entry_r_datum.insert(0, kopf.get('Rechnungsdatum', ''))
                self.entry_f_datum.delete(0, 'end')
                self.entry_f_datum.insert(0, kopf.get('Faelligkeitsdatum', ''))
                self.entry_k_name.set(kopf.get('KundeName', ''))
                self.entry_k_strasse.delete(0, 'end')
                self.entry_k_strasse.insert(0, kopf.get('KundeStrasse', ''))
                if str(kopf.get('Ratenzahlung', '')).lower() in ['true', '1', 'ja', 'yes']:
                    self.chk_raten.select()
                else:
                    self.chk_raten.deselect()
                self.entry_k_nr.delete(0, 'end')
                self.entry_k_nr.insert(0, kopf.get('KundeNr', ''))
                self.entry_az.delete(0, 'end')
                self.entry_az.insert(0, kopf.get('Aktenzeichen', ''))
                self.entry_k_az.delete(0, 'end')
                self.entry_k_az.insert(0, self.config.get("cli_kunde_az", kopf.get('KundeAktenzeichen', '')))
                self.entry_lz_kopf.delete(0, 'end')
                self.entry_lz_kopf.insert(0, kopf.get('LeistungszeitraumKopf', ''))
                self.entry_k_plz_ort.delete(0, 'end')
                self.entry_k_plz_ort.insert(0, f"{kopf.get('KundePLZ', '')} {kopf.get('KundeOrt', '')}".strip())
                self.entry_k_endpoint.delete(0, 'end')
                self.entry_k_endpoint.insert(0, kopf.get('KundeEndpoint', kopf.get('KundeEmail', '')))
                self.entry_k_endpoint_scheme.delete(0, 'end')
                self.entry_k_endpoint_scheme.insert(0, kopf.get('KundeEndpointScheme', ''))
                self.entry_k_land.delete(0, 'end')
                self.entry_k_land.insert(0, kopf.get('KundeLand', 'DE') or 'DE')
                self.combo_rc.set(kopf.get('ReverseCharge', 'Nein') or 'Nein')
                self.entry_k_ustid.delete(0, 'end')
                self.entry_k_ustid.insert(0, kopf.get('KundeUStId', ''))

                self.positionen_liste = reader

            self.zusatz_dict = {}
            load_zusatz = True
            if custom_path and not self.config.get("cli_override_zusatz_csv"):
                load_zusatz = False

            if load_zusatz and os.path.exists(self.p_config.get('zusatz_csv', '')):
                with open(self.p_config.get('zusatz_csv', ''), mode='r', encoding='utf-8-sig') as f:
                    for line in f:
                        line = line.strip()
                        if line and len(line.split(';', 1)) == 2:
                            pk, txt = line.split(';', 1)
                            for p in pk.strip().split(','):
                                self.zusatz_dict[p.strip()] = txt.strip()

            self.header_text = lade_textdatei(self.p_config.get('header_csv', ''))
            self.einleitung_text = lade_textdatei(self.p_config.get('einleitung_csv', ''))
            self.vor_gruss_text = lade_textdatei(self.p_config.get('vor_gruss_csv', ''))
            self.gruss_text = lade_textdatei(self.p_config.get('gruss_csv', ''))
            self.refresh_pos_list()
            self.check_live_validation()
        except Exception as e:
            if not silent:
                self._err("Fehler", f"Fehler beim Laden: {e}")

    def open_texte_popup(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Texte & Textvorlagen bearbeiten")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(dialog)
        self.center_window(dialog, 680, 720)
        dialog.transient(self)
        dialog.grab_set()

        if "text_vorlagen" not in self.p_config or not isinstance(self.p_config["text_vorlagen"], dict):
            self.p_config["text_vorlagen"] = {}
        if "Standard" not in self.p_config["text_vorlagen"]:
            self.p_config["text_vorlagen"]["Standard"] = {
                "header": self.header_text,
                "einleitung": self.einleitung_text,
                "vor_gruss": getattr(self, "vor_gruss_text", ""),
                "gruss": self.gruss_text,
                "zahlungsbedingungen": self.p_config.get("zahlungsbedingungen_default", ""),
                "rechnungsvermerk": self.p_config.get("rechnungsvermerk_default", "")
            }

        f_top = ctk.CTkFrame(dialog, corner_radius=8)
        f_top.pack(side="top", fill="x", padx=15, pady=(12, 5))

        f_vorlage_row1 = ctk.CTkFrame(f_top, fg_color="transparent")
        f_vorlage_row1.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(f_vorlage_row1, text="Textkombination / Vorlage:", font=("Helvetica", 13, "bold")).pack(side="left")

        def get_vorlagen_liste():
            keys = list(self.p_config["text_vorlagen"].keys())
            if "Standard" in keys:
                keys.remove("Standard")
                keys.insert(0, "Standard")
            return keys

        def load_vorlage_into_fields(name):
            v = self.p_config["text_vorlagen"].get(name)
            if not v:
                return
            t_head.delete("0.0", "end")
            t_head.insert("0.0", v.get("header", ""))
            t_einl.delete("0.0", "end")
            t_einl.insert("0.0", v.get("einleitung", ""))
            t_vor_gruss.delete("0.0", "end")
            t_vor_gruss.insert("0.0", v.get("vor_gruss", ""))
            t_gruss.delete("0.0", "end")
            t_gruss.insert("0.0", v.get("gruss", ""))
            t_zahl.delete("0.0", "end")
            t_zahl.insert("0.0", v.get("zahlungsbedingungen", ""))
            t_verm.delete("0.0", "end")
            t_verm.insert("0.0", v.get("rechnungsvermerk", ""))
            self.p_config["aktive_text_vorlage"] = name
            self.aktive_text_vorlage = name

        combo_vorlage = ctk.CTkComboBox(f_vorlage_row1, values=get_vorlagen_liste(), width=260, command=load_vorlage_into_fields)
        akt_v = self.p_config.get("aktive_text_vorlage", "Standard")
        combo_vorlage.set(akt_v if akt_v in self.p_config["text_vorlagen"] else "Standard")
        combo_vorlage.pack(side="left", padx=10, fill="x", expand=True)

        f_vorlage_row2 = ctk.CTkFrame(f_top, fg_color="transparent")
        f_vorlage_row2.pack(fill="x", padx=10, pady=(4, 8))

        def get_current_fields_dict():
            return {
                "header": t_head.get("0.0", "end").strip(),
                "einleitung": t_einl.get("0.0", "end").strip(),
                "vor_gruss": t_vor_gruss.get("0.0", "end").strip(),
                "gruss": t_gruss.get("0.0", "end").strip(),
                "zahlungsbedingungen": t_zahl.get("0.0", "end").strip(),
                "rechnungsvermerk": t_verm.get("0.0", "end").strip()
            }

        def save_current_vorlage():
            name = combo_vorlage.get().strip() or "Standard"
            self.p_config["text_vorlagen"][name] = get_current_fields_dict()
            self.p_config["aktive_text_vorlage"] = name
            speichere_config(self.config)
            if hasattr(self, "combo_text_vorlage_main"):
                self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                self.combo_text_vorlage_main.set(name)
            if hasattr(self, "show_info"):
                self.show_info("Vorlage gespeichert", f"Die Textkombination wurde in der Vorlage '{name}' dauerhaft gespeichert.", parent=dialog)
            else:
                messagebox.showinfo("Vorlage gespeichert", f"Die Textkombination wurde in der Vorlage '{name}' dauerhaft gespeichert.", parent=dialog)

        def save_as_standard():
            self.p_config["text_vorlagen"]["Standard"] = get_current_fields_dict()
            self.p_config["aktive_text_vorlage"] = "Standard"
            combo_vorlage.configure(values=get_vorlagen_liste())
            combo_vorlage.set("Standard")
            speichere_config(self.config)
            if hasattr(self, "combo_text_vorlage_main"):
                self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                self.combo_text_vorlage_main.set("Standard")
            if hasattr(self, "show_info"):
                self.show_info("Standard gespeichert", "Die aktuellen Texte wurden als 'Standard' gespeichert.", parent=dialog)
            else:
                messagebox.showinfo("Standard gespeichert", "Die aktuellen Texte wurden als 'Standard' gespeichert.", parent=dialog)

        def save_new_vorlage():
            inp = ctk.CTkInputDialog(
                text="Name der neuen Textkombination\n(z. B. Vorschussrechnung, Kostenfestsetzungsantrag):",
                title="Neue Textvorlage speichern"
            )
            if hasattr(self, "apply_window_icon"):
                self.apply_window_icon(inp)
            new_name = inp.get_input()
            if new_name and new_name.strip():
                new_name = new_name.strip()
                self.p_config["text_vorlagen"][new_name] = get_current_fields_dict()
                self.p_config["aktive_text_vorlage"] = new_name
                combo_vorlage.configure(values=get_vorlagen_liste())
                combo_vorlage.set(new_name)
                speichere_config(self.config)
                if hasattr(self, "combo_text_vorlage_main"):
                    self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                    self.combo_text_vorlage_main.set(new_name)
                if hasattr(self, "show_info"):
                    self.show_info("Vorlage angelegt", f"Die Vorlage '{new_name}' wurde gespeichert und ausgewählt.", parent=dialog)
                else:
                    messagebox.showinfo("Vorlage angelegt", f"Die Vorlage '{new_name}' wurde gespeichert und ausgewählt.", parent=dialog)

        def delete_vorlage():
            name = combo_vorlage.get().strip()
            if name == "Standard":
                return self._warn("Nicht möglich", "Die Vorlage 'Standard' kann nicht gelöscht werden.", parent=dialog)
            if name in self.p_config["text_vorlagen"]:
                if self._yesno("Vorlage löschen", f"Möchten Sie die Vorlage '{name}' wirklich löschen?", parent=dialog):
                    del self.p_config["text_vorlagen"][name]
                    combo_vorlage.configure(values=get_vorlagen_liste())
                    combo_vorlage.set("Standard")
                    load_vorlage_into_fields("Standard")
                    speichere_config(self.config)
                    if hasattr(self, "combo_text_vorlage_main"):
                        self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                        self.combo_text_vorlage_main.set("Standard")

        self.create_button(f_vorlage_row2, text="💾 Vorlage aktualisieren", width=150, command=save_current_vorlage).pack(side="left", padx=(0, 5))
        self.create_button(f_vorlage_row2, text="⭐ Als Standard speichern", width=165, fg_color="#1f538d", hover_color="#14375d", command=save_as_standard).pack(side="left", padx=5)
        self.create_button(f_vorlage_row2, text="➕ Als neue Vorlage...", width=155, fg_color="#289102", hover_color="#1e6e01", command=save_new_vorlage).pack(side="left", padx=5)
        self.create_button(f_vorlage_row2, text="🗑 Löschen", width=90, fg_color="#b30000", hover_color="#800000", command=delete_vorlage).pack(side="right", padx=(5, 0))

        f_btn = ctk.CTkFrame(dialog, fg_color="transparent")
        f_btn.pack(side="bottom", fill="x", pady=10)

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=15, pady=5)
        setup_auto_scrollbar(scroll)

        info_frame = ctk.CTkFrame(scroll, fg_color="#f8fbff", border_width=1, border_color="#6fa8dc", corner_radius=6)
        info_frame.pack(fill="x", padx=20, pady=(5, 15))

        info_text = (
            "💡 Tipps zur Textformatierung & Umbrüchen:\n"
            "• Absätze: Nutzen Sie die [Enter]-Taste für einen neuen Absatz.\n"
            "• Harter Zeilenumbruch: Schreiben Sie <br/> für einen Umbruch ohne Absatzabstand.\n"
            "• Bedingtes Trennzeichen: Nutzen Sie &shy; (z.B. Rechnungs&shy;nummer) für weiche Umbrüche,\n"
            "  die von der Text-Engine nur bei Bedarf am Zeilenende getrennt werden.\n"
            "• Textformatierung: <b>Fett</b> oder <i>Kursiv</i> sind über HTML-Tags möglich.\n"
            "• Blocksatz: Fließtexte werden automatisch im Blocksatz formatiert."
        )
        ctk.CTkLabel(info_frame, text=info_text, justify="left", font=("Helvetica", 11), text_color="#1f538d").pack(anchor="w", padx=12, pady=8)

        ctk.CTkLabel(scroll, text="Zentrierter Header (über Rechnungs-Nr.):").pack(anchor="w", padx=20, pady=(8, 0))
        t_head = ctk.CTkTextbox(scroll, height=55)
        t_head.pack(fill="x", padx=20, pady=(2, 8))
        t_head.insert("0.0", self.header_text)

        ctk.CTkLabel(scroll, text="Einleitung (vor Positionen):").pack(anchor="w", padx=20, pady=(4, 0))
        t_einl = ctk.CTkTextbox(scroll, height=70)
        t_einl.pack(fill="x", padx=20, pady=(2, 8))
        t_einl.insert("0.0", self.einleitung_text)

        ctk.CTkLabel(scroll, text="Vor Gruß (nach Zahlungshinweis / vor Gruß):").pack(anchor="w", padx=20, pady=(4, 0))
        t_vor_gruss = ctk.CTkTextbox(scroll, height=70)
        t_vor_gruss.pack(fill="x", padx=20, pady=(2, 8))
        t_vor_gruss.insert("0.0", getattr(self, "vor_gruss_text", ""))

        ctk.CTkLabel(scroll, text="Gruß (unten):").pack(anchor="w", padx=20, pady=(4, 0))
        t_gruss = ctk.CTkTextbox(scroll, height=70)
        t_gruss.pack(fill="x", padx=20, pady=(2, 8))
        t_gruss.insert("0.0", self.gruss_text)

        ctk.CTkLabel(scroll, text="ℹ️ Offizielle Hinweise zur Nutzung von BT-20 und BT-22 nach EN 16931 finden Sie im Handbuch (Kapitel 9).", text_color="#1f538d", font=("Helvetica", 11, "italic")).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(scroll, text="Zahlungsbedingungen (BT-20 - Fälligkeitshinweis):").pack(anchor="w", padx=20, pady=(4, 0))
        t_zahl = ctk.CTkTextbox(scroll, height=45)
        t_zahl.pack(fill="x", padx=20, pady=(2, 8))
        t_zahl.insert("0.0", self.p_config.get("zahlungsbedingungen_default", ""))

        ctk.CTkLabel(scroll, text="Rechnungsvermerk / Dauerrechnung (BT-22):").pack(anchor="w", padx=20, pady=(4, 0))
        t_verm = ctk.CTkTextbox(scroll, height=45)
        t_verm.pack(fill="x", padx=20, pady=(2, 8))
        t_verm.insert("0.0", self.p_config.get("rechnungsvermerk_default", ""))

        def save_texte():
            self.header_text = t_head.get("0.0", "end").strip()
            self.einleitung_text = t_einl.get("0.0", "end").strip()
            self.vor_gruss_text = t_vor_gruss.get("0.0", "end").strip()
            self.gruss_text = t_gruss.get("0.0", "end").strip()

            self.p_config["zahlungsbedingungen_default"] = t_zahl.get("0.0", "end").strip()
            self.p_config["rechnungsvermerk_default"] = t_verm.get("0.0", "end").strip()

            akt_name = combo_vorlage.get().strip() or "Standard"
            self.p_config["aktive_text_vorlage"] = akt_name
            self.aktive_text_vorlage = akt_name

            speichere_textdatei(self.p_config.get('header_csv'), self.header_text)
            speichere_textdatei(self.p_config.get('einleitung_csv'), self.einleitung_text)
            speichere_textdatei(self.p_config.get('vor_gruss_csv'), self.vor_gruss_text)
            speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)

            if hasattr(self, "combo_text_vorlage_main"):
                self.combo_text_vorlage_main.configure(values=get_vorlagen_liste())
                self.combo_text_vorlage_main.set(akt_name)

            speichere_config(self.config)
            dialog.destroy()

        self.create_button(f_btn, text="Übernehmen & Schließen", width=220, command=save_texte).pack(pady=5)

    def open_pos_popup(self, edit_index=None):
        briefbogen_pfad = self.p_config.get('briefbogen_pdf', '')

        if not os.path.exists(briefbogen_pfad):
            self._warn(
                "Briefbogen fehlt",
                f"Ohne briefbogen.pdf macht eine Rechnungserstellung wenig Sinn!\n\n"
                f"Bitte speichern Sie den Briefbogen unter folgendem Pfad ab:\n"
                f"{briefbogen_pfad}\n\n"
                f"Weitere Hinweise und Formatierungsanforderungen finden Sie im Handbuch unter 'Infos'."
            )
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Position bearbeiten" if edit_index is not None else "Neue Position")
        if hasattr(self, "apply_window_icon"):
            self.apply_window_icon(dialog)
        self.center_window(dialog, 450, 340)
        dialog.transient(self)
        dialog.grab_set()

        lbl_font = ("Helvetica", 12)
        fld_font = ("Helvetica", 12)

        def apply_produkt_by_name(wahl):
            wahl_clean = str(wahl or "").strip().lower()
            for p in (self.produkte_liste or []):
                if str(p.get("Bezeichnung", "")).strip().lower() == wahl_clean:
                    menge_raw = str(p.get("Menge", "")).strip() or "1"
                    preis_raw = str(p.get("EinzelpreisNetto", "")).strip() or "0"
                    steuer_raw = str(p.get("Steuersatz", "")).strip() or "19"

                    e_menge.delete(0, "end")
                    e_menge.insert(0, menge_raw)
                    e_preis.delete(0, "end")
                    e_preis.insert(0, preis_raw)
                    e_steuer.delete(0, "end")
                    e_steuer.insert(0, steuer_raw)

                    c = str(p.get("Einheit", "C62")).strip()
                    matched_einheit = False
                    for val in EINHEITEN_LISTE:
                        if f"({c})" in val or c == val or EINHEITEN_MAPPING.get(c, c) in val:
                            e_einheit.set(val)
                            matched_einheit = True
                            break
                    if not matched_einheit and c:
                        e_einheit.set(c)
                    break

        def open_article_selector(target_entry):
            self.open_produkt_search(target_entry)
            new_val = target_entry.get().strip()
            if new_val:
                apply_produkt_by_name(new_val)

        def _compact_row(label_text, is_combo=False, combo_values=None, command=None, btn_text=None, btn_cmd=None):
            row = ctk.CTkFrame(dialog, fg_color="transparent", height=28)
            row.pack(fill="x", padx=8, pady=2)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=label_text, width=95, anchor="w", font=lbl_font).pack(side="left")
            if btn_text and btn_cmd:
                entry = ctk.CTkEntry(row, height=24, font=fld_font)
                entry.pack(side="left", fill="x", expand=True, padx=(4, 3))
                self.create_button(row, text=btn_text, width=28, height=24, font=lbl_font, command=lambda: btn_cmd(entry)).pack(side="right")
                return entry
            entry = (
                ctk.CTkComboBox(row, values=combo_values or [], command=command, height=24, font=fld_font, dropdown_font=fld_font)
                if is_combo
                else ctk.CTkEntry(row, height=24, font=fld_font)
            )
            entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
            return entry

        e_bez = _compact_row("Bezeichnung", btn_text="🔍", btn_cmd=open_article_selector)

        def on_bez_tab(_event=None):
            open_article_selector(e_bez)
            return "break"

        e_bez.bind("<Tab>", on_bez_tab)
        e_bez.bind("<FocusOut>", lambda _e: apply_produkt_by_name(e_bez.get()), add="+")
        e_menge = _compact_row("Menge")
        e_einheit = _compact_row("Einheit", is_combo=True, combo_values=EINHEITEN_LISTE)
        e_preis = _compact_row("Einzelpreis (€)")
        e_steuer = _compact_row("Steuer (%)")
        e_lz_pos = _compact_row("Lz. Position", btn_text="📅", btn_cmd=self.open_date_picker)

        ex_notes = list(set([v.replace('~cr', '\\n') for k, v in self.zusatz_dict.items() if k != '0']))
        ex_notes.insert(0, "")
        e_anmerkung = _compact_row("Anmerkung", is_combo=True, combo_values=ex_notes)

        if edit_index is None:
            e_menge.insert(0, "1")
            e_einheit.set(self.p_config.get("letzte_einheit", "Stück (C62)"))
            e_steuer.insert(0, "19")
            e_anmerkung.set("")
            e_bez.delete(0, "end")
        else:
            p = self.positionen_liste[edit_index]
            e_bez.delete(0, "end")
            e_bez.insert(0, p.get('Bezeichnung', ''))
            e_menge.insert(0, f"{safe_float(p.get('Menge', 1)):g}")
            e_preis.insert(0, p.get('EinzelpreisNetto', ''))
            e_steuer.insert(0, p.get('Steuersatz', '19'))
            e_lz_pos.insert(0, p.get('LeistungszeitraumPos', ''))
            e_anmerkung.set(self.zusatz_dict.get(p.get('PosNr'), "").replace('~cr', '\\n'))
            c = p.get('Einheit', 'C62')
            for val in EINHEITEN_LISTE:
                if c in val or EINHEITEN_MAPPING.get(c, c) in val:
                    e_einheit.set(val)
                    break

        e_bez.focus_set()

        def save_it(event=None):
            if not e_bez.get().strip():
                return self._warn("Fehler", "Bezeichnung fehlt!", parent=dialog)
            try:
                float(e_menge.get().replace(',', '.') or "1")
                float(e_preis.get().replace(',', '.') or "0.0")
                float(e_steuer.get().replace(',', '.') or "19")
            except ValueError:
                return self._warn("Fehler", "Eingaben müssen Zahlen sein!", parent=dialog)

            lz_pos_val = parse_flexible_date_span(e_lz_pos.get())
            einheit_code = re.search(r'\((.*?)\)', e_einheit.get()).group(1).strip() if re.search(r'\((.*?)\)', e_einheit.get()) else e_einheit.get().strip()

            self.p_config["letzte_einheit"] = e_einheit.get()
            speichere_config(self.config)

            self.save_state_to_history()

            pos_nr = str(edit_index + 1) if edit_index is not None else str(len(self.positionen_liste) + 1)
            new_data = {
                'PosNr': pos_nr,
                'Menge': e_menge.get() or "1",
                'Einheit': einheit_code,
                'Bezeichnung': e_bez.get(),
                'EinzelpreisNetto': e_preis.get().replace(',', '.'),
                'Steuersatz': e_steuer.get() or "19",
                'LeistungszeitraumPos': lz_pos_val
            }
            if edit_index is not None:
                self.positionen_liste[edit_index] = new_data
            else:
                self.positionen_liste.append(new_data)

            anm_txt = e_anmerkung.get().strip()
            if anm_txt:
                self.zusatz_dict[pos_nr] = anm_txt.replace('\\n', '~cr')
            else:
                self.zusatz_dict.pop(pos_nr, None)

            self.refresh_pos_list()
            dialog.destroy()

        self.create_button(dialog, text="Speichern", width=120, height=28, font=lbl_font, command=save_it).pack(pady=(6, 6))
        dialog.bind('<Return>', save_it)

    def delete_pos(self, index):
        if self._yesno("Löschen", "Position wirklich löschen?"):
            self.save_state_to_history()
            del self.positionen_liste[index]
            new_zusatz = {'0': self.zusatz_dict['0']} if '0' in self.zusatz_dict else {}
            for i, p in enumerate(self.positionen_liste):
                old_nr = p['PosNr']
                new_nr = str(i + 1)
                p['PosNr'] = new_nr
                if old_nr in self.zusatz_dict:
                    new_zusatz[new_nr] = self.zusatz_dict[old_nr]
            self.zusatz_dict = new_zusatz
            self.refresh_pos_list()

    def refresh_pos_list(self):
        for widget in self.pos_scroll.winfo_children():
            widget.destroy()
        for idx, p in enumerate(self.positionen_liste):
            f = ctk.CTkFrame(self.pos_scroll)
            f.pack(fill="x", pady=2)
            self.create_button(
                f, text="🗑", width=32, fg_color="#b30000", hover_color="#800000",
                command=lambda i=idx: self.delete_pos(i)
            ).pack(side="right", padx=5, pady=2)
            self.create_button(
                f, text="📝", width=34, font=("Helvetica", 12), fg_color="#555", hover_color="#777",
                command=lambda i=idx: self.open_pos_popup(i)
            ).pack(side="right", padx=5, pady=4)

            pos_nr = str(p.get('PosNr', idx + 1))
            menge_val = safe_float(p.get('Menge', 1))
            menge_str = f_num(menge_val)
            code = p.get('Einheit', 'C62')
            einheit_str = EINHEITEN_MAPPING.get(code, code)
            menge_einheit_str = f"{menge_str} {einheit_str}".strip()
            preis_str = f_curr(safe_float(p.get('EinzelpreisNetto', 0)))
            ust_str = f"{f_num(safe_float(p.get('Steuersatz', 19)))}%"

            bez_voll = p.get('Bezeichnung', '').strip()
            anmerkung_voll = self.zusatz_dict.get(pos_nr, "").replace('~cr', '\n').replace('\\n', '\n').strip()
            anmerkung_einzeilig = " / ".join(z.strip() for z in anmerkung_voll.splitlines() if z.strip())

            lz_raw = p.get('LeistungszeitraumPos', '').strip()
            lz_str = parse_lz_lesbar(lz_raw) if lz_raw else "-"

            if anmerkung_einzeilig:
                max_bez = 50
                max_anm = 50
            else:
                max_bez = 100
                max_anm = 0

            bez_kurz = bez_voll if len(bez_voll) <= max_bez else bez_voll[:max_bez - 3] + "..."
            anm_kurz = (
                anmerkung_einzeilig if len(anmerkung_einzeilig) <= max_anm else anmerkung_einzeilig[:max_anm - 3] + "..."
            ) if max_anm > 0 else ""

            menge_preis_str = f"{menge_str}x{preis_str}"
            zeile_teile = [f"[{pos_nr}]", menge_preis_str, ust_str]
            if bez_kurz:
                zeile_teile.append(bez_kurz)
            if anm_kurz:
                zeile_teile.append(f"({anm_kurz})")

            lbl = ctk.CTkLabel(
                f,
                text="|".join(zeile_teile),
                anchor="w",
                font=("Helvetica", 11)
            )
            lbl.pack(side="left", fill="x", expand=True, padx=10, pady=4)

            hover_text = "\n".join([
                f"{menge_einheit_str} x {preis_str} + {ust_str}",
                f"{bez_voll or '-'}",
                f"{anmerkung_voll or '-'}",
                f"Leistungszeitraum: {lz_str or '-'}",
            ])

            create_tooltip(lbl, hover_text, font=("Helvetica", 12))
            create_tooltip(f, hover_text, font=("Helvetica", 12))

        self.update_totals_ui()
        update_scrollable_visibility(self.pos_scroll)

    def check_live_validation(self, *args):
        if not hasattr(self, 'lbl_live_errors'):
            return

        errors = []
        r_nr = self.entry_r_nr.get().strip()
        r_datum = self.entry_r_datum.get().strip()
        f_datum = self.entry_f_datum.get().strip()
        name = self.entry_k_name.get().strip()
        strasse = self.entry_k_strasse.get().strip()
        plz_ort = self.entry_k_plz_ort.get().strip()
        endpoint = self.entry_k_endpoint.get().strip()
        k_az = self.entry_k_az.get().strip()

        try:
            default_border = ctk.ThemeManager.theme["CTkEntry"]["border_color"]
        except Exception:
            default_border = ["#979DA2", "#565B5E"]

        if not r_nr:
            self.entry_r_nr.configure(border_color="red")
            errors.append("Rechnungs-Nr. fehlt")
        else:
            self.entry_r_nr.configure(border_color=default_border)

        try:
            parsed_r = parse_flexible_date(r_datum)
            datetime.strptime(parsed_r, "%Y-%m-%d")
            self.entry_r_datum.configure(border_color=default_border)
        except Exception:
            self.entry_r_datum.configure(border_color="red")
            errors.append("Rechnungsdatum ungültig / fehlt")

        try:
            parsed_f = parse_flexible_date(f_datum)
            datetime.strptime(parsed_f, "%Y-%m-%d")
            self.entry_f_datum.configure(border_color=default_border)
        except Exception:
            self.entry_f_datum.configure(border_color="red")
            errors.append("Fälligkeitsdatum ungültig / fehlt")

        lz_kopf = self.entry_lz_kopf.get().strip()
        if not lz_kopf:
            self.entry_lz_kopf.configure(border_color="red")
            errors.append("Leistungszeitraum fehlt")
        else:
            self.entry_lz_kopf.configure(border_color=default_border)

        if not name:
            self.entry_k_name.configure(border_color="red")
            errors.append("Kundenname fehlt")
        else:
            self.entry_k_name.configure(border_color=default_border)

        if not strasse:
            self.entry_k_strasse.configure(border_color="red")
            errors.append("Straße fehlt")
        else:
            self.entry_k_strasse.configure(border_color=default_border)

        parts = plz_ort.split()
        if not plz_ort or len(parts) < 2:
            self.entry_k_plz_ort.configure(border_color="red")
            if not plz_ort:
                errors.append("PLZ und Ort fehlen")
            else:
                errors.append("PLZ/Ort unvollständig (Leerzeichen fehlt)")
        else:
            self.entry_k_plz_ort.configure(border_color=default_border)

        if not endpoint:
            self.entry_k_endpoint.configure(border_color="red")
            errors.append("E-Mail / Leitweg-ID fehlt (für E-Rechnung)")
        else:
            self.entry_k_endpoint.configure(border_color=default_border)

        if not k_az:
            self.entry_k_az.configure(border_color="red")
            errors.append("'Ihr Zeichen' (Kunden-Aktenzeichen) fehlt")
        else:
            self.entry_k_az.configure(border_color=default_border)

        if not getattr(self, "positionen_liste", None):
            errors.append("Mindestens eine Rechnungsposition erfassen")

        if errors:
            self.lbl_live_errors.configure(text="⚠️ Zu Korrigieren: " + " | ".join(errors), text_color=("#a61c1c", "#ff7b7b"))
        else:
            self.lbl_live_errors.configure(text="✅ Alle Pflichtfelder ausgefüllt", text_color=("#1e7e00", "#5dc21c"))

    def save_manual_invoice(self, silent=False, require_buyer_endpoint=False):
        if hasattr(self, 'check_and_handle_lock') and not self.check_and_handle_lock("📋 ERSTELLEN"):
            return False
        self.set_firm_lock()

        if not self.positionen_liste:
            if not silent:
                self._warn("Fehler", "Bitte erfassen Sie zunächst Positionen!")
            return False

        self.check_live_validation()

        r_nr = self.entry_r_nr.get().strip()
        r_datum = parse_flexible_date(self.entry_r_datum.get())
        f_datum = parse_flexible_date(self.entry_f_datum.get())
        name = self.entry_k_name.get().strip()
        strasse = self.entry_k_strasse.get().strip()
        plz_ort = self.entry_k_plz_ort.get().strip()
        parts = plz_ort.split()
        endpoint = self.entry_k_endpoint.get().strip()

        k_az = self.entry_k_az.get().strip()
        lz_kopf = parse_flexible_date_span(self.entry_lz_kopf.get())

        has_date_error = False
        try:
            datetime.strptime(r_datum, "%Y-%m-%d")
            datetime.strptime(f_datum, "%Y-%m-%d")
        except ValueError:
            has_date_error = True

        if not r_nr or not name or not strasse or not plz_ort or len(parts) < 2 or not k_az or not lz_kopf or has_date_error or (require_buyer_endpoint and not endpoint):
            if not silent:
                self._warn(
                    "Fehlende Pflichtdaten",
                    "Bitte füllen Sie alle rot markierten Pflichtfelder (inkl. 'Ihr Zeichen' und 'Lz. Kopf') korrekt aus."
                )
            return False

        self.entry_r_datum.delete(0, 'end')
        self.entry_r_datum.insert(0, r_datum)
        self.entry_f_datum.delete(0, 'end')
        self.entry_f_datum.insert(0, f_datum)
        self.entry_lz_kopf.delete(0, 'end')
        self.entry_lz_kopf.insert(0, lz_kopf)

        rechnungs_csv_pfad = self.p_config.get('rechnung_csv', 'rechnung.csv')
        existierende_rechnungen = lade_rechnungen(rechnungs_csv_pfad)

        if r_nr in existierende_rechnungen:
            alle_r_nummern = list(existierende_rechnungen.keys())
            ist_letzte_rechnung = (r_nr == alle_r_nummern[-1]) if alle_r_nummern else False

            warn_text = (
                f"⚠️ Die Rechnungsnummer '{r_nr}' wurde bereits verwendet!\n\n"
                f"Die Änderung einer bereits erstellten Rechnung kann problematisch sein.\n"
            )

            if not ist_letzte_rechnung:
                warn_text += (
                    "HINWEIS: Da es sich NICHT um die allerletzte erstellte Rechnung handelt, "
                    "wird diese Änderung im Journal erfasst, was zu einer Unstimmigkeit des Journals führt!\n\n"
                )

            warn_text += (
                "Es ist grundsätzlich besser, eine Stornorechnung zu erfassen und die Rechnung "
                "dann neu zu erstellen.\n\n"
                "Möchten Sie die Rechnungsnummer dennoch erneut erstellen / überschreiben?"
            )

            if not self._yesno("Rechnungsnummer bereits vergeben", warn_text, default="no"):
                return False

            if not ist_letzte_rechnung:
                self._err(
                    "Überschreiben nicht zulässig",
                    "Da es sich nicht um die letzte erstellte Rechnung handelt, kann die Zeile aus Sicherheitsgründen nicht überschrieben werden."
                )
                return False

            audit_bemerkung = ""
            if self.p_config.get("audit_reason_required", False):
                d_audit = ctk.CTkInputDialog(text=f"Bitte geben Sie den Grund für die Änderung der Rechnung '{r_nr}' an (Audit-Log):", title="GoBD: Begründung erforderlich")
                if hasattr(self, "apply_window_icon"):
                    self.apply_window_icon(d_audit)
                audit_bemerkung = d_audit.get_input()
                if not audit_bemerkung:
                    self._warn("Abbruch", "Ohne Begründung darf die Rechnung nicht geändert werden.")
                    return False
            audit_aktion = "Geändert"
        else:
            audit_bemerkung = ""
            audit_aktion = "Erstellt"

        plz = parts[0]
        ort = " ".join(parts[1:])

        buyer_endpoint = endpoint
        buyer_scheme = self.entry_k_endpoint_scheme.get().strip()
        if buyer_endpoint and not buyer_scheme and '@' in buyer_endpoint:
            buyer_scheme = 'EM'
        if require_buyer_endpoint and buyer_endpoint and not buyer_scheme:
            self._warn("Fehler", "Für eine Leitweg-ID muss das Endpoint-Schema angegeben werden (regelmäßig 0204).")
            return False

        kunde_land = self.entry_k_land.get().strip().upper() or 'DE'
        rc_mode = self.combo_rc.get()
        kunde_ustid = self.entry_k_ustid.get().strip()

        full_positions = []
        for p in self.positionen_liste:
            p_copy = p.copy()
            p_copy.update({
                'Rechnungsnummer': r_nr,
                'Rechnungsdatum': r_datum,
                'Faelligkeitsdatum': f_datum,
                'KundeName': name,
                'KundeStrasse': strasse,
                'KundePLZ': plz,
                'KundeOrt': ort,
                'KundeLand': kunde_land,
                'KundeEmail': buyer_endpoint if '@' in buyer_endpoint else '',
                'KundeEndpoint': buyer_endpoint,
                'KundeEndpointScheme': buyer_scheme,
                'Zusatztext': '',
                'KundeNr': self.entry_k_nr.get().strip(),
                'Aktenzeichen': self.entry_az.get().strip(),
                'KundeAktenzeichen': self.entry_k_az.get().strip(),
                'LeistungszeitraumKopf': lz_kopf,
                'Ratenzahlung': str(bool(self.chk_raten.get())),
                'ReverseCharge': rc_mode,
                'KundeUStId': kunde_ustid,
            })
            full_positions.append(p_copy)

        fieldnames = [
            'Rechnungsnummer', 'Rechnungsdatum', 'Faelligkeitsdatum', 'KundeName', 'KundeStrasse',
            'KundePLZ', 'KundeOrt', 'KundeLand', 'KundeEmail', 'KundeEndpoint', 'KundeEndpointScheme',
            'KundeNr', 'Aktenzeichen', 'KundeAktenzeichen', 'LeistungszeitraumKopf', 'Ratenzahlung',
            'PosNr', 'Menge', 'Einheit', 'Bezeichnung', 'EinzelpreisNetto', 'Steuersatz',
            'Zusatztext', 'LeistungszeitraumPos', 'ReverseCharge', 'KundeUStId'
        ]

        try:
            with open(self.p_config['rechnung_csv'], 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                writer.writerows(full_positions)

            akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
            are_dir = self.p_config.get("ausgabe_ordner", "")
            if are_dir:
                arecsv_dir = os.path.join(os.path.dirname(are_dir), "arecsv", akt_jahr)
                os.makedirs(arecsv_dir, exist_ok=True)
                csv_archiv_pfad = os.path.join(arecsv_dir, f"Rechnung_{r_nr}.csv")
                with open(csv_archiv_pfad, 'w', newline='', encoding='utf-8-sig') as f_csv:
                    writer_csv = csv.DictWriter(f_csv, fieldnames=fieldnames, delimiter=';')
                    writer_csv.writeheader()
                    writer_csv.writerows(full_positions)

            with open(self.p_config['zusatz_csv'], 'w', encoding='utf-8-sig') as f:
                text_to_pos = {}
                for k, v in self.zusatz_dict.items():
                    if k == '0':
                        continue
                    if v not in text_to_pos:
                        text_to_pos[v] = []
                    text_to_pos[v].append(int(k))
                if '0' in self.zusatz_dict:
                    f.write(f"0;{self.zusatz_dict['0']}\n")
                for text, pos_list in text_to_pos.items():
                    f.write(f"{','.join(map(str, sorted(pos_list)))};{text}\n")

            speichere_textdatei(self.p_config.get('header_csv'), self.header_text)
            speichere_textdatei(self.p_config.get('einleitung_csv'), self.einleitung_text)
            speichere_textdatei(self.p_config.get('vor_gruss_csv'), getattr(self, 'vor_gruss_text', ''))
            speichere_textdatei(self.p_config.get('gruss_csv'), self.gruss_text)

            if self.chk_kunde_speichern.get() and name:
                kunde_save_payload = {
                    'Name': name,
                    'Strasse': strasse,
                    'PLZ_Ort': plz_ort,
                    'Land': kunde_land,
                    'KundeNr': self.entry_k_nr.get().strip(),
                    'Aktenzeichen': self.entry_az.get().strip(),
                    'KundeAktenzeichen': self.entry_k_az.get().strip(),
                    'Endpoint': buyer_endpoint,
                    'EndpointScheme': buyer_scheme
                }
                if kunde_ustid:
                    kunde_save_payload['UStId'] = kunde_ustid
                speichere_kunde(
                    self.p_config.get("kunden_csv", "kunden.csv"),
                    kunde_save_payload
                )
                self.kunden_liste = lade_kunden(self.p_config.get("kunden_csv", "kunden.csv"))

            self.p_config['letzte_rechnungsnummer'] = r_nr
            self.p_config['keep_raten'] = bool(self.chk_raten.get())
            self.p_config['keep_kunde_speichern'] = bool(self.chk_kunde_speichern.get())
            self.p_config['keep_email_versand'] = bool(self.chk_email_versand.get())
            speichere_config(self.config)

            base_data_path = self.config.get("base_data_path", "")
            if base_data_path:
                firm_dir = os.path.join(base_data_path, self.p_config["profil_name"].replace(" ", "_"))
                modus = "CLI (--edit)" if self.start_in_edit else "GUI"
                write_audit_log(firm_dir, "Ausgang", audit_aktion, r_nr, audit_bemerkung, modus)
            return True
        except Exception as e:
            self._err("Fehler", str(e))
            return False

    def generate_testrechnung(self):
        if not self.positionen_liste:
            return self._warn("Fehler", "Bitte erfassen Sie Positionen!")

        self.check_live_validation()
        if not self.entry_r_nr.get().strip() or not self.entry_k_name.get().strip() or not self.entry_k_strasse.get().strip() or len(self.entry_k_plz_ort.get().strip().split()) < 2:
            return self._warn("Fehlende Pflichtdaten", "Bitte korrigieren Sie die rot markierten Pflichtfelder vor der Vorschau.")

        valid, lz_msg = check_lz_logic(
            {'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())},
            [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste]
        )
        if not valid:
            return self._warn("Prüfung fehlgeschlagen", lz_msg)

        r_datum = parse_flexible_date(self.entry_r_datum.get())
        f_datum = parse_flexible_date(self.entry_f_datum.get())
        lz_kopf = parse_flexible_date_span(self.entry_lz_kopf.get())

        parts = self.entry_k_plz_ort.get().strip().split()
        plz = parts[0]
        ort = " ".join(parts[1:])

        kopf = {
            'Rechnungsnummer': '',
            'Rechnungsdatum': r_datum,
            'Faelligkeitsdatum': f_datum,
            'KundeName': self.entry_k_name.get(),
            'KundeStrasse': self.entry_k_strasse.get(),
            'KundePLZ': plz,
            'KundeOrt': ort,
            'KundeLand': self.entry_k_land.get().strip().upper() or 'DE',
            'KundeEmail': self.entry_k_endpoint.get() if '@' in self.entry_k_endpoint.get() else '',
            'KundeEndpoint': self.entry_k_endpoint.get(),
            'KundeEndpointScheme': self.entry_k_endpoint_scheme.get(),
            'Zusatztext': '',
            'KundeNr': self.entry_k_nr.get().strip(),
            'Aktenzeichen': self.entry_az.get().strip(),
            'KundeAktenzeichen': self.entry_k_az.get().strip(),
            'LeistungszeitraumKopf': lz_kopf,
            'Ratenzahlung': str(bool(self.chk_raten.get())),
            'ReverseCharge': self.combo_rc.get(),
            'KundeUStId': self.entry_k_ustid.get().strip()
        }
        rechnung_daten = {'kopf': kopf, 'positionen': self.positionen_liste}
        zusatztexte = [{'pos': k, 'text': v.replace('~cr', '\n')} for k, v in self.zusatz_dict.items()]

        from pdf_zugferd import erstelle_testrechnung
        act_prof = self.p_config
        firma = lade_firma(act_prof['firma_csv'])
        briefkopf_rechte_spalte = bool(act_prof.get("briefkopf_rechte_spalte", True))

        try:
            pdf_pfad = erstelle_testrechnung(
                firma, rechnung_daten, act_prof['briefbogen_pdf'],
                zusatztexte, self.gruss_text, self.header_text, self.einleitung_text,
                getattr(self, 'vor_gruss_text', ''),
                briefkopf_rechte_spalte=briefkopf_rechte_spalte,
            )
            os.startfile(pdf_pfad)
        except Exception as e:
            self._err("Fehler bei der Testrechnung", str(e))

    def save_generate_papierrechnung_exit(self):
        if not self.positionen_liste:
            return self._warn("Fehler", "Bitte erfassen Sie Positionen!")

        if not self.save_manual_invoice(silent=False, require_buyer_endpoint=False):
            return

        valid, lz_msg = check_lz_logic(
            {'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())},
            [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste]
        )
        if not valid:
            self._warn("Prüfung fehlgeschlagen", lz_msg)
            return

        from pdf_zugferd import erstelle_papierrechnung
        act_prof = self.p_config
        firma = lade_firma(act_prof['firma_csv'])
        rechnungen = lade_rechnungen(act_prof['rechnung_csv'])
        r_nr = self.entry_r_nr.get().strip()
        daten = rechnungen.get(r_nr)
        if not daten:
            self._err("Papierrechnung konnte nicht erstellt werden", f"Die gespeicherte Rechnung '{r_nr}' wurde nicht gefunden.")
            return
        briefkopf_rechte_spalte = bool(act_prof.get("briefkopf_rechte_spalte", True))
        try:
            pdf_pfad = erstelle_papierrechnung(
                firma, daten, act_prof['briefbogen_pdf'],
                lade_zusatz_csv(act_prof['zusatz_csv']), self.gruss_text,
                self.header_text, self.einleitung_text,
                act_prof['ausgabe_ordner'], act_prof['auswertungen_ordner'],
                act_prof.get("aktuelles_rechnungsjahr", str(datetime.now().year)),
                getattr(self, 'vor_gruss_text', ''),
                briefkopf_rechte_spalte=briefkopf_rechte_spalte,
            )
        except Exception as e:
            self._err("Papierrechnung konnte nicht erstellt werden", str(e))
            return
        if not os.path.isfile(pdf_pfad):
            self._err("Papierrechnung konnte nicht erstellt werden", "Die PDF-Datei wurde nicht angelegt.")
            return
        kopie_dir = self.config.get("cli_kopie")
        if kopie_dir:
            try:
                os.makedirs(kopie_dir, exist_ok=True)
                shutil.copy2(pdf_pfad, os.path.join(kopie_dir, os.path.basename(pdf_pfad)))
            except Exception as e:
                print(f"Fehler beim Kopieren: {e}")
        if not self.config.get("cli_no_open", False):
            try:
                os.startfile(pdf_pfad)
            except Exception:
                pass
        self.send_invoice_email()
        self.on_closing(skip_warning=True)

    def save_generate_xrechnung_exit(self):
        if not self.positionen_liste:
            return self._warn("Fehler", "Bitte erfassen Sie Positionen!")

        if not self.save_manual_invoice(silent=False, require_buyer_endpoint=True):
            return

        valid, lz_msg = check_lz_logic(
            {'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())},
            [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste]
        )
        if not valid:
            self._warn("Prüfung fehlgeschlagen", lz_msg)
            return

        from pdf_zugferd import erstelle_xrechnung
        act_prof = self.p_config
        firma = lade_firma(act_prof['firma_csv'])
        rechnungen = lade_rechnungen(act_prof['rechnung_csv'])
        zusatztexte = lade_zusatz_csv(act_prof['zusatz_csv'])
        akt_jahr = act_prof.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        briefkopf_rechte_spalte = bool(act_prof.get("briefkopf_rechte_spalte", True))

        r_nr = self.entry_r_nr.get().strip()
        daten = rechnungen.get(r_nr)
        if not daten:
            self._err("XRechnung konnte nicht erstellt werden", f"Die gespeicherte Rechnung '{r_nr}' wurde nicht gefunden.")
            return
        try:
            xml_p, pdf_p = erstelle_xrechnung(
                firma, daten, act_prof['briefbogen_pdf'],
                zusatztexte, self.gruss_text, self.header_text, self.einleitung_text,
                act_prof['ausgabe_ordner'], act_prof['auswertungen_ordner'], akt_jahr,
                getattr(self, 'vor_gruss_text', ''),
                briefkopf_rechte_spalte=briefkopf_rechte_spalte,
            )
        except Exception as e:
            self._err("XRechnung konnte nicht erstellt werden", str(e))
            return
        if not (os.path.isfile(xml_p) and os.path.isfile(pdf_p)):
            self._err("XRechnung konnte nicht erstellt werden", "XML oder Begleit-PDF wurde nicht angelegt.")
            return
        kopie_dir = self.config.get("cli_kopie")
        if kopie_dir:
            try:
                os.makedirs(kopie_dir, exist_ok=True)
                if os.path.isfile(xml_p):
                    shutil.copy2(xml_p, os.path.join(kopie_dir, os.path.basename(xml_p)))
                if os.path.isfile(pdf_p):
                    shutil.copy2(pdf_p, os.path.join(kopie_dir, os.path.basename(pdf_p)))
            except Exception as e:
                print(f"Fehler beim Kopieren: {e}")

        ziel_ordner = os.path.dirname(pdf_p)
        if os.path.exists(ziel_ordner):
            try:
                import subprocess
                subprocess.Popen(['explorer', ziel_ordner])
            except Exception:
                try:
                    os.startfile(ziel_ordner)
                except Exception:
                    pass
        self.send_invoice_email()
        self.on_closing(skip_warning=True)

    def save_generate_open_exit(self):
        if not self.positionen_liste:
            return self._warn("Fehler", "Bitte erfassen Sie Positionen!")

        if not self.save_manual_invoice(silent=False, require_buyer_endpoint=True):
            return

        valid, lz_msg = check_lz_logic(
            {'LeistungszeitraumKopf': parse_flexible_date_span(self.entry_lz_kopf.get().strip())},
            [{'PosNr': p.get('PosNr'), 'LeistungszeitraumPos': p.get('LeistungszeitraumPos')} for p in self.positionen_liste]
        )
        if not valid:
            self._warn("Prüfung fehlgeschlagen", lz_msg)
            return

        from pdf_zugferd import run_auto_generation
        run_auto_generation(self.config)

        r_nr = self.entry_r_nr.get()
        akt_jahr = self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        pdf_pfad = os.path.join(self.p_config['ausgabe_ordner'], akt_jahr, f"Rechnung_{r_nr}.pdf")
        kopie_dir = self.config.get("cli_kopie")
        if kopie_dir and os.path.exists(pdf_pfad):
            try:
                os.makedirs(kopie_dir, exist_ok=True)
                shutil.copy2(pdf_pfad, os.path.join(kopie_dir, os.path.basename(pdf_pfad)))
            except Exception as e:
                print(f"Fehler beim Kopieren: {e}")
        if os.path.exists(pdf_pfad):
            if not self.config.get("cli_no_open", False):
                try:
                    os.startfile(pdf_pfad)
                except Exception:
                    pass

            self.send_invoice_email()
            self.on_closing(skip_warning=True)

    def save_state_to_history(self):
        """Speichert einen Schnappschuss der Maske für Undo."""
        if getattr(self, '_is_restoring', False):
            return
        current_state = {
            'r_nr': self.entry_r_nr.get() if hasattr(self, 'entry_r_nr') else "",
            'r_datum': self.entry_r_datum.get() if hasattr(self, 'entry_r_datum') else "",
            'f_datum': self.entry_f_datum.get() if hasattr(self, 'entry_f_datum') else "",
            'k_nr': self.entry_k_nr.get() if hasattr(self, 'entry_k_nr') else "",
            'az': self.entry_az.get() if hasattr(self, 'entry_az') else "",
            'k_az': self.entry_k_az.get() if hasattr(self, 'entry_k_az') else "",
            'lz_kopf': self.entry_lz_kopf.get() if hasattr(self, 'entry_lz_kopf') else "",
            'k_name': self.entry_k_name.get() if hasattr(self, 'entry_k_name') else "",
            'k_strasse': self.entry_k_strasse.get() if hasattr(self, 'entry_k_strasse') else "",
            'k_plz_ort': self.entry_k_plz_ort.get() if hasattr(self, 'entry_k_plz_ort') else "",
            'k_land': self.entry_k_land.get() if hasattr(self, 'entry_k_land') else "DE",
            'rc': self.combo_rc.get() if hasattr(self, 'combo_rc') else "Nein",
            'k_ustid': self.entry_k_ustid.get() if hasattr(self, 'entry_k_ustid') else "",
            'k_endpoint': self.entry_k_endpoint.get() if hasattr(self, 'entry_k_endpoint') else "",
            'k_scheme': self.entry_k_endpoint_scheme.get() if hasattr(self, 'entry_k_endpoint_scheme') else "",
            'positionen': [p.copy() for p in getattr(self, 'positionen_liste', [])],
            'zusatz_dict': dict(getattr(self, 'zusatz_dict', {}))
        }

        if hasattr(self, 'undo_stack') and self.undo_stack and self.undo_stack[-1] == current_state:
            return
        self.undo_stack.append(current_state)
        if hasattr(self, 'redo_stack'):
            self.redo_stack.clear()
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def _capture_current_state(self):
        return {
            'r_nr': self.entry_r_nr.get(),
            'r_datum': self.entry_r_datum.get(),
            'f_datum': self.entry_f_datum.get(),
            'k_nr': self.entry_k_nr.get(),
            'az': self.entry_az.get(),
            'k_az': self.entry_k_az.get(),
            'lz_kopf': self.entry_lz_kopf.get(),
            'k_name': self.entry_k_name.get(),
            'k_strasse': self.entry_k_strasse.get(),
            'k_plz_ort': self.entry_k_plz_ort.get(),
            'k_land': self.entry_k_land.get(),
            'rc': self.combo_rc.get(),
            'k_ustid': self.entry_k_ustid.get(),
            'k_endpoint': self.entry_k_endpoint.get(),
            'k_scheme': self.entry_k_endpoint_scheme.get(),
            'positionen': [p.copy() for p in self.positionen_liste],
            'zusatz_dict': dict(self.zusatz_dict)
        }

    def perform_undo(self, event=None):
        if not getattr(self, 'undo_stack', None):
            return
        self._is_restoring = True
        self.redo_stack.append(self._capture_current_state())
        prev_state = self.undo_stack.pop()
        self._apply_state(prev_state)
        self._is_restoring = False

    def perform_redo(self, event=None):
        if not getattr(self, 'redo_stack', None):
            return
        self._is_restoring = True
        self.redo_stack.append(self._capture_current_state())
        next_state = self.redo_stack.pop()
        self._apply_state(next_state)
        self._is_restoring = False

    def _apply_state(self, state):
        self.entry_r_nr.delete(0, 'end')
        self.entry_r_nr.insert(0, state['r_nr'])
        self.entry_r_datum.delete(0, 'end')
        self.entry_r_datum.insert(0, state['r_datum'])
        self.entry_f_datum.delete(0, 'end')
        self.entry_f_datum.insert(0, state['f_datum'])
        self.entry_k_nr.delete(0, 'end')
        self.entry_k_nr.insert(0, state['k_nr'])
        self.entry_az.delete(0, 'end')
        self.entry_az.insert(0, state['az'])
        self.entry_k_az.delete(0, 'end')
        self.entry_k_az.insert(0, state['k_az'])
        self.entry_lz_kopf.delete(0, 'end')
        self.entry_lz_kopf.insert(0, state['lz_kopf'])
        if hasattr(self.entry_k_name, 'set'):
            self.entry_k_name.set(state['k_name'])
        else:
            self.entry_k_name.delete(0, 'end')
            self.entry_k_name.insert(0, state['k_name'])
        self.entry_k_strasse.delete(0, 'end')
        self.entry_k_strasse.insert(0, state['k_strasse'])
        self.entry_k_plz_ort.delete(0, 'end')
        self.entry_k_plz_ort.insert(0, state['k_plz_ort'])
        self.entry_k_land.delete(0, 'end')
        self.entry_k_land.insert(0, state.get('k_land', 'DE') or 'DE')
        self.combo_rc.set(state.get('rc', 'Nein') or 'Nein')
        self.entry_k_ustid.delete(0, 'end')
        self.entry_k_ustid.insert(0, state.get('k_ustid', ''))
        self.entry_k_endpoint.delete(0, 'end')
        self.entry_k_endpoint.insert(0, state['k_endpoint'])
        self.entry_k_endpoint_scheme.delete(0, 'end')
        self.entry_k_endpoint_scheme.insert(0, state['k_scheme'])
        self.positionen_liste = [p.copy() for p in state['positionen']]
        self.zusatz_dict = dict(state['zusatz_dict'])
        self.refresh_pos_list()
        self.check_live_validation()