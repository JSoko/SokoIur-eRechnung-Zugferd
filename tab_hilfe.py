import customtkinter as ctk
import tkinter.messagebox as messagebox
import os
import sys
import json
import re
import csv
import threading
import webbrowser
from datetime import datetime
from config import get_appdata_dir
import hilfe_texte
from hilfe_texte import ensure_doku_files


def _get_doku_dir() -> str:
    if getattr(sys, "frozen", False):
        prog_dir = os.path.abspath(os.path.dirname(sys.executable))
    else:
        prog_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(prog_dir, "html")


class TabHilfeMixin:
    def build_hilfe_tab(self):
        scroll_main = ctk.CTkScrollableFrame(self.tab_hilfe, fg_color="transparent")
        scroll_main.pack(fill="both", expand=True, padx=10, pady=10)

        f = ctk.CTkFrame(scroll_main, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=30, pady=10)

        ctk.CTkLabel(f, text="Handbuch & Dokumentation", font=("Helvetica", 20, "bold")).pack(pady=(0, 10))
        ctk.CTkLabel(
            f,
            text="Das Handbuch wird als HTML-Datei erstellt und in Ihrem Standard-Webbrowser geöffnet.",
            justify="center",
        ).pack(pady=(0, 15))

        self.create_button(
            f, text="📖 Handbuch im Browser öffnen", width=250, height=35, command=self.open_html_help
        ).pack(pady=(0, 10))
        self.create_button(
            f, text="📜 Changelog im Browser öffnen", width=250, height=35, command=self.open_changelog_html
        ).pack(pady=(0, 15))

        f_stat = ctk.CTkFrame(
            f, fg_color="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#e6e6e6", corner_radius=8
        )
        f_stat.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            f_stat, text="📊 Programm- & Beleg-Statistik (Aktive Firma)", font=("Helvetica", 14, "bold")
        ).pack(pady=(10, 5))
        self.lbl_stats = ctk.CTkLabel(
            f_stat, text="Statistiken werden geladen... ⏳", justify="left", font=("Helvetica", 12)
        )
        self.lbl_stats.pack(pady=(0, 15), padx=20)

        f_stat_net = ctk.CTkFrame(
            f, fg_color="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#e6e6e6", corner_radius=8
        )
        f_stat_net.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            f_stat_net,
            text="🌐 Programm- & Beleg-Statistik (Netzwerkweit / Alle Firmen)",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(10, 5))
        self.lbl_stats_net = ctk.CTkLabel(
            f_stat_net, text="Netzwerk-Statistiken werden geladen... ⏳", justify="left", font=("Helvetica", 12)
        )
        self.lbl_stats_net.pack(pady=(0, 15), padx=20)

        akt_jahr = str(datetime.now().year)
        threading.Thread(target=self._load_stats_async, args=(akt_jahr,), daemon=True).start()

    def _count_rows_in_folder(self, base_folder: str, year: str, prefix: str) -> int:
        if not base_folder or not os.path.isdir(base_folder):
            return 0
        pattern = re.compile(rf"^{re.escape(prefix)}\d{{6}}\.csv$", re.IGNORECASE)
        count = 0
        year_dir = os.path.join(base_folder, year)
        candidate_dirs = [year_dir] if os.path.isdir(year_dir) else [base_folder]
        for d in candidate_dirs:
            try:
                for fname in os.listdir(d):
                    fpath = os.path.join(d, fname)
                    if os.path.isfile(fpath) and pattern.match(fname):
                        try:
                            with open(fpath, "r", encoding="utf-8-sig") as f:
                                rows = [r for r in csv.DictReader(f, delimiter=";") if any((v or "").strip() for v in r.values())]
                                count += len(rows)
                        except Exception:
                            pass
            except Exception:
                pass
        return count

    def _load_stats_async(self, akt_jahr: str):
        try:
            p_cfg = dict(self.p_config) if hasattr(self, "p_config") else {}
            profiles = list(self.config.get("profiles", [])) if hasattr(self, "config") else []
            base_path = self.config.get("base_data_path", "") if hasattr(self, "config") else ""

            aus_jahr = self._count_rows_in_folder(p_cfg.get("auswertungen_ordner", ""), akt_jahr, "re")
            ein_jahr = self._count_rows_in_folder(p_cfg.get("eingangsjournal_ordner", ""), akt_jahr, "er")

            kunden_anz = len(getattr(self, "kunden_liste", []))
            produkte_anz = len(getattr(self, "produkte_liste", []))

            text_aktiv = (
                f"Aktives Profil: {p_cfg.get('profil_name', '-')}\n"
                f"Ausgangsrechnungen ({akt_jahr}): {aus_jahr}\n"
                f"Eingangsrechnungen ({akt_jahr}): {ein_jahr}\n"
                f"Kundenstamm: {kunden_anz}  |  Produktstamm: {produkte_anz}"
            )

            net_aus_jahr = 0
            net_ein_jahr = 0
            for prof in profiles:
                prof_name = prof.get("profil_name", "").replace(" ", "_")
                aus_dir = prof.get("auswertungen_ordner") or (os.path.join(base_path, prof_name, "aausw") if base_path else "")
                ein_dir = prof.get("eingangsjournal_ordner") or (os.path.join(base_path, prof_name, "eausw") if base_path else "")
                net_aus_jahr += self._count_rows_in_folder(aus_dir, akt_jahr, "re")
                net_ein_jahr += self._count_rows_in_folder(ein_dir, akt_jahr, "er")

            text_net = (
                f"Anzahl Firmenprofile: {len(profiles)}\n"
                f"Ausgangsrechnungen gesamt ({akt_jahr}): {net_aus_jahr}\n"
                f"Eingangsrechnungen gesamt ({akt_jahr}): {net_ein_jahr}"
            )
        except Exception as e:
            text_aktiv = f"Statistik konnte nicht geladen werden: {e}"
            text_net = "Netzwerk-Statistik nicht verfügbar."

        def _apply():
            if hasattr(self, "lbl_stats") and self.lbl_stats.winfo_exists():
                self.lbl_stats.configure(text=text_aktiv)
            if hasattr(self, "lbl_stats_net") and self.lbl_stats_net.winfo_exists():
                self.lbl_stats_net.configure(text=text_net)

        try:
            self.after(0, _apply)
        except Exception:
            pass

    def _write_and_open_doc(self, filename: str, html_content: str, title_label: str):
        target_dir = _get_doku_dir()
        try:
            os.makedirs(target_dir, exist_ok=True)
            out_path = os.path.join(target_dir, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        except OSError:
            app_dir = get_appdata_dir()
            os.makedirs(app_dir, exist_ok=True)
            out_path = os.path.join(app_dir, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)

        if hasattr(os, "startfile"):
            os.startfile(out_path)
        else:
            doc_url = os.path.abspath(out_path).replace("\\", "/")
            webbrowser.open(f"file:///{doc_url}")

    def open_html_help(self):
        try:
            version = getattr(self, "current_version", "1.000")
            html_content = hilfe_texte.get_doku_html(version)
            self._write_and_open_doc("SokoIur_Hilfe.html", html_content, "Hilfe")
        except Exception as e:
            messagebox.showerror(
                "Fehler",
                f"Die Hilfe-Datei konnte nicht geöffnet werden:\n\n{str(e)}",
                parent=self,
            )

    def open_changelog_html(self):
        try:
            version = getattr(self, "current_version", "1.000")
            changelog_content = hilfe_texte.get_changelog_html(version)
            self._write_and_open_doc("changelog.html", changelog_content, "Changelog")
        except Exception as e:
            messagebox.showerror(
                "Fehler",
                f"Die Changelog-Datei konnte nicht geöffnet werden:\n\n{str(e)}",
                parent=self,
            )