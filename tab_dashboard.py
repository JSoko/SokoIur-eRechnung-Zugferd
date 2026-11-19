"""
tab_dashboard.py
----------------
Visuelles Dashboard (Matplotlib) für Umsatz, Kunden und Steuern.
"""
import os
import csv
from datetime import datetime
from collections import defaultdict
import customtkinter as ctk
import tkinter.messagebox as messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from crud import lade_rechnungen
from utils import safe_float, f_curr
class TabDashboardMixin:
    def open_dashboard_popup(self):
        # 1. Popup-Fenster erstellen
        self.dash_popup = ctk.CTkToplevel(self)
        self.dash_popup.title("📈 Visuelles Auswertungs-Dashboard")
        self.center_window(self.dash_popup, 1000, 700)
        self.dash_popup.transient(self)
        self.dash_popup.grab_set()
        
        # Oben: Titel & Jahresauswahl-Dropdown
        f_top = ctk.CTkFrame(self.dash_popup, fg_color="transparent")
        f_top.pack(fill="x", pady=15, padx=20)
        
        ctk.CTkLabel(f_top, text="📊 Business Dashboard", font=("Helvetica", 20, "bold")).pack(side="left")
        
        # Rechte Seite des Top-Frames: Jahresauswahl
        f_jahr_wahl = ctk.CTkFrame(f_top, fg_color="transparent")
        f_jahr_wahl.pack(side="right")
        
        ctk.CTkLabel(f_jahr_wahl, text="Geschäftsjahr:").pack(side="left", padx=(0, 8))
        
        # Verfügbare Jahre ermitteln
        verfuegbare_jahre = self.get_available_years() if hasattr(self, 'get_available_years') else [str(datetime.now().year)]
        
        self.dash_jahr_var = ctk.StringVar(value=self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year)))
        
        self.combo_dash_jahr = ctk.CTkComboBox(
            f_jahr_wahl, 
            values=verfuegbare_jahre, 
            variable=self.dash_jahr_var, 
            width=110,
            command=self.on_dashboard_jahr_wechsel
        )
        self.combo_dash_jahr.pack(side="left")

        # Container für die Diagramme (wird beim Jahrwechsel dynamisch neu gezeichnet)
        self.dash_canvas_frame = ctk.CTkFrame(self.dash_popup, fg_color="transparent")
        self.dash_canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initiales Zeichnen der Charts
        self.refresh_dashboard_charts()
        
        # Unten: Schließen Button
        ctk.CTkButton(self.dash_popup, text="Schließen", command=self.dash_popup.destroy, width=150, fg_color="#555", hover_color="#777").pack(pady=10)

    def on_dashboard_jahr_wechsel(self, neues_jahr):
        """Wird aufgerufen, wenn im Dashboard ein anderes Jahr ausgewählt wird."""
        self.p_config["aktuelles_rechnungsjahr"] = neues_jahr
        self.refresh_dashboard_charts()

    def refresh_dashboard_charts(self):
        """Erstellt oder aktualisiert die Matplotlib-Charts im Canvas-Frame."""
        for widget in self.dash_canvas_frame.winfo_children():
            widget.destroy()

        jahr = self.dash_jahr_var.get()

        # Daten für das gewählte Jahr sammeln
        try:
            jahres_daten = self.gather_dashboard_data()
        except Exception as e:
            ctk.CTkLabel(self.dash_canvas_frame, text=f"Fehler beim Laden der Daten:\n{e}", text_color="red").pack(pady=50)
            return

        # Matplotlib Figure erstellen
        fig = Figure(figsize=(10, 6), dpi=100, facecolor='#2b2b2b')
        fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.1, wspace=0.3, hspace=0.4)

        text_color = "white"
        
        # --- CHART 1: Umsatzverlauf pro Monat ---
        ax1 = fig.add_subplot(2, 1, 1)
        ax1.set_facecolor('#2b2b2b')
        ax1.tick_params(colors=text_color)
        for spine in ax1.spines.values(): spine.set_color('#555555')
        
        monate = sorted(jahres_daten['umsatz_monat'].keys())
        umsaetze = [jahres_daten['umsatz_monat'][m] for m in monate]
        
        ax1.bar(monate, umsaetze, color='#1f538d', alpha=0.8)
        ax1.plot(monate, umsaetze, color='#4aa3df', marker='o', linewidth=2)
        ax1.set_title(f"Netto-Umsatzverlauf {jahr}", color=text_color, pad=10)
        ax1.grid(True, axis='y', linestyle='--', alpha=0.3, color='gray')

        # --- CHART 2: Top 5 Kunden (mit Namen direkt in den Balken) ---
        ax2 = fig.add_subplot(2, 2, 3)
        ax2.set_facecolor('#2b2b2b')
        ax2.tick_params(colors=text_color, labelleft=False)
        for spine in ax2.spines.values(): spine.set_color('#555555')
        
        top_kunden = sorted(jahres_daten['kunden_umsatz'].items(), key=lambda x: x[1], reverse=True)[:5]
        top_kunden.reverse()  # Umgekehrte Reihenfolge, damit der größte oben ist
        
        k_namen = [k[0] for k in top_kunden]
        k_werte = [k[1] for k in top_kunden]
        
        bars = ax2.barh(range(len(k_namen)), k_werte, color='#2c8c68')
        ax2.set_title(f"Top 5 Kunden {jahr} (Netto)", color=text_color, pad=10)

        if k_werte:
            max_w = max(k_werte) if max(k_werte) > 0 else 1
            for i, bar in enumerate(bars):
                width = bar.get_width()
                name = k_namen[i]
                ax2.text(
                    max_w * 0.03, 
                    bar.get_y() + bar.get_height() / 2, 
                    f"{name} ({f_curr(width)})", 
                    color='white', 
                    va='center', 
                    ha='left', 
                    fontweight='bold',
                    fontsize=9
                )

        # --- CHART 3: Umsatzsteuer vs. Vorsteuer (Vergleich mit Wert-Labels) ---
        ax3 = fig.add_subplot(2, 2, 4)
        ax3.set_facecolor('#2b2b2b')
        ax3.tick_params(colors=text_color)
        for spine in ax3.spines.values(): spine.set_color('#555555')
        
        labels = ['Eingenommene\nUSt.', 'Gezahlte\nVorsteuer', 'Zahllast\n(Finanzamt)']
        ust = jahres_daten['ust_eingenommen']
        vst = jahres_daten['vst_gezahlt']
        zahllast = ust - vst
        werte = [ust, vst, zahllast]
        farben = ['#1f538d', '#d9534f', '#f0ad4e']
        
        bars3 = ax3.bar(labels, werte, color=farben)
        ax3.set_title(f"Steuer-Übersicht {jahr}", color=text_color, pad=10)
        ax3.axhline(0, color='gray', linewidth=1)

        # Exakte Beträge direkt ÜBER/UNTER den Säulen einblenden
        for bar in bars3:
            yval = bar.get_height()
            # Position anpassen: Bei positiven Werten knapp darüber, bei negativen darunter
            offset = max(abs(max(werte) * 0.03), 10) if yval >= 0 else -max(abs(min(werte) * 0.03), 10)
            va_align = 'bottom' if yval >= 0 else 'top'
            
            ax3.text(
                bar.get_x() + bar.get_width() / 2, 
                yval + offset, 
                f"{f_curr(yval)}", 
                color='white', 
                ha='center', 
                va=va_align, 
                fontsize=9,
                fontweight='bold'
            )

        # Canvas einbetten
        canvas = FigureCanvasTkAgg(fig, master=self.dash_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def gather_dashboard_data(self):
        """Sammelt aggregierte Daten aus den Monats-Journalen und Eingangsrechnungen."""
        jahr = self.dash_jahr_var.get() if hasattr(self, 'dash_jahr_var') else self.p_config.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        ausw_ordner = self.p_config.get("auswertungen_ordner", "aausw")
        
        daten = {
            'umsatz_monat': {f"{jahr}-{str(m).zfill(2)}": 0.0 for m in range(1, 13)},
            'kunden_umsatz': defaultdict(float),
            'ust_eingenommen': 0.0,
            'vst_gezahlt': 0.0
        }
        
        # 1. Alle Monats-Journale (reYYYYMM.csv) für das gewählte Jahr auslesen
        such_muster = [f"re{jahr}{m:02d}.csv" for m in range(1, 13)]
        gefundene_rechnungen = []
        
        for datei in such_muster:
            pfad = os.path.join(ausw_ordner, jahr, datei) if os.path.exists(os.path.join(ausw_ordner, jahr, datei)) else os.path.join(ausw_ordner, datei)
            if os.path.exists(pfad):
                try:
                    with open(pfad, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f, delimiter=';')
                        for row in reader:
                            gefundene_rechnungen.append(row)
                except Exception:
                    pass

        # Daten aus den Journalen aggregieren
        for r in gefundene_rechnungen:
            datum_str = r.get('Datum', '')
            kunde = r.get('Empfaenger', 'Unbekannt')
            
            netto = safe_float(r.get('Netto', 0))
            m19 = safe_float(r.get('MwSt_19', 0))
            m7 = safe_float(r.get('MwSt_7', 0))
            m0 = safe_float(r.get('MwSt_0', 0))
            ust_summe = m19 + m7 + m0
            
            if datum_str.startswith(jahr) or (len(datum_str) >= 10 and datum_str[6:10] == jahr):
                if len(datum_str) == 10 and datum_str[2] == '.' and datum_str[5] == '.':
                    monat_key = f"{datum_str[6:10]}-{datum_str[3:5]}"
                else:
                    monat_key = f"{jahr}-01"
                
                if monat_key in daten['umsatz_monat']:
                    daten['umsatz_monat'][monat_key] += netto
                daten['kunden_umsatz'][kunde] += netto
                daten['ust_eingenommen'] += ust_summe

        # 2. Eingangsrechnungen (Vorsteuer) auslesen
        einj_dir = self.p_config.get("eingangsjournal_ordner", "")
        jahr_dir = os.path.join(einj_dir, jahr)
        
        if os.path.exists(jahr_dir):
            for filename in os.listdir(jahr_dir):
                if filename.endswith(".csv"):
                    csv_pfad = os.path.join(jahr_dir, filename)
                    try:
                        with open(csv_pfad, "r", encoding="utf-8-sig") as f:
                            reader = csv.DictReader(f, delimiter=";")
                            for row in reader:
                                m19 = safe_float(str(row.get('MwSt_19', '0')).replace(',', '.'))
                                m7 = safe_float(str(row.get('MwSt_7', '0')).replace(',', '.'))
                                m_sonst = safe_float(str(row.get('MwSt_sonstige', '0')).replace(',', '.'))
                                daten['vst_gezahlt'] += (m19 + m7 + m_sonst)
                    except Exception:
                        pass

        return daten