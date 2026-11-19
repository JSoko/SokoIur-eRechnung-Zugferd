"""
updater.py
----------
Logik für die automatische Update-Prüfung und Installation (P2P & Online).
"""
import os
import sys
import shutil
import threading
import subprocess
import tempfile
import ctypes
import urllib.request
import ssl
import customtkinter as ctk
import tkinter.messagebox as messagebox

from config import speichere_config

class UpdaterMixin:
    def enforce_network_version(self):
        def _check_version():
            base_path = self.config.get("base_data_path", "")
            if not base_path or not os.path.exists(base_path): return True
                    
            version_file = os.path.join(base_path, "erech.txt")
            stored_version = ""
            if os.path.exists(version_file):
                try:
                    with open(version_file, "r") as f:
                        stored_version = f.read().strip()
                except: pass
                
            # NEU: Wenn wir im Entwicklermodus sind, prüfen wir nichts und schreiben nichts ins Netzwerk!
            if self.current_version == "Entwickler-Version":
                return True
                
            
            def parse_v(v):
                if not v: return 0.0
                try:
                    p = v.split('.')
                    return float(p[0] + '.' + ''.join(p[1:]))
                except ValueError:
                    # Falls noch "Entwickler-Version" in der Datei steht, werten wir das als Version 0.0
                    return 0.0
                
            c_v = parse_v(self.current_version)
            s_v = parse_v(stored_version)
            
            # --- NEU: SokoIur_eRechnung_Update.exe ersetzen, wenn die gestartete exe neuer (jünger) ist ---
            if getattr(sys, 'frozen', False):
                try:
                    import shutil
                    update_exe_path = os.path.join(base_path, "SokoIur_eRechnung_Update.exe")
                    current_exe = os.path.abspath(sys.executable)
                    
                    if current_exe.lower() != update_exe_path.lower():
                        should_copy = False
                        if not os.path.exists(update_exe_path):
                            should_copy = True
                        else:
                            # Vergleicht das Änderungsdatum (Modification Time)
                            if os.path.getmtime(current_exe) > os.path.getmtime(update_exe_path):
                                should_copy = True
                                
                        if should_copy:
                            shutil.copy2(current_exe, update_exe_path)
                except Exception as e:
                    print(f"Fehler beim Aktualisieren der Update.exe im Netzwerk: {e}")
            
            if c_v < s_v:
                self.withdraw()  # Hauptfenster verstecken, um Datenzugriff zu blockieren
                messagebox.showerror("Versionskonflikt", f"Die Daten wurden mit einer neueren Programmversion ({stored_version}) bearbeitet.\n\nUm Datenverlust im Netzwerk zu vermeiden, ist ein Update zwingend erforderlich!")
                self.check_for_updates(force=True)
                return False
            elif c_v > s_v:
                try:
                    # Überschreibt die fehlerhafte "Entwickler-Version" im Netzwerk wieder mit der echten Versionsnummer
                    with open(version_file, "w") as f:
                        f.write(self.current_version)
                except: pass
            return True
        import threading
        threading.Thread(target=_check_version, daemon=True).start()
        return True # Sofort True zurückgeben, damit die GUI weiterlädt
        
        
        

    def check_for_updates(self, force=False):
        # 1. Zuerst prüfen, ob im lokalen Netzwerklaufwerk bereits ein Update liegt
        base_path = self.config.get("base_data_path", "")
        network_version = "0.0"
        network_exe = ""
        
        def parse_v(v):
            if not v: return 0.0
            try:
                p = v.split('.')
                return float(p[0] + '.' + ''.join(p[1:]))
            except ValueError:
                return 0.0

        if base_path and os.path.exists(base_path):
            v_file = os.path.join(base_path, "erech.txt")
            exe_file = os.path.join(base_path, "SokoIur_eRechnung_Update.exe")
            if os.path.exists(v_file) and os.path.exists(exe_file):
                try:
                    with open(v_file, "r") as f:
                        network_version = f.read().strip()
                    network_exe = exe_file
                except: pass

        c_v = parse_v(self.current_version)
        n_v = parse_v(network_version)

        # Wenn im Netzwerk eine neuere Version liegt, diese sofort verwenden (P2P)!
        if n_v > c_v and network_exe:
            self.prompt_update(network_version, "LOCAL", force)
            return

        # 2. Falls kein lokales Update, fragen ob online gesucht werden soll
        if not force:
            msg = "Auf dem Netzwerklaufwerk liegt kein neueres Update vor.\nMöchten Sie jetzt online (erech.6078.de) nach einer neuen Version suchen?"
            if not messagebox.askyesno("Online suchen?", msg): 
                return
        else:
            if not messagebox.askyesno("Update erforderlich", "Möchten Sie jetzt zum Update-Server verbinden, um das zwingend erforderliche Update zu laden?\n(Bei 'Nein' wird das Programm sicherheitshalber beendet)"):
                self.do_update_exit()
                return
                
        if hasattr(self, 'btn_update'): self.btn_update.configure(text="⏳ Suche läuft...", state="disabled")
        if hasattr(self, 'btn_footer_update'): self.btn_footer_update.configure(text="⏳ Suche...", state="disabled")
        
        def _check():
            try:
                import ssl
                import urllib.request
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    "https://erech.6078.de/erech.txt", 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Cache-Control': 'no-cache'}
                )
                with urllib.request.urlopen(req, context=ctx) as response: 
                    latest_version = response.read().decode('utf-8').strip()
                
                if not latest_version:
                    self.after(0, lambda: [
                        (self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal") if hasattr(self, 'btn_update') else None),
                        (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                        messagebox.showerror("Fehler", "Keine gültigen Versionsdaten auf dem Server gefunden."),
                        self.do_update_exit() if force else None
                    ])
                    return
                
                download_url = "https://erech.6078.de/SokoIur_eRechnung.exe"
                
                is_newer = False
                try:
                    is_newer = parse_v(latest_version) > parse_v(self.current_version)
                except: 
                    is_newer = latest_version > self.current_version
                
                if is_newer: 
                    self.after(0, lambda: self.prompt_update(latest_version, download_url, force))
                else:
                    self.after(0, lambda: [
                        (self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal") if hasattr(self, 'btn_update') else None),
                        (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                        messagebox.showinfo("Update-Prüfung", f"Sie nutzen bereits die aktuellste Version!\n\nIhre: {self.current_version}\nOnline: {latest_version}") if not force else messagebox.showerror("Fehler", "Online ist keine neuere Version verfügbar. Abbruch!"),
                        self.do_update_exit() if force else None
                    ])
            except Exception as e:
                self.after(0, lambda: [
                    (self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal") if hasattr(self, 'btn_update') else None),
                    (self.btn_footer_update.configure(text="Update?", state="normal") if hasattr(self, 'btn_footer_update') else None),
                    messagebox.showerror("Fehler", f"Fehler bei der Update-Prüfung:\n{str(e)}"),
                    self.do_update_exit() if force else None
                ])
        threading.Thread(target=_check, daemon=True).start()
    
    def prompt_update(self, latest_version, download_url, force=False):
        if hasattr(self, 'btn_update'): self.btn_update.configure(text="🔄 Auf Updates prüfen", state="normal")
        if hasattr(self, 'btn_footer_update'): self.btn_footer_update.configure(text="Update?", state="normal")
        
        source = "im lokalen Netzwerk" if download_url == "LOCAL" else "online"
        
        msg = f"Version {latest_version} ist {source} verfügbar!\nMöchten Sie diese jetzt installieren?"
        if force: msg = f"Zwingendes Update auf Version {latest_version} {source} gefunden!\nJetzt installieren und neu starten?"
        
        if messagebox.askyesno("Update verfügbar!", msg):
            self.download_and_install_update(download_url)
        elif force:
            self.do_update_exit()

    def download_and_install_update(self, download_url):
        dl_win = ctk.CTkToplevel(self); dl_win.title("Update")
        self.center_window(dl_win, 300, 150); dl_win.transient(self); dl_win.grab_set()
        
        msg_text = "Lade Update aus dem Netzwerk...\nBitte warten." if download_url == "LOCAL" else "Lade Update online herunter...\nBitte warten."
        ctk.CTkLabel(dl_win, text=msg_text, font=("Helvetica", 14)).pack(expand=True); self.update()
        
        def _download():
            try:
                import ssl
                import shutil
                import os
                import subprocess
                import urllib.request
                import tempfile
                import ctypes
                
                # 1. Absolute Pfade des laufenden Programms ermitteln
                current_exe = os.path.abspath(sys.executable)
                exe_dir = os.path.dirname(current_exe)
                
                # 2. Ziel im Netzwerk ermitteln
                base_path = self.config.get("base_data_path", "")
                if base_path and os.path.exists(base_path):
                    dl_target = os.path.join(base_path, "SokoIur_eRechnung_Update.exe")
                else:
                    dl_target = os.path.join(exe_dir, "SokoIur_eRechnung_Update.exe")
                
                # 3. Nur online herunterladen, wenn es kein lokales P2P-Update ist
                if download_url != "LOCAL":
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    
                    req_dl = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                    with urllib.request.urlopen(req_dl, context=ctx) as response, open(dl_target, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                
                if not getattr(sys, 'frozen', False):
                    self.after(0, lambda: [dl_win.destroy(), messagebox.showinfo("Info", f"Update im Skript-Modus bereit unter:\n{dl_target}")])
                    return
                
                # --- AB HIER: ADMIN-RECHTE UND BATCH-CODE ---
                bat_path = os.path.join(tempfile.gettempdir(), "sokoiur_update.bat")
                
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write('@echo off\n')
                    f.write(':loop\n')
                    f.write('timeout /t 1 /nobreak > NUL\n')
                    f.write(f'copy /Y "{dl_target}" "{current_exe}" > NUL\n')
                    f.write('if errorlevel 1 goto loop\n')
                    f.write(f'start "" "{current_exe}"\n')
                    f.write('del "%~f0"\n')
                
                ctypes.windll.shell32.ShellExecuteW(None, "runas", bat_path, None, None, 0)
                
                self.after(0, self.do_update_exit)
                                
            except Exception as e:
                self.after(0, lambda: [dl_win.destroy(), messagebox.showerror("Fehler", f"Update fehlgeschlagen:\n{str(e)}")])
                
        threading.Thread(target=_download, daemon=True).start()

    def do_update_exit(self):
        # --- NEU: Lock-Datei vor dem Update-Neustart zwingend entfernen ---
        try:
            if hasattr(self, 'unlock_firm'):
                self.unlock_firm()
        except Exception as e:
            print(f"Fehler beim Entfernen der Lock-Datei während des Updates: {e}")
                
        self.destroy()
        import sys
        sys.exit(0)
    

