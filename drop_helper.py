"""
drop_helper.py
--------------
Eigenständiges Drag & Drop-Hilfsprogramm zum Ablegen von Eingangsrechnungen
in den Eingangsordner (reneu) der jeweiligen Firma aus SokoIur eRechnung.
"""
import argparse
import json
import os
import shutil
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    if hasattr(sys, "_MEIPASS") and sys._MEIPASS not in sys.path:
        sys.path.append(sys._MEIPASS)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)

from config import init_config, speichere_config, get_resource_path

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_TKDND = True
except ImportError:
    HAS_TKDND = False


STATE_FILE_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "SokoIur_eRechnung",
    "drop_helper_state.json",
)


def _load_saved_geometry() -> str:
    try:
        if os.path.isfile(STATE_FILE_PATH):
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            geom = str(data.get("geometry", "")).strip()
            if geom:
                return geom
    except Exception:
        pass
    return "480x270"


def _save_geometry(geometry_str: str) -> None:
    if not geometry_str:
        return
    try:
        os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
        data = {}
        if os.path.isfile(STATE_FILE_PATH):
            try:
                with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["geometry"] = geometry_str
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--profil", dest="profil", default="", help="Name des Firmenprofils")
    parser.add_argument("--profil-index", dest="profil_index", type=int, default=-1, help="Index des Firmenprofils")
    args, _ = parser.parse_known_args()
    return args


class DropHelperApp:
    def __init__(self, initial_profil_name: str = "", initial_profil_index: int = -1):
        self.config = init_config()
        self.profiles = self.config.get("profiles", [])
        self.active_idx = self._resolve_initial_profile_index(initial_profil_name, initial_profil_index)

        if self.profiles and self.config.get("active_profile_index") != self.active_idx:
            self.config["active_profile_index"] = self.active_idx
            try:
                speichere_config(self.config)
            except Exception:
                pass

        self.root = TkinterDnD.Tk() if HAS_TKDND else tk.Tk()
        self.root.title("SokoIur eRechnung – Drop-Helper (Eingangsrechnungen)")

        saved_geom = _load_saved_geometry()
        try:
            self.root.geometry(saved_geom)
        except Exception:
            self.root.geometry("480x270")

        self.root.minsize(380, 220)
        self.root.attributes("-topmost", True)

        icon_path = get_resource_path("SokoIur.ico")
        if icon_path and os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _resolve_initial_profile_index(self, profil_name: str, profil_index: int) -> int:
        if not self.profiles:
            return 0

        if profil_name:
            target_clean = profil_name.strip().lower()
            for idx, prof in enumerate(self.profiles):
                p_name = str(prof.get("profil_name", "")).strip().lower()
                if p_name == target_clean:
                    return idx

        if 0 <= profil_index < len(self.profiles):
            return profil_index

        cfg_idx = int(self.config.get("active_profile_index", 0))
        return min(max(cfg_idx, 0), len(self.profiles) - 1)

    def _current_profile(self) -> dict:
        if not self.profiles:
            return {}
        return self.profiles[self.active_idx]

    def _resolve_reneu_dir(self) -> str:
        prof = self._current_profile()
        reneu = prof.get("eingangsordner", "")
        if reneu and os.path.isdir(reneu):
            return reneu
        base_path = self.config.get("base_data_path", "")
        if base_path and prof.get("profil_name"):
            candidate = os.path.join(base_path, str(prof["profil_name"]).replace(" ", "_"), "reneu")
            os.makedirs(candidate, exist_ok=True)
            return candidate
        return reneu

    def _build_ui(self):
        bg_main = "#1e293b"
        bg_drop = "#0f172a"
        fg_text = "#f8fafc"
        accent = "#38bdf8"

        self.root.configure(bg=bg_main)

        top_frame = tk.Frame(self.root, bg=bg_main)
        top_frame.pack(fill="x", padx=14, pady=(12, 6))

        tk.Label(
            top_frame, text="Firma:", bg=bg_main, fg=fg_text, font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(0, 8))

        profil_namen = [p.get("profil_name", "Firma") for p in self.profiles]
        self.combo_firma = ttk.Combobox(top_frame, values=profil_namen, state="readonly", width=28)
        if profil_namen:
            self.combo_firma.current(self.active_idx)
        self.combo_firma.pack(side="left", fill="x", expand=True)
        self.combo_firma.bind("<<ComboboxSelected>>", self._on_firma_change)

        self.drop_frame = tk.Frame(
            self.root,
            bg=bg_drop,
            highlightbackground=accent,
            highlightthickness=2,
            cursor="hand2",
        )
        self.drop_frame.pack(fill="both", expand=True, padx=14, pady=8)

        hint = (
            "⬇️ Rechnungen (PDF, XML, Scans) hier ablegen\n\n"
            "(oder klicken zum Auswählen)"
            if HAS_TKDND
            else "📄 Klicken, um Rechnungen auszuwählen\n\n"
                 "(Für direktes Drag & Drop 'tkinterdnd2' installieren)"
        )

        self.lbl_status = tk.Label(
            self.drop_frame,
            text=hint,
            bg=bg_drop,
            fg=fg_text,
            font=("Segoe UI", 11, "bold"),
            justify="center",
            wraplength=420,
        )
        self.lbl_status.pack(expand=True, padx=12, pady=12)

        self.drop_frame.bind("<Button-1>", self._pick_files)
        self.lbl_status.bind("<Button-1>", self._pick_files)

        if HAS_TKDND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)
            self.lbl_status.drop_target_register(DND_FILES)
            self.lbl_status.dnd_bind("<<Drop>>", self._on_drop)

        bot_frame = tk.Frame(self.root, bg=bg_main)
        bot_frame.pack(fill="x", padx=14, pady=(0, 10))

        self.lbl_path = tk.Label(
            bot_frame, text="", bg=bg_main, fg="#94a3b8", font=("Segoe UI", 8), anchor="w"
        )
        self.lbl_path.pack(side="left", fill="x", expand=True)

        btn_open = tk.Button(
            bot_frame,
            text="📂 Ordner",
            bg="#334155",
            fg=fg_text,
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._open_target_folder,
        )
        btn_open.pack(side="right")

        self._update_path_label()

    def _update_path_label(self):
        target = self._resolve_reneu_dir()
        self.lbl_path.configure(text=f"Ziel: {target}")

    def _on_firma_change(self, _event=None):
        self.active_idx = max(self.combo_firma.current(), 0)
        self.config["active_profile_index"] = self.active_idx
        try:
            speichere_config(self.config)
        except Exception:
            pass
        self._update_path_label()

    def _open_target_folder(self):
        target = self._resolve_reneu_dir()
        if target and os.path.isdir(target):
            os.startfile(target)

    def _pick_files(self, _event=None):
        paths = filedialog.askopenfilenames(
            title="Belege in Eingangsordner (reneu) kopieren",
            filetypes=[("Belege", "*.pdf *.xml *.jpg *.jpeg *.png *.tif *.tiff"), ("Alle Dateien", "*.*")],
        )
        if paths:
            self._copy_files(paths)

    def _on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        self._copy_files(files)

    def _copy_files(self, paths):
        target_dir = self._resolve_reneu_dir()
        if not target_dir:
            messagebox.showerror("Fehler", "Kein gültiger Eingangsordner (reneu) konfiguriert.")
            return

        os.makedirs(target_dir, exist_ok=True)
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
            self.lbl_status.configure(
                text=f"✅ {copied} Beleg(e) nach 'reneu' kopiert!",
                fg="#4ade80",
            )
            self.root.after(
                2500,
                lambda: self.lbl_status.configure(
                    text="⬇️ Rechnungen (PDF, XML, Scans) hier ablegen\n\n(oder klicken zum Auswählen)",
                    fg="#f8fafc",
                ),
            )

    def _on_close(self):
        try:
            self.root.update_idletasks()
            _save_geometry(self.root.geometry())
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    parsed = _parse_args()
    DropHelperApp(
        initial_profil_name=parsed.profil,
        initial_profil_index=parsed.profil_index,
    ).run()