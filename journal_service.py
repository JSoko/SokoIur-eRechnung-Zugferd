"""
journal_service.py
------------------
Fach- und Exportlogik für Ausgangs- und Eingangsjournale (CSV, PDF, DATEV, Bezahlt-Status).
Trennung von Daten-/Exportlogik und CustomTkinter-UI.
"""
import os
import re
import csv
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

from crud import lade_firma, atomic_save_csv
from utils import safe_float, f_curr
from eingangsrechnung import extract_account_number


OUTGOING_JOURNAL_FIELDS = [
    "Rechnungsnummer",
    "Datum",
    "Empfaenger",
    "Netto",
    "MwSt_19",
    "MwSt_7",
    "MwSt_0",
    "Brutto",
    "Bezahlt",
]


def is_invoice_paid(row: dict) -> bool:
    """Prüft anhand des Feldes 'Bezahlt', ob eine Ausgangsrechnung als bezahlt markiert ist."""
    val = str((row or {}).get("Bezahlt", "")).strip().lower()
    return val in ("1", "ja", "yes", "true", "x", "bezahlt") or val.startswith("ja")


def find_outgoing_invoice_pdf(ausgabe_ordner: str, re_nr: str, datum_str: str = "", preferred_years: list = None) -> str:
    """Sucht die zugehörige PDF-Datei einer Ausgangsrechnung im Rechnungsordner (are)."""
    if not ausgabe_ordner or not re_nr:
        return ""

    jahr_from_date = ""
    if len(datum_str) == 10 and datum_str[2] == "." and datum_str[5] == ".":
        jahr_from_date = datum_str[6:10]

    candidate_dirs = []
    for y in ([jahr_from_date] + list(preferred_years or [])):
        if y:
            d = os.path.join(ausgabe_ordner, str(y))
            if os.path.isdir(d) and d not in candidate_dirs:
                candidate_dirs.append(d)

    if os.path.isdir(ausgabe_ordner) and ausgabe_ordner not in candidate_dirs:
        candidate_dirs.append(ausgabe_ordner)

    if os.path.isdir(ausgabe_ordner):
        for sub in sorted(os.listdir(ausgabe_ordner), reverse=True):
            sub_p = os.path.join(ausgabe_ordner, sub)
            if os.path.isdir(sub_p) and sub_p not in candidate_dirs:
                candidate_dirs.append(sub_p)

    filenames = [
        f"Rechnung_{re_nr}.pdf",
        f"Rechnung_{re_nr}_Begleit.pdf",
        f"Rechnung_{re_nr}_Papier.pdf",
    ]
    for folder in candidate_dirs:
        for fname in filenames:
            full_p = os.path.join(folder, fname)
            if os.path.isfile(full_p):
                return full_p
    return ""


def get_available_outgoing_years(ordner: str) -> list:
    """Ermittelt verfügbare Geschäftsjahre aus Unterordnern oder reYYYYMM.csv-Dateien."""
    jahre = set()
    if ordner and os.path.exists(ordner):
        for d in os.listdir(ordner):
            if os.path.isdir(os.path.join(ordner, d)) and re.match(r"^\d{4}$", d):
                jahre.add(d)
        for f in os.listdir(ordner):
            m = re.match(r"^re(\d{4})\d{2}\.csv$", f.lower())
            if m:
                jahre.add(m.group(1))
    return sorted(list(jahre), reverse=True) if jahre else [datetime.now().strftime("%Y")]


def load_outgoing_journal_rows(ordner: str, jahr: str, monat: str) -> list:
    """Lädt Ausgangsjournal-Einträge für ein Jahr und einen Monat (oder 'Alle Monate')."""
    if not ordner or not os.path.exists(ordner):
        return []

    such_muster = (
        [f"re{jahr}{m:02d}.csv" for m in range(1, 13)]
        if monat == "Alle Monate"
        else [f"re{jahr}{monat}.csv"]
    )

    gefundene = []
    for datei in such_muster:
        p1 = os.path.join(ordner, jahr, datei)
        p2 = os.path.join(ordner, datei)
        pfad = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
        if pfad:
            with open(pfad, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                if not reader.fieldnames:
                    continue
                for row in reader:
                    row.setdefault("Bezahlt", "")
                    row["_csv_path"] = pfad
                    gefundene.append(row)
    return gefundene


def set_outgoing_invoice_paid(rec: dict, paid: bool) -> tuple[bool, str]:
    """Setzt oder entfernt die Bezahlt-Kennzeichnung einer Ausgangsrechnung in ihrer Journal-CSV."""
    csv_path = (rec or {}).get("_csv_path", "")
    re_nr = str((rec or {}).get("Rechnungsnummer", "")).strip()
    if not csv_path or not os.path.isfile(csv_path) or not re_nr:
        return False, "Journaldatei für diese Rechnung wurde nicht gefunden."

    new_paid_val = f"Ja ({datetime.now().strftime('%d.%m.%Y')})" if paid else ""

    try:
        rows = []
        fieldnames = list(OUTGOING_JOURNAL_FIELDS)
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            if reader.fieldnames:
                fieldnames = list(reader.fieldnames)
                if "Bezahlt" not in fieldnames:
                    fieldnames.append("Bezahlt")
            for row in reader:
                if str(row.get("Rechnungsnummer", "")).strip() == re_nr:
                    row["Bezahlt"] = new_paid_val
                else:
                    row.setdefault("Bezahlt", "")
                rows.append({k: row.get(k, "") for k in fieldnames})

        atomic_save_csv(csv_path, fieldnames, rows, delimiter=";")
        return True, ""
    except PermissionError:
        return False, (
            f"Die Journaldatei ist gerade in einem anderen Programm (z. B. Excel) geöffnet:\n"
            f"{csv_path}\n\nBitte schließen Sie die Datei und versuchen Sie es erneut."
        )
    except Exception as e:
        return False, f"Status konnte nicht gespeichert werden:\n{e}"


def create_outgoing_journal_pdf(ordner: str, jahr: str, monat: str, firma_csv: str) -> tuple[str | None, str]:
    """Erzeugt das PDF-Ausgangsjournal inkl. Bezahlt-Haken ('✔') in der Spalte 'Bez.'."""
    if not ordner or not os.path.exists(ordner):
        return None, "Der Auswertungs-Ordner existiert nicht."

    zeit_str = f"{jahr}" if monat == "Alle Monate" else f"{monat}.{jahr}"
    gefundene = load_outgoing_journal_rows(ordner, jahr, monat)
    if not gefundene:
        return None, f"Für {zeit_str} wurden keine Daten gefunden."

    firma_name = lade_firma(firma_csv).get("FirmaName", "Unbekannte Firma")
    jahr_ordner = os.path.join(ordner, jahr)
    os.makedirs(jahr_ordner, exist_ok=True)
    pdf_pfad = os.path.join(jahr_ordner, f"Journal_{zeit_str.replace('.', '_')}.pdf")

    c_dummy = canvas.Canvas(BytesIO(), pagesize=landscape(A4))
    _, hoehe = landscape(A4)

    def render_journal(c_obj, is_final=False, total_pages=1):
        page_num = 1

        def draw_header():
            c_obj.setFont("Helvetica-Bold", 16)
            c_obj.drawString(40, hoehe - 50, f"Rechnungsjournal - {zeit_str} - {firma_name}")
            c_obj.setFont("Helvetica-Bold", 10)
            c_obj.drawString(40, hoehe - 80, "Datum")
            c_obj.drawString(100, hoehe - 80, "Rechnungs-Nr.")
            c_obj.drawString(215, hoehe - 80, "Empfänger")
            c_obj.drawRightString(475, hoehe - 80, "Netto")
            c_obj.drawRightString(550, hoehe - 80, "19% USt.")
            c_obj.drawRightString(625, hoehe - 80, "7% USt.")
            c_obj.drawRightString(695, hoehe - 80, "0% USt.")
            c_obj.drawRightString(770, hoehe - 80, "Brutto")
            c_obj.drawCentredString(802, hoehe - 80, "Bez.")
            c_obj.line(40, hoehe - 85, 820, hoehe - 85)
            return hoehe - 105

        def draw_footer():
            c_obj.setFont("Helvetica", 9)
            c_obj.drawString(40, 20, f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr")
            if total_pages > 1:
                c_obj.drawRightString(820, 20, f"Seite {page_num} / {total_pages}")

        y = draw_header()
        if is_final:
            draw_footer()
        c_obj.setFont("Helvetica", 10)

        sum_n = sum_19 = sum_7 = sum_0 = sum_b = 0.0
        for r in gefundene:
            if y < 60:
                c_obj.showPage()
                page_num += 1
                y = draw_header()
                if is_final:
                    draw_footer()
                c_obj.setFont("Helvetica", 10)

            n = safe_float(r.get("Netto", 0))
            m19 = safe_float(r.get("MwSt_19", 0))
            m7 = safe_float(r.get("MwSt_7", 0))
            m0 = safe_float(r.get("MwSt_0", 0))
            b = safe_float(r.get("Brutto", 0))
            sum_n += n
            sum_19 += m19
            sum_7 += m7
            sum_0 += m0
            sum_b += b

            c_obj.setFont("Helvetica", 10)
            c_obj.drawString(40, y, str(r.get("Datum", "")))
            c_obj.drawString(100, y, str(r.get("Rechnungsnummer", "")))
            empf = str(r.get("Empfaenger", ""))
            c_obj.drawString(215, y, empf[:22] + "..." if len(empf) > 25 else empf)
            c_obj.drawRightString(475, y, f_curr(n))
            c_obj.drawRightString(550, y, f_curr(m19))
            c_obj.drawRightString(625, y, f_curr(m7))
            c_obj.drawRightString(695, y, f_curr(m0))
            c_obj.drawRightString(770, y, f_curr(b))

            if is_invoice_paid(r):
                c_obj.saveState()
                c_obj.setStrokeColorRGB(0.10, 0.55, 0.15)
                c_obj.setLineWidth(1.6)
                cx = 802
                c_obj.line(cx - 4, y + 3, cx - 1, y)
                c_obj.line(cx - 1, y, cx + 5, y + 7)
                c_obj.restoreState()

            y -= 15

        c_obj.line(40, y + 10, 820, y + 10)
        y -= 10
        c_obj.setFont("Helvetica-Bold", 10)
        c_obj.drawString(40, y, "GESAMTSUMMEN:")
        c_obj.drawRightString(475, y, f_curr(sum_n))
        c_obj.drawRightString(550, y, f_curr(sum_19))
        c_obj.drawRightString(625, y, f_curr(sum_7))
        c_obj.drawRightString(695, y, f_curr(sum_0))
        c_obj.drawRightString(770, y, f_curr(sum_b))
        return page_num

    t_pages = render_journal(c_dummy)
    c = canvas.Canvas(pdf_pfad, pagesize=landscape(A4))
    render_journal(c, is_final=True, total_pages=t_pages)
    c.save()
    return pdf_pfad, ""


def export_outgoing_journal_csv(ordner: str, jahr: str, monat: str) -> tuple[str | None, str]:
    """Exportiert Ausgangsjournaldaten als CSV."""
    if not ordner or not os.path.exists(ordner):
        return None, "Der Auswertungs-Ordner existiert nicht."

    zeit_str = f"{jahr}" if monat == "Alle Monate" else f"{monat}.{jahr}"
    gefundene = load_outgoing_journal_rows(ordner, jahr, monat)
    if not gefundene:
        return None, f"Für {zeit_str} wurden keine Daten gefunden."

    header = list(OUTGOING_JOURNAL_FIELDS)
    cleaned = [{k: r.get(k, "") for k in header} for r in gefundene]

    jahr_ordner = os.path.join(ordner, jahr)
    os.makedirs(jahr_ordner, exist_ok=True)
    csv_export_pfad = os.path.join(jahr_ordner, f"Journal_Export_{zeit_str.replace('.', '_')}.csv")
    atomic_save_csv(csv_export_pfad, header, cleaned, delimiter=";")
    return csv_export_pfad, ""


def export_outgoing_datev_csv(ordner: str, jahr: str, monat: str, p_config: dict) -> tuple[str | None, str]:
    """Erstellt den DATEV-ASCII-Export für Ausgangsrechnungen."""
    if not ordner or not os.path.exists(ordner):
        return None, "Der Auswertungs-Ordner existiert nicht."

    zeit_str = f"{jahr}" if monat == "Alle Monate" else f"{monat}.{jahr}"
    gefundene = load_outgoing_journal_rows(ordner, jahr, monat)
    if not gefundene:
        return None, f"Für {zeit_str} wurden keine Daten gefunden."

    jahr_ordner = os.path.join(ordner, jahr)
    os.makedirs(jahr_ordner, exist_ok=True)
    csv_export_pfad = os.path.join(jahr_ordner, f"DATEV_Ausgang_{zeit_str.replace('.', '_')}.csv")

    header = ["Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "Konto", "Gegenkonto (BU-Schlüssel)", "Belegdatum", "Belegfeld 1", "Buchungstext"]
    debitor = (p_config or {}).get("datev_debitor", "10000")
    k19 = (p_config or {}).get("datev_erloese_19", "8400")
    k7 = (p_config or {}).get("datev_erloese_7", "8300")
    k0 = (p_config or {}).get("datev_erloese_0", "8200")

    with open(csv_export_pfad, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(header)

        for r in gefundene:
            netto = safe_float(r.get("Netto", 0))
            mwst19 = safe_float(r.get("MwSt_19", 0))
            mwst7 = safe_float(r.get("MwSt_7", 0))

            netto_19 = round(mwst19 / 0.19, 2) if mwst19 else 0.0
            brutto_19 = netto_19 + mwst19

            netto_7 = round(mwst7 / 0.07, 2) if mwst7 else 0.0
            brutto_7 = netto_7 + mwst7

            netto_0 = round(netto - netto_19 - netto_7, 2)
            brutto_0 = netto_0

            date_str = r.get("Datum", "")
            date_datev = date_str[:2] + date_str[3:5] if len(date_str) >= 5 else ""
            beleg_nr = r.get("Rechnungsnummer", "")[:36]
            buchungstext = r.get("Empfaenger", "")[:60]

            if brutto_19 > 0:
                writer.writerow([f"{brutto_19:.2f}".replace(".", ","), "H", k19, debitor, date_datev, beleg_nr, buchungstext])
            if brutto_7 > 0:
                writer.writerow([f"{brutto_7:.2f}".replace(".", ","), "H", k7, debitor, date_datev, beleg_nr, buchungstext])
            if brutto_0 > 0:
                writer.writerow([f"{brutto_0:.2f}".replace(".", ","), "H", k0, debitor, date_datev, beleg_nr, buchungstext])

    return csv_export_pfad, ""


def export_incoming_journal_csv(folder: str, year: str, month: str) -> tuple[str | None, str]:
    """Exportiert Eingangsjournaldaten als CSV."""
    targets = [f"er{year}{m:02d}.csv" for m in range(1, 13)] if month == "Alle Monate" else [f"er{year}{month}.csv"]
    zeit_str = year if month == "Alle Monate" else f"{month}.{year}"

    gefundene = []
    header = []
    for fname in targets:
        p1 = os.path.join(folder, year, fname)
        p2 = os.path.join(folder, fname)
        pfad = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
        if pfad:
            with open(pfad, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                if reader.fieldnames and not header:
                    header = list(reader.fieldnames)
                for row in reader:
                    gefundene.append(row)

    if not gefundene:
        return None, f"Für {zeit_str} wurden keine Daten gefunden."

    jahr_ordner = os.path.join(folder, year)
    os.makedirs(jahr_ordner, exist_ok=True)
    csv_export_pfad = os.path.join(jahr_ordner, f"Eingangsjournal_Export_{zeit_str.replace('.', '_')}.csv")
    atomic_save_csv(csv_export_pfad, header, gefundene, delimiter=";")
    return csv_export_pfad, ""


def export_incoming_datev_csv(folder: str, year: str, month: str, p_config: dict) -> tuple[str | None, str]:
    """Erstellt den DATEV-ASCII-Export für Eingangsrechnungen."""
    targets = [f"er{year}{m:02d}.csv" for m in range(1, 13)] if month == "Alle Monate" else [f"er{year}{month}.csv"]
    zeit_str = year if month == "Alle Monate" else f"{month}.{year}"

    gefundene = []
    for fname in targets:
        p1 = os.path.join(folder, year, fname)
        p2 = os.path.join(folder, fname)
        pfad = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
        if pfad:
            with open(pfad, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f, delimiter=";"):
                    gefundene.append(row)

    if not gefundene:
        return None, f"Für {zeit_str} wurden keine Daten gefunden."

    jahr_ordner = os.path.join(folder, year)
    os.makedirs(jahr_ordner, exist_ok=True)
    csv_export_pfad = os.path.join(jahr_ordner, f"DATEV_Eingang_{zeit_str.replace('.', '_')}.csv")

    header = ["Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "Konto", "Gegenkonto (BU-Schlüssel)", "Belegdatum", "Belegfeld 1", "Buchungstext"]
    kreditor = (p_config or {}).get("datev_kreditor", "70000")
    def_a19 = (p_config or {}).get("datev_aufwand_19", "3400")
    def_a7 = (p_config or {}).get("datev_aufwand_7", "3300")
    def_a0 = (p_config or {}).get("datev_aufwand_0", "3200")

    with open(csv_export_pfad, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(header)

        for r in gefundene:
            netto = safe_float(r.get("Netto", 0))
            mwst19 = safe_float(r.get("MwSt_19", 0))
            mwst7 = safe_float(r.get("MwSt_7", 0))

            netto_19 = round(mwst19 / 0.19, 2) if mwst19 else 0.0
            brutto_19 = netto_19 + mwst19

            netto_7 = round(mwst7 / 0.07, 2) if mwst7 else 0.0
            brutto_7 = netto_7 + mwst7

            netto_0 = round(netto - netto_19 - netto_7, 2)
            brutto_0 = netto_0

            date_str = r.get("Rechnungsdatum", "")
            date_datev = date_str[:2] + date_str[3:5] if len(date_str) >= 5 else ""
            beleg_nr = r.get("Externe Rechnungsnummer", "")[:36]
            buchungstext = r.get("Lieferant", "")[:60]
            erfasstes_konto = extract_account_number(r.get("Konto", ""))

            if brutto_19 > 0:
                writer.writerow([f"{brutto_19:.2f}".replace(".", ","), "S", erfasstes_konto or def_a19, kreditor, date_datev, beleg_nr, buchungstext])
            if brutto_7 > 0:
                writer.writerow([f"{brutto_7:.2f}".replace(".", ","), "S", erfasstes_konto or def_a7, kreditor, date_datev, beleg_nr, buchungstext])
            if brutto_0 > 0:
                writer.writerow([f"{brutto_0:.2f}".replace(".", ","), "S", erfasstes_konto or def_a0, kreditor, date_datev, beleg_nr, buchungstext])

    return csv_export_pfad, ""


def create_audit_log_pdf(base_data_path: str, profil_name: str, bereich: str, jahr: str) -> tuple[str | None, str]:
    """Erstellt das GoBD-Audit-Log als PDF."""
    if not base_data_path:
        return None, "Kein Daten-Grundpfad definiert."

    firm_dir = os.path.join(base_data_path, profil_name.replace(" ", "_"))
    audit_csv = os.path.join(firm_dir, "audit", jahr, f"audit_{bereich}_{jahr}.csv")
    if not os.path.exists(audit_csv):
        return None, f"Für das Jahr {jahr} existiert noch kein Audit-Log ({bereich})."

    gefundene = []
    with open(audit_csv, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            gefundene.append(row)

    if not gefundene:
        return None, "Das Audit-Log ist leer."

    pdf_pfad = os.path.join(firm_dir, "audit", jahr, f"AuditLog_{bereich}_{jahr}.pdf")
    _, hoehe = landscape(A4)

    def render_journal(c_obj, is_final=False, total_pages=1):
        page_num = 1

        def draw_header():
            c_obj.setFont("Helvetica-Bold", 15)
            c_obj.drawString(35, hoehe - 45, f"GoBD Audit-Log ({bereich}) - {jahr} - {profil_name}")
            c_obj.setFont("Helvetica-Bold", 9)
            y_h = hoehe - 75
            c_obj.drawString(35, y_h, "Zeitstempel")
            c_obj.drawString(130, y_h, "Arbeitsplatz")
            c_obj.drawString(220, y_h, "Modus")
            c_obj.drawString(280, y_h, "Aktion")
            c_obj.drawString(350, y_h, "BelegNr")
            c_obj.drawString(450, y_h, "Bemerkung / Begründung")
            c_obj.line(35, y_h - 5, 815, y_h - 5)
            return y_h - 20

        def draw_footer():
            c_obj.setFont("Helvetica", 8.5)
            c_obj.drawString(35, 20, f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr")
            if total_pages > 1:
                c_obj.drawRightString(815, 20, f"Seite {page_num} / {total_pages}")

        y = draw_header()
        if is_final:
            draw_footer()
        c_obj.setFont("Helvetica", 9)

        for r in gefundene:
            if y < 40:
                c_obj.showPage()
                page_num += 1
                y = draw_header()
                if is_final:
                    draw_footer()
                c_obj.setFont("Helvetica", 9)

            c_obj.drawString(35, y, r.get("Zeitstempel", ""))
            c_obj.drawString(130, y, str(r.get("Arbeitsplatz", ""))[:15])
            c_obj.drawString(220, y, str(r.get("Modus", "")))
            c_obj.drawString(280, y, str(r.get("Aktion", "")))
            c_obj.drawString(350, y, str(r.get("BelegNr", "")))

            bem = str(r.get("Bemerkung", ""))
            if len(bem) > 75:
                bem = bem[:72] + "..."
            c_obj.drawString(450, y, bem)
            y -= 15

        return page_num

    c_dummy = canvas.Canvas(BytesIO(), pagesize=landscape(A4))
    t_pages = render_journal(c_dummy)

    c = canvas.Canvas(pdf_pfad, pagesize=landscape(A4))
    render_journal(c, is_final=True, total_pages=t_pages)
    c.save()
    return pdf_pfad, ""