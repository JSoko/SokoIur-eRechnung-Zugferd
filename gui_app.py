"""
gui_app.py
----------
Hauptklasse und Fensterverwaltung für die grafische Benutzeroberfläche (GUI).
"""
import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import filedialog
import os
import sys
import time
from datetime import datetime, timedelta
import webbrowser

from config import speichere_config, get_resource_path, LOCK_FILE, get_app_version, get_default_profile
from utils import berechne_naechste_rechnungsnummer
from tab_hilfe import TabHilfeMixin
from tab_auswertungen import TabAuswertungenMixin
from tab_einstellungen import TabEinstellungenMixin
from tab_erfassen import TabErfassenMixin
from tab_manuell import TabManuellMixin
from updater import UpdaterMixin
from tab_verwaltung import TabVerwaltungMixin
from gui_utils import create_tooltip
from tab_dashboard import TabDashboardMixin
from tab_eingang_journal import TabEingangJournalMixin
from license_manager import LicenseManager

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class _TabHostProxy:
    """Kleine Kompatibilitäts-Hülle, damit Aufrufe wie self.tabview.get() und self.tabview.set(...) weiter funktionieren."""

    def __init__(self, app):
        self._app = app

    def get(self):
        return self._app.active_tab_name

    def set(self, tab_name):
        self._app.show_tab(tab_name, run_change_logic=False)

    def configure(self, **kwargs):
        pass


class App(
    ctk.CTk,
    TabManuellMixin,
    TabErfassenMixin,
    TabAuswertungenMixin,
    TabEingangJournalMixin,
    TabEinstellungenMixin,
    TabHilfeMixin,
    UpdaterMixin,
    TabVerwaltungMixin,
    TabDashboardMixin,
):

    def apply_window_icon(self, window):
        """Setzt das Programm-Icon zuverlässig auf das Hauptfenster oder einen Toplevel-Dialog."""
        icon_path = get_resource_path("SokoIur.ico")
        if not icon_path or not os.path.exists(icon_path):
            return
        try:
            window.iconbitmap(icon_path)
        except Exception:
            pass
        try:
            window.after(150, lambda w=window, p=icon_path: w.iconbitmap(p) if w.winfo_exists() else None)
        except Exception:
            pass

    def _popup_parent(self, parent=None):
        """Wählt das aktuell aktive/sichtbare Top-Level-Fenster für die Zentrierung."""
        if parent is not None and parent.winfo_exists():
            return parent
        try:
            focus_w = self.focus_get()
            if focus_w is not None and focus_w.winfo_exists():
                top = focus_w.winfo_toplevel()
                if top is not None and top.winfo_exists():
                    return top
        except Exception:
            pass
        return self

    def center_on_target(self, dialog, target, width, height):
        """Zentriert einen Dialog mittig über dem Ziel-Fenster oder auf dem Bildschirm, falls noch nicht sichtbar."""
        self.update_idletasks()
        use_target = False
        if target is not None and target.winfo_exists():
            target.update_idletasks()
            tw, th = target.winfo_width(), target.winfo_height()
            if tw > 50 and th > 50 and target.winfo_viewable():
                tx, ty = target.winfo_rootx(), target.winfo_rooty()
                x = tx + (tw // 2) - (width // 2)
                y = ty + (th // 2) - (height // 2)
                use_target = True
        if not use_target:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw // 2) - (width // 2)
            y = (sh // 2) - (height // 2)
        x = max(0, x)
        y = max(0, y)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _show_custom_dialog(self, title, message, kind="info", buttons=("OK",), default_index=0, parent=None):
        anchor = self._popup_parent(parent)
        dlg = ctk.CTkToplevel(anchor if anchor is not self else self)
        dlg.title(title)
        self.apply_window_icon(dlg)

        zeilen = message.count("\n") + max(1, len(message) // 52)
        hoehe = min(460, max(170, 100 + zeilen * 18))
        breite = 460
        self.center_on_target(dlg, anchor, breite, hoehe)
        parent_win = anchor if anchor is not self else self
        try:
            if parent_win.winfo_exists() and parent_win.winfo_viewable():
                dlg.transient(parent_win)
            else:
                dlg.attributes("-topmost", True)
        except Exception:
            pass

        farben = {
            "info": ("ℹ️", "#1f538d"),
            "warn": ("⚠️", "#b85c00"),
            "error": ("❌", "#b30000"),
            "ask": ("❓", "#1f538d"),
        }
        symbol, akzent = farben.get(kind, ("ℹ️", "#1f538d"))

        f_top = ctk.CTkFrame(dlg, fg_color="transparent")
        f_top.pack(fill="both", expand=True, padx=16, pady=(14, 6))

        ctk.CTkLabel(f_top, text=symbol, font=("Helvetica", 22), width=36).pack(side="left", anchor="n", padx=(0, 8))
        ctk.CTkLabel(
            f_top,
            text=message,
            font=("Helvetica", 12),
            justify="left",
            wraplength=375,
        ).pack(side="left", fill="both", expand=True)

        default_cancel = False if kind == "ask" else None
        result = {"value": default_cancel}
        closed = {"done": False}

        top_bg = dlg._apply_appearance_mode(ctk.ThemeManager.theme["CTkToplevel"]["fg_color"])
        f_btns = tk.Frame(dlg, bg=top_bg)
        f_btns.pack(pady=(6, 14))

        def choose(val):
            if closed["done"]:
                return
            closed["done"] = True
            result["value"] = val
            try:
                dlg.grab_release()
            except Exception:
                pass
            if dlg.winfo_exists():
                dlg.destroy()

        dlg.protocol("WM_DELETE_WINDOW", lambda: choose(default_cancel))

        btn_widgets = []
        btn_values = []
        btn_labels = []

        inactive_bg = "#289102"
        inactive_bd = "#1b6301"
        active_bg = "#ffd400"
        active_fg = "#111111"
        active_bd = "#ffffff"

        for b_text in buttons:
            if b_text in ("Ja", "OK", "Erhöhen"):
                val = True
            elif b_text in ("Nein", "Beibehalten"):
                val = False
            else:
                val = b_text

            btn = tk.Button(
                f_btns,
                text=b_text,
                width=14,
                font=("Helvetica", 11, "bold"),
                bg=inactive_bg,
                fg="#ffffff",
                activebackground=active_bg,
                activeforeground=active_fg,
                relief="flat",
                bd=3,
                highlightthickness=3,
                highlightbackground=inactive_bd,
                highlightcolor=active_bg,
                takefocus=1,
                cursor="hand2",
                command=lambda v=val: choose(v),
            )
            btn.pack(side="left", padx=8, ipadx=6, ipady=4)
            btn_widgets.append(btn)
            btn_values.append(val)
            btn_labels.append(b_text)

        current_idx = {"i": min(max(default_index, 0), max(len(btn_widgets) - 1, 0))}

        def _paint_active(idx):
            for k, b in enumerate(btn_widgets):
                base_label = btn_labels[k]
                if k == idx:
                    b.configure(
                        text=f"▶ {base_label}",
                        bg=active_bg,
                        fg=active_fg,
                        relief="raised",
                        bd=3,
                        highlightbackground=active_bd,
                        highlightcolor=active_bd,
                    )
                else:
                    b.configure(
                        text=base_label,
                        bg=inactive_bg,
                        fg="#ffffff",
                        relief="flat",
                        bd=2,
                        highlightbackground=inactive_bd,
                        highlightcolor=inactive_bd,
                    )

        def set_focus_idx(idx, move_focus=True):
            if not btn_widgets:
                return
            idx = idx % len(btn_widgets)
            current_idx["i"] = idx
            _paint_active(idx)
            target = btn_widgets[idx]
            if move_focus and dlg.focus_get() is not target:
                target.focus_set()

        def step_focus(delta, event=None):
            if not btn_widgets:
                return "break"
            set_focus_idx(current_idx["i"] + delta, move_focus=True)
            return "break"

        def trigger_current(event=None):
            if not btn_widgets:
                return "break"
            choose(btn_values[current_idx["i"]])
            return "break"

        custom_tag = f"DlgNavTag_{id(dlg)}"
        for k, b in enumerate(btn_widgets):
            tags = [t for t in b.bindtags() if t != "Button"]
            if custom_tag not in tags:
                idx_w = tags.index(str(b)) if str(b) in tags else 0
                tags.insert(idx_w + 1, custom_tag)
            b.bindtags(tuple(tags))

            b.bind("<FocusIn>", lambda e, idx_k=k: set_focus_idx(idx_k, move_focus=False), add="+")
            b.bind("<Button-1>", lambda e, idx_k=k: set_focus_idx(idx_k, move_focus=True), add="+")
            b.bind("<ButtonRelease-1>", lambda e, v=btn_values[k]: choose(v), add="+")
            b.bind("<Return>", trigger_current)
            b.bind("<KP_Enter>", trigger_current)
            b.bind("<space>", trigger_current)

        dlg.bind_class(custom_tag, "<Tab>", lambda e: step_focus(1, e))
        dlg.bind_class(custom_tag, "<ISO_Left_Tab>", lambda e: step_focus(-1, e))
        dlg.bind_class(custom_tag, "<Shift-Tab>", lambda e: step_focus(-1, e))
        dlg.bind_class(custom_tag, "<Left>", lambda e: step_focus(-1, e))
        dlg.bind_class(custom_tag, "<Right>", lambda e: step_focus(1, e))
        dlg.bind_class(custom_tag, "<Return>", trigger_current)
        dlg.bind_class(custom_tag, "<KP_Enter>", trigger_current)
        dlg.bind_class(custom_tag, "<space>", trigger_current)

        dlg.bind("<Tab>", lambda e: step_focus(1, e))
        dlg.bind("<ISO_Left_Tab>", lambda e: step_focus(-1, e))
        dlg.bind("<Shift-Tab>", lambda e: step_focus(-1, e))
        dlg.bind("<Left>", lambda e: step_focus(-1, e))
        dlg.bind("<Right>", lambda e: step_focus(1, e))
        dlg.bind("<Return>", trigger_current)
        dlg.bind("<KP_Enter>", trigger_current)
        dlg.bind("<Escape>", lambda e: choose(default_cancel))

        dlg.update_idletasks()
        try:
            dlg.wait_visibility()
            dlg.grab_set()
        except Exception:
            pass

        if btn_widgets:
            dlg.after(20, lambda: dlg.winfo_exists() and set_focus_idx(current_idx["i"], move_focus=True))

        self.wait_window(dlg)
        return result["value"]

    def show_info(self, title, message, parent=None):
        return self._show_custom_dialog(title, message, kind="info", buttons=("OK",), parent=parent)

    def show_warning(self, title, message, parent=None):
        return self._show_custom_dialog(title, message, kind="warn", buttons=("OK",), parent=parent)

    def show_error(self, title, message, parent=None):
        return self._show_custom_dialog(title, message, kind="error", buttons=("OK",), parent=parent)

    def ask_yes_no(self, title, message, parent=None, default="yes"):
        idx = 1 if str(default).strip().lower() == "no" else 0
        res = self._show_custom_dialog(
            title,
            message,
            kind="ask",
            buttons=("Ja", "Nein"),
            default_index=idx,
            parent=parent,
        )
        return res is True

    def get_firm_lock_path(self, lock_name="erechnung.lock"):
        base_path = self.config.get("base_data_path")
        if not base_path:
            return None
        firm_dir = os.path.join(base_path, self.p_config["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir):
            os.makedirs(firm_dir, exist_ok=True)
        return os.path.join(firm_dir, lock_name)

    def set_firm_lock(self, lock_name="erechnung.lock"):
        lock_file = self.get_firm_lock_path(lock_name)
        if not lock_file:
            return
        if not hasattr(self, "current_lock_files"):
            self.current_lock_files = {}
        try:
            with open(lock_file, "w") as f:
                f.write(str(os.getpid()))
            self.current_lock_files[lock_name] = lock_file
        except Exception:
            pass

    def unlock_firm(self, lock_name=None):
        if not hasattr(self, "current_lock_files"):
            self.current_lock_files = {}

        candidates = []
        if lock_name:
            if self.current_lock_files.get(lock_name):
                candidates.append((lock_name, self.current_lock_files.get(lock_name)))
            p = self.get_firm_lock_path(lock_name)
            if p:
                candidates.append((lock_name, p))
        else:
            for lname, lfile in list(self.current_lock_files.items()):
                if lfile:
                    candidates.append((lname, lfile))
            for default_lock in ("erechnung.lock", "erfassung.lock"):
                p = self.get_firm_lock_path(default_lock)
                if p:
                    candidates.append((default_lock, p))

        seen = set()
        for lname, lfile in candidates:
            norm = os.path.abspath(lfile)
            if norm in seen:
                continue
            seen.add(norm)

            if os.path.exists(lfile):
                can_remove = True
                try:
                    with open(lfile, "r") as f:
                        content = f.read().strip()
                    if content and content.isdigit() and content != str(os.getpid()):
                        can_remove = False
                except Exception:
                    pass

                if can_remove:
                    for _ in range(5):
                        try:
                            os.remove(lfile)
                            break
                        except PermissionError:
                            time.sleep(0.05)
                        except FileNotFoundError:
                            break
                        except Exception:
                            break

            if lname in self.current_lock_files:
                self.current_lock_files[lname] = None

    def lock_firm(self, p_dict, lock_name="erechnung.lock"):
        base_path = self.config.get("base_data_path")
        if not base_path:
            return True
        firm_dir = os.path.join(base_path, p_dict["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir):
            os.makedirs(firm_dir, exist_ok=True)

        lock_file = os.path.join(firm_dir, lock_name)
        if not hasattr(self, "current_lock_files"):
            self.current_lock_files = {}

        if self.current_lock_files.get(lock_name) == lock_file:
            return True

        if os.path.exists(lock_file):
            try:
                file_age = time.time() - os.path.getmtime(lock_file)
                if file_age > 43200:
                    os.remove(lock_file)
                else:
                    self.show_warning(
                        "Firma gesperrt",
                        f"Die Firma '{p_dict['profil_name']}' wird aktuell bearbeitet ({lock_name}).",
                    )
                    return False
            except Exception:
                return False

        try:
            with open(lock_file, "w") as f:
                f.write(str(os.getpid()))
            self.current_lock_files[lock_name] = lock_file
            return True
        except Exception:
            return True

    def check_and_handle_lock(self, target_tab, lock_name="erechnung.lock"):
        base_path = self.config.get("base_data_path")
        if not base_path:
            return True
        firm_dir = os.path.join(base_path, self.p_config["profil_name"].replace(" ", "_"))
        if not os.path.exists(firm_dir):
            os.makedirs(firm_dir, exist_ok=True)
        lock_file = os.path.join(firm_dir, lock_name)

        if not hasattr(self, "current_lock_files"):
            self.current_lock_files = {}
        if self.current_lock_files.get(lock_name) == lock_file:
            return True

        while os.path.exists(lock_file):
            try:
                with open(lock_file, "r") as f:
                    content = f.read().strip()
                if content == str(os.getpid()):
                    self.current_lock_files[lock_name] = lock_file
                    return True
            except Exception:
                pass

            dlg = ctk.CTkToplevel(self)
            dlg.title("Firma gesperrt")
            self.apply_window_icon(dlg)
            self.center_window(dlg, 450, 200)
            dlg.transient(self)
            dlg.grab_set()

            modul = "Rechnungserfassung" if lock_name == "erfassung.lock" else "Rechnungserstellung"
            ctk.CTkLabel(
                dlg,
                text=f"Die Firma '{self.p_config['profil_name']}' wird aktuell\nim Bereich {modul} bearbeitet.",
                font=("Helvetica", 13, "bold"),
                justify="center",
            ).pack(pady=20)

            f_btn = ctk.CTkFrame(dlg, fg_color="transparent")
            f_btn.pack(pady=10)

            result = {"action": None}

            def do_retry():
                result["action"] = "retry"
                dlg.destroy()

            def do_force_unlock():
                if self.ask_yes_no(
                    "Sicherheitswarnung",
                    f"Soll der Lock ({lock_name}) wirklich entfernt werden?\n\nEs droht Datenverlust!",
                    parent=dlg,
                    default="no",
                ):
                    result["action"] = "force"
                    dlg.destroy()

            self.create_button(f_btn, text="Erneut prüfen", width=120, command=do_retry).pack(side="left", padx=5)
            self.create_button(
                f_btn,
                text="Lock entfernen",
                width=120,
                fg_color="#b30000",
                hover_color="#800000",
                command=do_force_unlock,
            ).pack(side="left", padx=5)
            self.wait_window(dlg)

            if result["action"] == "retry":
                continue
            elif result["action"] == "force":
                try:
                    os.remove(lock_file)
                except Exception:
                    pass
                break
            else:
                return False
        return True

    def _update_tab_button_styles(self):
        if not hasattr(self, "tab_buttons"):
            return
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        for name, item in self.tab_buttons.items():
            is_active = (name == self.active_tab_name)
            if isinstance(item, dict):
                item["is_active"] = is_active
                redraw_fn = item.get("redraw")
                if callable(redraw_fn):
                    redraw_fn(hovered=bool(item.get("hovered", False)))
            elif item is not None and hasattr(item, "configure"):
                if is_active:
                    item.configure(
                        fg_color=("#1f538d", "#1f538d"),
                        hover_color=("#14375d", "#14375d"),
                        text_color=("#ffffff", "#ffffff"),
                    )
                else:
                    item.configure(
                        fg_color=("#e8eef5", "#2b3038") if not is_dark else ("#2b3038", "#2b3038"),
                        hover_color=("#d7e3f1", "#383f4a"),
                        text_color=("#1e293b", "#e2e8f0"),
                    )

    def _create_glass_tab_button(self, parent, full_label, shortcut_char, command):
        import tkinter.font as tkfont

        canvas = tk.Canvas(parent, height=38, highlightthickness=0, bd=0, cursor="hand2")
        state = {"is_active": False, "hovered": False, "redraw": None}

        font_norm = tkfont.Font(family="Segoe UI", size=16)
        font_under = tkfont.Font(family="Segoe UI", size=16, underline=True)

        def _round_rect(c, x1, y1, x2, y2, r, **kwargs):
            pts = [
                x1 + r, y1,
                x2 - r, y1,
                x2, y1,
                x2, y1 + r,
                x2, y2 - r,
                x2, y2,
                x2 - r, y2,
                x1 + r, y2,
                x1, y2,
                x1, y2 - r,
                x1, y1 + r,
                x1, y1,
            ]
            return c.create_polygon(pts, smooth=True, splinesteps=24, **kwargs)

        def redraw(hovered=False):
            state["hovered"] = hovered
            if not canvas.winfo_exists():
                return
            w = max(canvas.winfo_width(), 60)
            h = max(canvas.winfo_height(), 36)
            is_dark = ctk.get_appearance_mode().lower() == "dark"

            try:
                parent_bg = parent._apply_appearance_mode(ctk.ThemeManager.theme["CTk"]["fg_color"])
            except Exception:
                parent_bg = "#1e1e1e" if is_dark else "#f2f4f7"
            canvas.configure(bg=parent_bg)
            canvas.delete("all")

            active = state["is_active"]
            if active:
                fill_col = "#1f538d" if not hovered else "#2563a8"
                border_col = "#60a5fa"
                top_gloss = "#7dd3fc"
                txt_col = "#ffffff"
                accent_col = "#ffd400"
            else:
                if is_dark:
                    fill_col = "#2c333d" if not hovered else "#374151"
                    border_col = "#4b5563" if not hovered else "#6b7280"
                    top_gloss = "#64748b"
                    txt_col = "#f1f5f9"
                    accent_col = "#38bdf8"
                else:
                    fill_col = "#eef3f9" if not hovered else "#e1ebf7"
                    border_col = "#bfd0e4" if not hovered else "#93b4d8"
                    top_gloss = "#ffffff"
                    txt_col = "#1e293b"
                    accent_col = "#1f538d"

            _round_rect(canvas, 1, 1, w - 2, h - 2, 10, fill=fill_col, outline=border_col, width=1.2)
            canvas.create_line(10, 3, w - 10, 3, fill=top_gloss, width=1)

            if active:
                canvas.create_line(14, h - 4, w - 14, h - 4, fill=accent_col, width=2)

            idx_u = -1
            if shortcut_char and len(shortcut_char) == 1:
                idx_u = full_label.lower().find(shortcut_char.lower())

            if idx_u != -1:
                pre = full_label[:idx_u]
                mid = full_label[idx_u]
                post = full_label[idx_u + 1:]
                w_pre = font_norm.measure(pre)
                w_mid = font_under.measure(mid)
                w_post = font_norm.measure(post)
                total_w = w_pre + w_mid + w_post
                start_x = (w - total_w) / 2.0
                cy = h / 2.0 - (1 if active else 0)

                if pre:
                    canvas.create_text(start_x, cy, text=pre, anchor="w", font=font_norm, fill=txt_col)
                canvas.create_text(start_x + w_pre, cy, text=mid, anchor="w", font=font_under, fill=txt_col)
                if post:
                    canvas.create_text(start_x + w_pre + w_mid, cy, text=post, anchor="w", font=font_norm, fill=txt_col)
            else:
                cy = h / 2.0 - (1 if active else 0)
                canvas.create_text(w / 2.0, cy, text=full_label, anchor="center", font=font_norm, fill=txt_col)

        state["redraw"] = redraw
        canvas.bind("<Configure>", lambda e: redraw(state["hovered"]))
        canvas.bind("<Enter>", lambda e: redraw(True))
        canvas.bind("<Leave>", lambda e: redraw(False))
        canvas.bind("<Button-1>", lambda e: command())
        return canvas, state

    def build_profile_header(self):
        for w in self.header_container.winfo_children():
            w.destroy()

        f_firm = ctk.CTkFrame(self.header_container, fg_color="transparent")
        f_firm.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(f_firm, text="Firma:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(0, 6))

        profil_namen = [p["profil_name"] for p in self.config["profiles"]]
        self.combo_profile = ctk.CTkComboBox(
            f_firm,
            values=profil_namen,
            width=180,
            height=36,
            corner_radius=10,
            command=self.on_profile_switch,
        )
        self.combo_profile.set(self.p_config["profil_name"])
        self.combo_profile.pack(side="left")

        f_tabs = ctk.CTkFrame(self.header_container, fg_color="transparent")
        f_tabs.pack(side="left", fill="x", expand=True)

        tab_specs = [
            (self.name_manuell, "E", "Rechnung erstellen (Alt+E)"),
            (self.name_erfassen, "F", "Eingangsrechnungen erfassen (Alt+F)"),
            (self.name_ausgang, "A", "Ausgangsrechnungen / Journal (Alt+A)"),
            (self.name_eingang, "I", "Eingangsrechnungen / Journal (Alt+I)"),
            (self.name_settings, "K", "Einstellungen & Konfiguration (Alt+K)"),
            (self.name_hilfe, "", "Hilfe & Info (F1)"),
        ]

        self.tab_buttons = {}
        for idx, (tab_name, shortcut_char, tip_text) in enumerate(tab_specs):
            f_tabs.columnconfigure(idx, weight=1, uniform="top_tabs")
            btn_canvas, btn_state = self._create_glass_tab_button(
                f_tabs,
                full_label=tab_name,
                shortcut_char=shortcut_char,
                command=lambda t=tab_name: self.show_tab(t, run_change_logic=True),
            )
            btn_canvas.grid(
                row=0,
                column=idx,
                sticky="ew",
                padx=(0 if idx == 0 else 4, 0 if idx == len(tab_specs) - 1 else 4),
            )
            create_tooltip(btn_canvas, tip_text)
            self.tab_buttons[tab_name] = btn_state

        self._update_tab_button_styles()

    def show_tab(self, tab_name, run_change_logic=True):
        if tab_name not in self.tab_frames:
            return
        self.active_tab_name = tab_name
        for name, frame in self.tab_frames.items():
            if name == tab_name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self._update_tab_button_styles()
        if run_change_logic and not getattr(self, "_initializing", False):
            self.on_tab_change()

    def on_tab_change(self):
        if getattr(self, "_initializing", False):
            return
        selected_tab = self.active_tab_name

        if not self.loaded_tabs.get(selected_tab, True):
            if selected_tab == self.name_manuell:
                self.build_manuell_tab()
            elif selected_tab == self.name_erfassen:
                self.build_erfassen_tab()
            elif selected_tab == self.name_ausgang:
                self.build_ausgang_tab()
            elif selected_tab == self.name_eingang:
                self.build_eingang_tab()
            elif selected_tab == self.name_settings:
                self.build_settings_tab()
            elif selected_tab == self.name_hilfe:
                self.build_hilfe_tab()
            self.loaded_tabs[selected_tab] = True

        if selected_tab == self.name_manuell:
            if not self.check_and_handle_lock(selected_tab, "erechnung.lock"):
                self.show_tab(self.name_hilfe, run_change_logic=False)
                return
            self.lock_firm(self.p_config, "erechnung.lock")
            self.unlock_firm("erfassung.lock")

        elif selected_tab == self.name_erfassen:
            if not self.check_and_handle_lock(selected_tab, "erfassung.lock"):
                self.show_tab(self.name_hilfe, run_change_logic=False)
                return
            self.lock_firm(self.p_config, "erfassung.lock")
            self.unlock_firm("erechnung.lock")

        elif selected_tab == self.name_settings:
            if not self.check_and_handle_lock(selected_tab, "erechnung.lock") or not self.check_and_handle_lock(
                selected_tab, "erfassung.lock"
            ):
                self.show_tab(self.name_hilfe, run_change_logic=False)
                return
            self.lock_firm(self.p_config, "erechnung.lock")
            self.lock_firm(self.p_config, "erfassung.lock")

        elif selected_tab == self.name_ausgang:
            self.unlock_firm()
            if hasattr(self, "refresh_ausgang_journal_ui"):
                self.refresh_ausgang_journal_ui()

        elif selected_tab == self.name_eingang:
            self.unlock_firm()
            if hasattr(self, "refresh_eingang_journal_ui"):
                self.refresh_eingang_journal_ui()

        else:
            self.unlock_firm()

        self._update_tab_button_styles()

    def __init__(self, config, start_in_edit=False):
        super().__init__()
        self.config = config
        self.start_in_edit = start_in_edit
        self._initializing = True
        self.title("SokoIur eRechnung")
        self.license_mgr = LicenseManager(self)

        self.current_version = get_app_version()
        self.apply_window_icon(self)
        self.minsize(650, 550)

        saved_geometry = self.config.get("window_geometry", "950x700")
        win_state = self.config.get("window_state", "normal")

        try:
            tk.Tk.geometry(self, saved_geometry)
        except Exception:
            self.geometry(saved_geometry)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.name_manuell = "📝 Erstellen"
        self.name_erfassen = "📥 Erfassen"
        self.name_ausgang = "📤 Ausgang"
        self.name_eingang = "📥 Eingang"
        self.name_settings = "⚙️ Konfig"
        self.name_hilfe = "ℹ️ Info"
        self.active_tab_name = self.name_manuell
        self.tabview = _TabHostProxy(self)

        self.bind("<plus>", self.handle_plus_key)
        self.bind("<KP_Add>", self.handle_plus_key)
        self.bind("<Alt-l>", lambda e: self.load_manual_invoice(is_button_click=True))
        self.bind("<Alt-L>", lambda e: self.load_manual_invoice(is_button_click=True))
        self.bind("<Alt-t>", lambda e: self.open_texte_popup())
        self.bind("<Alt-T>", lambda e: self.open_texte_popup())
        self.bind("<Alt-s>", lambda e: self.save_manual_invoice())
        self.bind("<Alt-S>", lambda e: self.save_manual_invoice())
        self.bind("<Alt-p>", lambda e: self.save_generate_open_exit())
        self.bind("<Alt-P>", lambda e: self.save_generate_open_exit())
        self.bind("<Alt-e>", lambda e: self.show_tab(self.name_manuell))
        self.bind("<Alt-E>", lambda e: self.show_tab(self.name_manuell))
        self.bind("<Alt-f>", lambda e: self.show_tab(self.name_erfassen))
        self.bind("<Alt-F>", lambda e: self.show_tab(self.name_erfassen))
        self.bind("<Alt-a>", lambda e: self.show_tab(self.name_ausgang))
        self.bind("<Alt-A>", lambda e: self.show_tab(self.name_ausgang))
        self.bind("<Alt-i>", lambda e: self.show_tab(self.name_eingang))
        self.bind("<Alt-I>", lambda e: self.show_tab(self.name_eingang))
        self.bind("<Alt-k>", lambda e: self.show_tab(self.name_settings))
        self.bind("<Alt-K>", lambda e: self.show_tab(self.name_settings))
        self.bind("<F1>", lambda e: self.show_tab(self.name_hilfe))
        self.bind("<Control-z>", lambda e: self.perform_undo() if hasattr(self, "perform_undo") else None)
        self.bind("<Control-Z>", lambda e: self.perform_undo() if hasattr(self, "perform_undo") else None)
        self.bind("<Control-y>", lambda e: self.perform_redo() if hasattr(self, "perform_redo") else None)
        self.bind("<Control-Y>", lambda e: self.perform_redo() if hasattr(self, "perform_redo") else None)

        self.header_container = ctk.CTkFrame(self, fg_color="transparent")
        self.header_container.pack(fill="x", padx=5, pady=(1, 0))

        f_footer = ctk.CTkFrame(self, fg_color="transparent")
        f_footer.pack(side="bottom", fill="x", padx=5, pady=2)

        lbl_footer_l = ctk.CTkLabel(f_footer, text="(C) Joachim Sokolowski", text_color="#1f538d", cursor="hand2")
        lbl_footer_l.pack(side="left")
        lbl_footer_l.bind("<Button-1>", lambda e: webbrowser.open("https://sokolowski.org"))

        lbl_footer_c = ctk.CTkLabel(f_footer, text=f"| Version: {self.current_version}")
        lbl_footer_c.pack(side="left", padx=10)

        self.btn_footer_exit = ctk.CTkButton(
            f_footer,
            text="Beenden",
            width=80,
            fg_color="#b30000",
            hover_color="#800000",
            command=self.on_closing,
        )
        self.btn_footer_exit.pack(side="right", padx=(5, 0))

        self.btn_footer_hilfe = ctk.CTkButton(
            f_footer,
            text="Hilfe",
            width=80,
            fg_color="#1f538d",
            hover_color="#14375d",
            command=self.open_html_help,
        )
        self.btn_footer_hilfe.pack(side="right", padx=5)

        self.btn_footer_update = ctk.CTkButton(
            f_footer,
            text="Update?",
            width=80,
            fg_color="#555",
            hover_color="#777",
            command=self.check_for_updates,
        )
        self.btn_footer_update.pack(side="right")

        self.content_host = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#cbd5e1", "#3a3d42"),
        )
        self.content_host.pack(padx=3, pady=(1, 1), fill="both", expand=True)

        self.loaded_tabs = {
            self.name_manuell: False,
            self.name_erfassen: False,
            self.name_ausgang: False,
            self.name_eingang: False,
            self.name_settings: False,
            self.name_hilfe: False,
        }

        self.tab_manuell = ctk.CTkFrame(self.content_host, fg_color="transparent")
        self.tab_erfassen = ctk.CTkFrame(self.content_host, fg_color="transparent")
        self.tab_ausgang = ctk.CTkFrame(self.content_host, fg_color="transparent")
        self.tab_eingang = ctk.CTkFrame(self.content_host, fg_color="transparent")
        self.tab_settings = ctk.CTkFrame(self.content_host, fg_color="transparent")
        self.tab_hilfe = ctk.CTkFrame(self.content_host, fg_color="transparent")

        self.tab_frames = {
            self.name_manuell: self.tab_manuell,
            self.name_erfassen: self.tab_erfassen,
            self.name_ausgang: self.tab_ausgang,
            self.name_eingang: self.tab_eingang,
            self.name_settings: self.tab_settings,
            self.name_hilfe: self.tab_hilfe,
        }

        self.build_profile_header()

        if not self.config.get("base_data_path"):
            try:
                import pyi_splash
                pyi_splash.close()
            except ImportError:
                pass

            new_path = self.ask_for_base_path("Zentralen Datenspeicherort festlegen")
            if not new_path:
                sys.exit(0)
            self.config["base_data_path"] = new_path
            self.license_mgr._load_and_sync_state()

            shared_config_path = os.path.join(new_path, "shared_firms.json")
            firmen_gefunden = False
            if os.path.exists(shared_config_path):
                import json
                try:
                    with open(shared_config_path, "r", encoding="utf-8") as f:
                        net_profiles = json.load(f)
                        if net_profiles:
                            self.config["profiles"] = net_profiles
                            self.config["active_profile_index"] = 0
                            self.build_profile_header()
                            firmen_gefunden = True

                            self.show_info(
                                "Netzwerk-Daten gefunden",
                                f"Es wurden {len(net_profiles)} bereits bestehende Firmen im Netzwerklaufwerk gefunden und in Ihre lokale Ansicht übernommen!",
                            )
                except Exception:
                    pass

            self.setup_firm_folders(self.p_config, show_message=not firmen_gefunden)
            speichere_config(self.config)
        else:
            self.setup_firm_folders(self.p_config)

        if not self.enforce_network_version():
            return

        lock_file = self.get_firm_lock_path()
        while lock_file and os.path.exists(lock_file):
            is_other_process = True
            try:
                with open(lock_file, "r") as f:
                    content = f.read().strip()
                if content == str(os.getpid()):
                    is_other_process = False
            except Exception:
                pass

            if not is_other_process:
                break

            try:
                import pyi_splash
                pyi_splash.close()
            except ImportError:
                pass

            wahl = self._show_custom_dialog(
                "Programmstart verweigert",
                f"Die Firma '{self.p_config['profil_name']}' ist bereits auf diesem oder einem anderen Rechner in Bearbeitung (Lock aktiv).\n\n"
                "Das Programm wird zum Schutz vor Datenkonflikten beendet, sofern der Lock nicht entfernt wird.",
                kind="error",
                buttons=("OK", "Noch einmal prüfen", "Lock entfernen"),
                default_index=0,
            )

            if wahl == "Noch einmal prüfen":
                continue
            elif wahl == "Lock entfernen":
                if self.ask_yes_no(
                    "Sicherheitswarnung",
                    f"Soll der Lock ({os.path.basename(lock_file)}) im Firmenordner wirklich entfernt werden?\n\n"
                    "Es droht Datenverlust, falls die Firma auf einem anderen Rechner noch geöffnet ist!",
                    default="no",
                ):
                    try:
                        if os.path.exists(lock_file):
                            os.remove(lock_file)
                    except Exception as e:
                        self.show_error("Fehler", f"Lock-Datei konnte nicht entfernt werden:\n{e}")
                    continue
                else:
                    continue
            else:
                sys.exit(0)

        self.set_firm_lock()
        self.refresh_all_ui()
        self.show_tab(self.name_manuell, run_change_logic=False)

        self._initializing = False
        if win_state == "zoomed":
            self.after(100, lambda: self.state("zoomed") if self.winfo_exists() else None)

        if self.config.get("background_update_check", False) and hasattr(self, "schedule_background_update_check"):
            self._bg_update_scheduled = True
            self.after(65000, self.schedule_background_update_check)

        if start_in_edit:
            import_pfad = self.config.get("cli_override_rechnung_csv")
            self.after(200, lambda: self.load_manual_invoice(is_button_click=False, silent=True, custom_path=import_pfad))

    @property
    def p_config(self):
        return self.config["profiles"][self.config["active_profile_index"]]

    def ask_for_base_path(self, title_text):
        program_dir = os.path.abspath(os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__))
        while True:
            self.show_info(
                "Datenspeicherort wählen",
                f"{title_text}\n\nBitte wählen Sie einen Ordner für die Datenspeicherung.\n\n"
                "WICHTIG: Der Ordner darf NICHT im oder unterhalb des Programmverzeichnisses liegen! "
                "Bei der Nutzung von mehreren Rechnern aus sollte zwingend ein freigegebenes Netzwerklaufwerk gewählt werden.",
            )
            path = filedialog.askdirectory(title="Daten-Grundpfad wählen")
            if not path:
                if self.ask_yes_no(
                    "Abbruch", "Ohne Datenspeicherort kann die Firma nicht eingerichtet werden. Möchten Sie abbrechen?"
                ):
                    return None
                continue

            path_abs = os.path.abspath(path)
            try:
                common = os.path.commonpath([program_dir, path_abs])
                if common == program_dir:
                    self.show_warning(
                        "Ungültiger Pfad",
                        f"Der gewählte Pfad liegt innerhalb des Programmordners:\n{program_dir}\n\nBitte wählen Sie einen anderen Ort (z. B. auf einem Netzwerklaufwerk).",
                    )
                    continue
            except ValueError:
                pass

            return path_abs

    def setup_firm_folders(self, p_dict, show_message=False):
        base_path = self.config.get("base_data_path")
        if not base_path:
            return

        firm_folder = p_dict["profil_name"].replace(" ", "_")
        firm_dir = os.path.join(base_path, firm_folder)
        ausw_dir = os.path.join(firm_dir, "aausw")
        are_dir = os.path.join(firm_dir, "are")
        reneu_dir = os.path.join(firm_dir, "reneu")
        rebearb_dir = os.path.join(firm_dir, "rebearb")
        rchn_dir = os.path.join(firm_dir, "rchn")
        einj_dir = os.path.join(firm_dir, "eausw")

        already_exists = os.path.exists(firm_dir) and os.path.exists(os.path.join(firm_dir, "firma.csv"))

        os.makedirs(ausw_dir, exist_ok=True)
        os.makedirs(are_dir, exist_ok=True)
        for _d in (reneu_dir, rebearb_dir, rchn_dir, einj_dir):
            os.makedirs(_d, exist_ok=True)

        p_dict["auswertungen_ordner"] = ausw_dir
        p_dict["ausgabe_ordner"] = are_dir
        p_dict["eingangsordner"] = reneu_dir
        p_dict["bearbeitete_eingangsrechnungen_ordner"] = rebearb_dir
        p_dict["eingangsrechnungen_ordner"] = rchn_dir
        p_dict["eingangsjournal_ordner"] = einj_dir

        dateien = [
            "firma.csv",
            "rechnung.csv",
            "briefbogen.pdf",
            "zusatz.csv",
            "gruss.csv",
            "vor_gruss.csv",
            "header.csv",
            "einleitung.csv",
            "kunden.csv",
            "produkte.csv",
        ]
        for datei in dateien:
            key_name = datei.replace(".", "_")
            p_dict[key_name] = os.path.join(firm_dir, datei)
        override_keys = [
            "ausgabe_ordner",
            "auswertungen_ordner",
            "firma_csv",
            "briefbogen_pdf",
            "zusatz_csv",
            "gruss_csv",
            "vor_gruss_csv",
            "header_csv",
            "einleitung_csv",
        ]
        for key in override_keys:
            cli_val = self.config.get(f"cli_override_{key}")
            if cli_val:
                p_dict[key] = cli_val

        if already_exists:
            if show_message:
                self.show_info(
                    "Netzwerk-Daten gefunden",
                    f"Es wurden bestehende Daten für '{p_dict['profil_name']}' gefunden und erfolgreich verknüpft!",
                )
        else:
            from crud import create_csv_if_missing

            create_csv_if_missing(
                p_dict["firma_csv"],
                "FirmaName;Strasse;Absenderzeile;PLZ;Ort;Land;UStId;Steuernummer;BankName;IBAN;BIC;Kontoinhaber;Email;Telefon",
            )
            create_csv_if_missing(
                p_dict["rechnung_csv"],
                "Rechnungsnummer;Rechnungsdatum;Faelligkeitsdatum;KundeName;KundeStrasse;KundePLZ;KundeOrt;KundeLand;KundeEmail;KundeEndpoint;KundeEndpointScheme;KundeNr;Aktenzeichen;KundeAktenzeichen;LeistungszeitraumKopf;Ratenzahlung;PosNr;Menge;Einheit;Bezeichnung;EinzelpreisNetto;Steuersatz;Zusatztext;LeistungszeitraumPos",
            )
            create_csv_if_missing(
                p_dict["kunden_csv"],
                "Name;Strasse;PLZ_Ort;Land;KundeNr;UStId;Aktenzeichen;KundeAktenzeichen;Endpoint;EndpointScheme",
            )
            create_csv_if_missing(p_dict["produkte_csv"], "Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz")
            for f in ["zusatz_csv", "gruss_csv", "vor_gruss_csv", "header_csv", "einleitung_csv"]:
                create_csv_if_missing(p_dict[f], "")

    def on_profile_switch(self, wahl):
        for i, p in enumerate(self.config["profiles"]):
            if p["profil_name"] == wahl:
                base_path = self.config.get("base_data_path")
                if base_path:
                    new_lock = os.path.join(base_path, p["profil_name"].replace(" ", "_"), "erechnung.lock")
                    if os.path.exists(new_lock):
                        self.show_warning(
                            "Firma gesperrt", f"Die Firma '{p['profil_name']}' wird aktuell bearbeitet.\nBitte warten."
                        )
                        self.combo_profile.set(self.p_config["profil_name"])
                        return

                self.unlock_firm()
                self.config["active_profile_index"] = i
                speichere_config(self.config)

                self.setup_firm_folders(self.p_config)
                self.lock_firm(self.p_config, "erechnung.lock")

                if not self.enforce_network_version():
                    return

                self.refresh_all_ui()
                self.show_tab(self.name_manuell, run_change_logic=False)
                break

    def add_profile(self):
        d_name = ctk.CTkInputDialog(text="Name der neuen Firma:", title="Neues Profil")
        self.apply_window_icon(d_name)
        name = d_name.get_input()
        if name:
            new_p = get_default_profile(str(int(time.time()))[-5:])
            new_p["profil_name"] = name
            self.setup_firm_folders(new_p, show_message=True)
            self.config["profiles"].append(new_p)

            self.unlock_firm()
            self.lock_firm(new_p)

            self.config["active_profile_index"] = len(self.config["profiles"]) - 1
            speichere_config(self.config)
            self.build_profile_header()
            self.refresh_all_ui()

            if len(self.config["profiles"]) >= 3 and hasattr(self, "license_mgr"):
                self.license_mgr.record_pro_feature_use("Mehr-Firmen-Betrieb (ab dem 3. Firmenprofil)")

    def rename_profile(self):
        d_name = ctk.CTkInputDialog(text="Neuer Name für das Profil:", title="Profil umbenennen")
        self.apply_window_icon(d_name)
        name = d_name.get_input()
        if name:
            self.p_config["profil_name"] = name
            speichere_config(self.config)
            self.build_profile_header()

    def delete_profile(self):
        if len(self.config["profiles"]) <= 1:
            return self.show_warning("Fehler", "Letztes Profil kann nicht gelöscht werden.")
        d_pwd = ctk.CTkInputDialog(
            text="Bitte geben Sie das Sicherheitspasswort ein, um die Firma zu löschen:", title="Sicherheitsabfrage"
        )
        self.apply_window_icon(d_pwd)
        pwd = d_pwd.get_input()
        if pwd == "63263":
            del self.config["profiles"][self.config["active_profile_index"]]
            self.config["active_profile_index"] = 0
            speichere_config(self.config)
            self.build_profile_header()
            self.refresh_all_ui()
            self.show_info("Gelöscht", "Die Firma wurde entfernt.")
        elif pwd is not None:
            self.show_error("Fehler", "Falsches Passwort!")

    def refresh_all_ui(self):
        from crud import lade_kunden, lade_produkte, lade_textdatei

        self.kunden_liste = lade_kunden(self.p_config.get("kunden_csv", "kunden.csv"))
        self.produkte_liste = lade_produkte(self.p_config.get("produkte_csv", "produkte.csv"))
        self.header_text = lade_textdatei(self.p_config.get("header_csv", ""))
        self.einleitung_text = lade_textdatei(self.p_config.get("einleitung_csv", ""))
        self.vor_gruss_text = lade_textdatei(self.p_config.get("vor_gruss_csv", ""))
        self.gruss_text = lade_textdatei(self.p_config.get("gruss_csv", ""))

        if "text_vorlagen" not in self.p_config or not isinstance(self.p_config["text_vorlagen"], dict):
            self.p_config["text_vorlagen"] = {}
        if "Standard" not in self.p_config["text_vorlagen"]:
            self.p_config["text_vorlagen"]["Standard"] = {
                "header": self.header_text,
                "einleitung": self.einleitung_text,
                "vor_gruss": self.vor_gruss_text,
                "gruss": self.gruss_text,
                "zahlungsbedingungen": self.p_config.get("zahlungsbedingungen_default", ""),
                "rechnungsvermerk": self.p_config.get("rechnungsvermerk_default", ""),
            }
        self.aktive_text_vorlage = self.p_config.get("aktive_text_vorlage", "Standard")
        if self.aktive_text_vorlage not in self.p_config["text_vorlagen"]:
            self.aktive_text_vorlage = "Standard"
            self.p_config["aktive_text_vorlage"] = "Standard"

        self.positionen_liste = []
        self.zusatz_dict = {}
        self.has_unsaved_changes = False

        reiter_liste = [
            self.tab_manuell,
            self.tab_erfassen,
            self.tab_ausgang,
            self.tab_eingang,
            self.tab_settings,
            self.tab_hilfe,
        ]
        for tab in reiter_liste:
            for w in tab.winfo_children():
                w.destroy()

        for key in self.loaded_tabs:
            self.loaded_tabs[key] = False

        self.build_manuell_tab()
        self.loaded_tabs[self.name_manuell] = True

        heute = datetime.now()
        tage = (
            int(self.p_config.get("faelligkeit_tage", "29"))
            if str(self.p_config.get("faelligkeit_tage", "29")).isdigit()
            else 29
        )

        self.entry_r_datum.delete(0, "end")
        self.entry_r_datum.insert(0, heute.strftime("%Y-%m-%d"))

        self.entry_f_datum.delete(0, "end")
        self.entry_f_datum.insert(0, (heute + timedelta(days=tage)).strftime("%Y-%m-%d"))

        self.entry_r_nr.delete(0, "end")
        self.entry_r_nr.insert(0, berechne_naechste_rechnungsnummer(self.p_config.get("letzte_rechnungsnummer", "")))

        if self.p_config.get("default_lz_heute", False) and hasattr(self, "entry_lz_kopf"):
            self.entry_lz_kopf.delete(0, "end")
            self.entry_lz_kopf.insert(0, heute.strftime("%Y-%m-%d"))

        if self.p_config.get("default_ihr_zeichen_dash", False) and hasattr(self, "entry_k_az"):
            self.entry_k_az.delete(0, "end")
            self.entry_k_az.insert(0, "-")

        if hasattr(self, "check_live_validation"):
            self.check_live_validation()

    def on_closing(self, skip_warning=False):
        if not skip_warning:
            if getattr(self, "start_in_edit", False):
                antwort = self.ask_yes_no(
                    "Vorgang abbrechen?",
                    "Das Programm wurde von einer externen Anwendung zur Rechnungserstellung aufgerufen.\n\n"
                    "Möglicherweise hat das aufrufende Programm bereits eine Rechnungsnummer reserviert, aber es wurde noch keine finale Rechnung generiert.\n\n"
                    "Möchten Sie wirklich abbrechen und das Fenster schließen?",
                )
                if not antwort:
                    return
            elif hasattr(self, "positionen_liste") and len(self.positionen_liste) > 0:
                antwort = self.ask_yes_no(
                    "Programm beenden?",
                    "Es befinden sich aktuell Rechnungspositionen in der Bearbeitungsmaske.\n\n"
                    "Nicht gespeicherte Daten gehen beim Beenden unwiderruflich verloren.\n\n"
                    "Möchten Sie das Programm wirklich schließen?",
                )
                if not antwort:
                    return

        self.update_idletasks()

        current_state = self.state()
        if current_state == "zoomed":
            self.config["window_state"] = "zoomed"
        else:
            self.config["window_state"] = "normal"
            if current_state != "iconic":
                w = self.winfo_width()
                h = self.winfo_height()
                x = self.winfo_x()
                y = self.winfo_y()
                if w > 100 and h > 100:
                    self.config["window_geometry"] = f"{w}x{h}+{x}+{y}"

        try:
            speichere_config(self.config)
        except Exception:
            pass

        try:
            self.unlock_firm()
        except Exception:
            pass

        self.destroy()
        sys.exit(0)

    def center_window(self, dialog, width, height):
        self.center_on_target(dialog, self, width, height)

    def handle_plus_key(self, event):
        if self.active_tab_name == self.name_manuell:
            widget = self.focus_get()
            if widget and widget.winfo_class() in ("Entry", "Text"):
                return
            self.open_pos_popup()

    def create_button(self, parent, text, command, **kwargs):
        btn = ctk.CTkButton(parent, text=text, command=command, **kwargs)
        btn.bind("<Return>", lambda e: command())
        btn.bind("<space>", lambda e: command())
        return btn

    def create_input(self, parent, label_text, is_combo=False, combo_values=None, command=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
        entry = (
            ctk.CTkComboBox(frame, values=combo_values or [], command=command)
            if is_combo
            else ctk.CTkEntry(frame)
        )
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        return entry

    def create_input_with_button(self, parent, label_text, btn_text, btn_cmd):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label_text, width=120, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame)
        entry.pack(side="left", fill="x", expand=True, padx=(10, 5))
        self.create_button(frame, text=btn_text, width=40, command=lambda: btn_cmd(entry)).pack(side="right")
        return entry
