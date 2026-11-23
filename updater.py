"""
updater.py
----------
Logik für die automatische Update-Prüfung und Installation (P2P/Netzwerk & Online)
über das Setup-Installationspaket.
"""
import os
import sys
import shutil
import threading
import subprocess
import tempfile
import urllib.request
import ssl
import tkinter.messagebox as messagebox
import customtkinter as ctk

from config import speichere_config


class UpdaterMixin:
    def _parse_version(self, v):
        if not v:
            return 0.0
        try:
            p = str(v).strip().split(".")
            return float(p[0] + "." + "".join(p[1:]))
        except ValueError:
            return 0.0

    def enforce_network_version(self):
        def _check_version():
            base_path = self.config.get("base_data_path", "")
            if not base_path or not os.path.exists(base_path):
                return True

            version_file = os.path.join(base_path, "erech.txt")
            stored_version = ""
            if os.path.exists(version_file):
                try:
                    with open(version_file, "r", encoding="utf-8") as f:
                        stored_version = f.read().strip()
                except Exception:
                    pass

            if self.current_version == "Entwickler-Version":
                return True

            c_v = self._parse_version(self.current_version)
            s_v = self._parse_version(stored_version)

            if c_v < s_v:
                self.after(0, self.withdraw)
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Versionskonflikt",
                        f"Die Daten wurden mit einer neueren Programmversion ({stored_version}) bearbeitet.\n\n"
                        "Um Datenverlust im Netzwerk zu vermeiden, ist ein Update zwingend erforderlich!",
                    ),
                )
                self.after(0, lambda: self.check_for_updates(force=True))
                return False
            elif c_v > s_v:
                try:
                    with open(version_file, "w", encoding="utf-8") as f:
                        f.write(self.current_version)
                except Exception:
                    pass
            return True

        threading.Thread(target=_check_version, daemon=True).start()
        return True

    def check_for_updates(self, force=False):
        base_path = self.config.get("base_data_path", "")
        network_version = "0.0"
        network_setup = ""

        if base_path and os.path.exists(base_path):
            v_file = os.path.join(base_path, "erech.txt")
            setup_file = os.path.join(base_path, "SokoIur_eRechnung_Update_Setup.exe")
            if os.path.exists(v_file) and os.path.exists(setup_file):
                try:
                    with open(v_file, "r", encoding="utf-8") as f:
                        network_version = f.read().strip()
                    network_setup = setup_file
                except Exception:
                    pass

        c_v = self._parse_version(self.current_version)
        n_v = self._parse_version(network_version)

        if n_v > c_v and network_setup:
            self.prompt_update(network_version, "LOCAL", force, local_setup_path=network_setup)
            return

        if not force:
            msg = (
                "Auf dem Netzwerklaufwerk liegt kein neueres Update vor.\n"
                "Möchten Sie jetzt online (erech.6078.de) nach einer neuen Version suchen?"
            )
            if not messagebox.askyesno("Online suchen?", msg):
                return
        else:
            if not messagebox.askyesno(
                "Update erforderlich",
                "Möchten Sie jetzt zum Update-Server verbinden, um das zwingend erforderliche Update zu laden?\n"
                "(Bei 'Nein' wird das Programm sicherheitshalber beendet)",
            ):
                self.do_update_exit()
                return

        if hasattr(self, "btn_update"):
            self.btn_update.configure(text="⏳ Suche läuft...", state="disabled")
        if hasattr(self, "btn_footer_update"):
            self.btn_footer_update.configure(text="⏳ Suche...", state="disabled")

        def _check():
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                req = urllib.request.Request(
                    "https://erech.6078.de/erech.txt",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Cache-Control": "no-cache",
                    },
                )
                with urllib.request.urlopen(req, context=ctx) as response:
                    latest_version = response.read().decode("utf-8").strip()

                if not latest_version:
                    self.after(
                        0,
                        lambda: [
                            self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal")
                            if hasattr(self, "btn_update")
                            else None,
                            self.btn_footer_update.configure(text="Update?", state="normal")
                            if hasattr(self, "btn_footer_update")
                            else None,
                            messagebox.showerror("Fehler", "Keine gültigen Versionsdaten auf dem Server gefunden."),
                            self.do_update_exit() if force else None,
                        ],
                    )
                    return

                download_url = "https://erech.6078.de/SokoIur_eRechnung_Update_Setup.exe"
                is_newer = self._parse_version(latest_version) > self._parse_version(self.current_version)

                if is_newer:
                    self.after(
                        0,
                        lambda: self.prompt_update(
                            latest_version,
                            download_url,
                            force,
                            target_version=latest_version,
                        ),
                    )
                else:
                    self.after(
                        0,
                        lambda: [
                            self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal")
                            if hasattr(self, "btn_update")
                            else None,
                            self.btn_footer_update.configure(text="Update?", state="normal")
                            if hasattr(self, "btn_footer_update")
                            else None,
                            messagebox.showinfo(
                                "Update-Prüfung",
                                f"Sie nutzen bereits die aktuellste Version!\n\nIhre: {self.current_version}\nOnline: {latest_version}",
                            )
                            if not force
                            else messagebox.showerror("Fehler", "Online ist keine neuere Version verfügbar. Abbruch!"),
                            self.do_update_exit() if force else None,
                        ],
                    )
            except Exception as e:
                self.after(
                    0,
                    lambda: [
                        self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal")
                        if hasattr(self, "btn_update")
                        else None,
                        self.btn_footer_update.configure(text="Update?", state="normal")
                        if hasattr(self, "btn_footer_update")
                        else None,
                        messagebox.showerror("Fehler", f"Fehler bei der Update-Prüfung:\n{str(e)}"),
                        self.do_update_exit() if force else None,
                    ],
                )

        threading.Thread(target=_check, daemon=True).start()

    def prompt_update(self, latest_version, download_url, force=False, local_setup_path="", target_version=""):
        if hasattr(self, "btn_update"):
            self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal")
        if hasattr(self, "btn_footer_update"):
            self.btn_footer_update.configure(text="Update?", state="normal")

        source = "im lokalen Netzwerk" if download_url == "LOCAL" else "online"
        msg = f"Version {latest_version} ist {source} verfügbar!\nMöchten Sie das Installationspaket jetzt ausführen?"
        if force:
            msg = f"Zwingendes Update auf Version {latest_version} {source} gefunden!\nJetzt installieren und neu starten?"

        if messagebox.askyesno("Update verfügbar!", msg):
            self.download_and_install_update(
                download_url,
                local_setup_path=local_setup_path,
                target_version=target_version or latest_version,
            )
        elif force:
            self.do_update_exit()

    def download_and_install_update(self, download_url, local_setup_path="", target_version=""):
        dl_win = ctk.CTkToplevel(self)
        dl_win.title("Update")
        self.center_window(dl_win, 340, 150)
        dl_win.transient(self)
        dl_win.grab_set()

        msg_text = (
            "Starte Installationspaket aus dem Netzwerk...\nBitte warten."
            if download_url == "LOCAL"
            else "Lade Installationspaket online herunter\nund speichere im Netzwerk...\nBitte warten."
        )
        ctk.CTkLabel(dl_win, text=msg_text, font=("Helvetica", 13)).pack(expand=True)
        self.update()

        def _show_err_and_close(title, text):
            if dl_win.winfo_exists():
                dl_win.destroy()
            messagebox.showerror(title, text)

        def _download():
            temp_update_dir = os.path.join(tempfile.gettempdir(), "SokoIur_Update")
            log_file = os.path.join(temp_update_dir, "setup_update.log")
            try:
                os.makedirs(temp_update_dir, exist_ok=True)
                if os.path.exists(log_file):
                    try:
                        os.remove(log_file)
                    except Exception:
                        pass

                base_path = self.config.get("base_data_path", "")
                has_network = bool(base_path and os.path.isdir(base_path))
                network_setup_path = os.path.join(base_path, "SokoIur_eRechnung_Update_Setup.exe") if has_network else ""
                network_version_path = os.path.join(base_path, "erech.txt") if has_network else ""

                if download_url == "LOCAL":
                    src_path = local_setup_path or network_setup_path
                    if not src_path or not os.path.isfile(src_path):
                        raise FileNotFoundError(f"Lokales Setup-Paket im Netzwerk nicht gefunden:\n{src_path}")
                    local_exec_setup = os.path.join(temp_update_dir, os.path.basename(src_path))
                    shutil.copy2(src_path, local_exec_setup)
                    setup_target = local_exec_setup
                else:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE

                    req_dl = urllib.request.Request(
                        download_url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                    )

                    if has_network:
                        with urllib.request.urlopen(req_dl, context=ctx) as response, open(network_setup_path, "wb") as out_file:
                            shutil.copyfileobj(response, out_file)
                        if target_version:
                            try:
                                with open(network_version_path, "w", encoding="utf-8") as vf:
                                    vf.write(str(target_version).strip())
                            except Exception:
                                pass
                        local_exec_setup = os.path.join(temp_update_dir, os.path.basename(network_setup_path))
                        shutil.copy2(network_setup_path, local_exec_setup)
                        setup_target = local_exec_setup
                    else:
                        temp_setup = os.path.join(temp_update_dir, "SokoIur_eRechnung_Update_Setup.exe")
                        with urllib.request.urlopen(req_dl, context=ctx) as response, open(temp_setup, "wb") as out_file:
                            shutil.copyfileobj(response, out_file)
                        setup_target = temp_setup

                if not getattr(sys, "frozen", False):
                    self.after(
                        0,
                        lambda: [
                            dl_win.destroy() if dl_win.winfo_exists() else None,
                            messagebox.showinfo("Info", f"Setup-Paket im Skript-Modus bereit unter:\n{setup_target}"),
                        ],
                    )
                    return

                subprocess.Popen([
                    setup_target,
                    "/SILENT",
                    "/CLOSEAPPLICATIONS",
                    "/NORESTART",
                    f"/LOG={log_file}",
                ])

                self.after(0, self.do_update_exit)

            except Exception as e:
                err_detail = f"Update fehlgeschlagen:\n{str(e)}\n\nLogdatei (falls vorhanden): {log_file}"
                self.after(0, lambda msg=err_detail: _show_err_and_close("Fehler", msg))

        threading.Thread(target=_download, daemon=True).start()

    def do_update_exit(self):
        try:
            if hasattr(self, "unlock_firm"):
                self.unlock_firm()
        except Exception as e:
            print(f"Fehler beim Entfernen der Lock-Datei während des Updates: {e}")

        self.destroy()
        sys.exit(0)

    def schedule_background_update_check(self):
        if not self.config.get("background_update_check", False):
            return
        if getattr(self, "_bg_update_started", False):
            return
        self._bg_update_started = True
        threading.Thread(target=self._run_background_update_worker, daemon=True).start()

    def _run_background_update_worker(self):
        import json
        import socket
        from datetime import datetime

        try:
            if not self.config.get("background_update_check", False):
                return
            if self.current_version == "Entwickler-Version":
                return

            base_path = self.config.get("base_data_path", "")
            if not base_path or not os.path.isdir(base_path):
                return

            today_str = datetime.now().strftime("%Y-%m-%d")
            marker_path = os.path.join(base_path, "update_check_state.json")

            # Prüfen, ob heute bereits eine Instanz im Netzwerk den Updateserver abgefragt hat
            if os.path.isfile(marker_path):
                try:
                    with open(marker_path, "r", encoding="utf-8") as f:
                        state = json.load(f)
                    if str(state.get("last_check_date", "")).strip() == today_str:
                        return
                except Exception:
                    pass

            # Heutigen Check im Netzwerk vermerken (atomar), damit andere Arbeitsplätze heute nicht erneut prüfen
            marker_payload = {
                "last_check_date": today_str,
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "checked_by": os.environ.get("COMPUTERNAME", socket.gethostname()),
            }
            fd, tmp_marker = tempfile.mkstemp(dir=base_path, prefix="upd_chk_", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as tf:
                    json.dump(marker_payload, tf, indent=2)
                os.replace(tmp_marker, marker_path)
            except Exception:
                try:
                    if os.path.exists(tmp_marker):
                        os.remove(tmp_marker)
                except Exception:
                    pass

            # Updateserver prüfen
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(
                "https://erech.6078.de/erech.txt",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Cache-Control": "no-cache",
                },
            )
            with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
                latest_version = response.read().decode("utf-8").strip()

            if not latest_version:
                return

            remote_v = self._parse_version(latest_version)
            current_v = self._parse_version(self.current_version)

            network_version_path = os.path.join(base_path, "erech.txt")
            network_setup_path = os.path.join(base_path, "SokoIur_eRechnung_Update_Setup.exe")

            existing_net_v = 0.0
            existing_net_ver_str = ""
            if os.path.isfile(network_version_path):
                try:
                    with open(network_version_path, "r", encoding="utf-8") as vf:
                        existing_net_ver_str = vf.read().strip()
                    existing_net_v = self._parse_version(existing_net_ver_str)
                except Exception:
                    pass

            # Nur wenn auf dem Server eine aktuellere Version als lokal und als im Netzwerk liegt:
            # Setup in den Netzwerkordner laden (ohne Installation im laufenden Betrieb)
            if remote_v > current_v and remote_v > existing_net_v:
                if os.path.isfile(network_setup_path) and existing_net_ver_str:
                    archived_setup = os.path.join(
                        base_path, f"SokoIur_eRechnung_Update_Setup_V{existing_net_ver_str}.exe"
                    )
                    if not os.path.exists(archived_setup):
                        try:
                            shutil.copy2(network_setup_path, archived_setup)
                        except Exception:
                            pass

                download_url = "https://erech.6078.de/SokoIur_eRechnung_Update_Setup.exe"
                req_dl = urllib.request.Request(
                    download_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                )

                fd_dl, tmp_setup = tempfile.mkstemp(dir=base_path, prefix="setup_dl_", suffix=".tmp")
                os.close(fd_dl)
                try:
                    with urllib.request.urlopen(req_dl, timeout=60, context=ctx) as dl_resp, open(tmp_setup, "wb") as out_f:
                        shutil.copyfileobj(dl_resp, out_f)
                    os.replace(tmp_setup, network_setup_path)
                    with open(network_version_path, "w", encoding="utf-8") as vf:
                        vf.write(latest_version)
                finally:
                    if os.path.exists(tmp_setup):
                        try:
                            os.remove(tmp_setup)
                        except Exception:
                            pass
        except Exception:
            pass
