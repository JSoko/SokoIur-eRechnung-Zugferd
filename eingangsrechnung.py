"""
eingangsrechnung.py
-------------------
Logik für die Erkennung, Validierung (CII & UBL), Duplikatsprüfung (SHA-256 & Belegdaten),
Leseabschrift-Generierung, Archivierung, Suche/Stornierung und Journalisierung
von Eingangsrechnungen.
"""
import os
import re
import csv
import hashlib
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from io import BytesIO

from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape


JOURNAL_FIELDS = [
    "Interne ER-Nr.",
    "Eingangsdatum",
    "Rechnungsdatum",
    "Lieferant",
    "Externe Rechnungsnummer",
    "Format",
    "Netto",
    "MwSt_19",
    "MwSt_7",
    "MwSt_sonstige",
    "Brutto",
    "Vorsteuer geprüft",
    "Quelldatei",
    "Archivdatei",
    "Dateihash",
]


def _d(val, default="0.00") -> Decimal:
    """Konvertiert beliebige Eingaben sicher in ein Decimal auf 2 Nachkommastellen."""
    if val is None:
        return Decimal(default)
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    s = str(val).strip().replace("€", "").replace("EUR", "").strip()
    if not s:
        return Decimal(default)
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return Decimal(s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return Decimal(default)


def _money(val) -> str:
    """Formatiert einen Wert als deutschen Währungsstring ohne Symbol (z. B. '123,45')."""
    d = _d(val)
    return f"{d:.2f}".replace(".", ",")


def file_sha256(path: str) -> str:
    """Berechnet den SHA-256-Hash einer Datei zur zuverlässigen Duplikatserkennung."""
    if not path or not os.path.isfile(path):
        return ""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def normalize_date_de(date_str: str) -> str:
    """Wandelt diverse Datumsformate (YYYYMMDD, YYYY-MM-DD, DD.MM.YY etc.) in TT.MM.JJJJ um."""
    if not date_str:
        return ""
    s = str(date_str).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%Y%m%d", "%d.%m.%y", "%d%m%Y", "%d%m%y", "%d,%m,%Y", "%d,%m,%y"):
        try:
            return datetime.strptime(s, fmt).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return s


def next_number(last_nr: str, year: str) -> str:
    """Berechnet die nächste interne Eingangsrechnungsnummer (z. B. ER260001)."""
    yy = str(year)[-2:] if len(str(year)) >= 2 else datetime.now().strftime("%y")
    prefix = f"ER{yy}"
    if last_nr and last_nr.upper().startswith(prefix):
        m = re.search(r"(\d+)$", last_nr)
        if m:
            num = int(m.group(1)) + 1
            return f"{prefix}{num:04d}"
    return f"{prefix}0001"


def load_all_journal_entries(journal_base_folder: str) -> list:
    """Liest sämtliche erfassten Eingangsrechnungen aus allen Journal-CSVs ein."""
    entries = []
    if not journal_base_folder or not os.path.isdir(journal_base_folder):
        return entries

    csv_files = []
    for root, dirs, files in os.walk(journal_base_folder):
        for f in files:
            if re.match(r"^er\d{6}\.csv$", f.lower()):
                csv_files.append(os.path.join(root, f))

    for csv_path in sorted(csv_files, reverse=True):
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f, delimiter=";"):
                    row["_csv_path"] = csv_path
                    entries.append(row)
        except Exception:
            pass
    return entries


def check_duplicate_incoming(
    path: str,
    journal_base_folder: str,
    waiting_list: list = None,
    invoice_data: dict = None,
    entries: list = None,
):
    """
    Prüft mehrstufig, ob eine Datei im Eingangsordner bereits erfasst wurde:
    1. Steht der Dateipfad bereits auf der Lösch-Warteliste (`eingang_loesch_warteliste`)?
    2. Stimmt der SHA-256-Hash mit einer bereits im Journal oder Archiv vorhandenen Datei überein?
    3. Stimmen Lieferant + Externe Rechnungsnummer + Bruttobetrag mit einem Journaleintrag überein?

    Rückgabe: (is_duplicate: bool, reason_msg: str, existing_record: dict or None)
    """
    abs_path = os.path.abspath(path)
    norm_wait = {os.path.abspath(p) for p in (waiting_list or []) if p}
    if abs_path in norm_wait:
        return (
            True,
            "Diese Datei wurde bereits erfasst, konnte aber beim letzten Mal im Eingangsordner nicht gelöscht werden (Lösch-Warteliste).",
            None,
        )

    f_hash = file_sha256(path)
    #entries = load_all_journal_entries(journal_base_folder)
    if entries is None:
        entries = load_all_journal_entries(journal_base_folder)

    for rec in entries:
        er_nr = rec.get("Interne ER-Nr.", "")
        rec_hash = (rec.get("Dateihash") or "").strip()
        arch_path = rec.get("Archivdatei", "")

        if not rec_hash and arch_path and os.path.isfile(arch_path):
            rec_hash = file_sha256(arch_path)

        if f_hash and rec_hash and f_hash == rec_hash:
            return (
                True,
                f"Exakt identische Datei wurde bereits unter der internen Nummer {er_nr} "
                f"(Lieferant: {rec.get('Lieferant', '-')}, RE-Nr.: {rec.get('Externe Rechnungsnummer', '-')}) erfasst.",
                rec,
            )

        if invoice_data:
            sup_new = (invoice_data.get("supplier") or "").strip().lower()
            num_new = (invoice_data.get("number") or "").strip().lower()
            gross_new = _d(invoice_data.get("gross", "0"))

            sup_old = (rec.get("Lieferant") or "").strip().lower()
            num_old = (rec.get("Externe Rechnungsnummer") or "").strip().lower()
            gross_old = _d(rec.get("Brutto", "0"))

            if (
                sup_new
                and num_new
                and num_new not in ("ohne nr.", "-")
                and sup_new == sup_old
                and num_new == num_old
                and gross_new == gross_old
            ):
                return (
                    True,
                    f"Eine Rechnung von '{rec.get('Lieferant')}' mit der Rechnungsnummer '{rec.get('Externe Rechnungsnummer')}' "
                    f"und dem Bruttobetrag {_money(gross_old)} € wurde bereits unter {er_nr} erfasst.",
                    rec,
                )

    return False, "", None


def delete_journal_entry(
    journal_base_folder: str,
    er_nr: str,
    delete_archive_files: bool = True,
    rebearb_base_folder: str = "",
) -> tuple:
    """
    Entfernt einen Eintrag anhand seiner internen ER-Nr. aus der Monats-CSV und
    löscht optional die zugehörige Archivdatei, Leseabschrift und Kopie in rebearb.
    Rückgabe: (success: bool, message: str)
    """
    entries = load_all_journal_entries(journal_base_folder)
    target = None
    for r in entries:
        if r.get("Interne ER-Nr.", "").strip().upper() == er_nr.strip().upper():
            target = r
            break

    if not target:
        return False, f"Eintrag {er_nr} wurde im Journal nicht gefunden."

    csv_path = target.get("_csv_path")
    if not csv_path or not os.path.isfile(csv_path):
        return False, f"Journaldatei für {er_nr} nicht gefunden."

    try:
        remaining = []
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            fieldnames = reader.fieldnames or JOURNAL_FIELDS
            for row in reader:
                if row.get("Interne ER-Nr.", "").strip().upper() != er_nr.strip().upper():
                    remaining.append(row)

        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for r in remaining:
                clean_r = {k: r.get(k, "") for k in fieldnames}
                writer.writerow(clean_r)
    except Exception as e:
        return False, f"Fehler beim Aktualisieren der Journal-CSV: {e}"

    deleted_files = []
    if delete_archive_files:
        arch_file = target.get("Archivdatei", "")
        if arch_file and os.path.isfile(arch_file):
            try:
                os.remove(arch_file)
                deleted_files.append(os.path.basename(arch_file))
            except Exception:
                pass
            lese_pdf = os.path.join(os.path.dirname(arch_file), f"{er_nr}_Leseabschrift.pdf")
            if os.path.isfile(lese_pdf):
                try:
                    os.remove(lese_pdf)
                    deleted_files.append(os.path.basename(lese_pdf))
                except Exception:
                    pass

        if rebearb_base_folder and os.path.isdir(rebearb_base_folder):
            quell_name = target.get("Quelldatei", "")
            for root, dirs, files in os.walk(rebearb_base_folder):
                for fname in files:
                    if fname == f"{er_nr}_{quell_name}" or (quell_name and fname == quell_name):
                        fpath = os.path.join(root, fname)
                        try:
                            os.remove(fpath)
                            deleted_files.append(fname)
                        except Exception:
                            pass

    info_files = f" (Gelöschte Dateien: {', '.join(deleted_files)})" if deleted_files else ""
    return True, f"Eingangsrechnung {er_nr} wurde erfolgreich aus dem Journal entfernt{info_files}."


def _extract_xml_from_pdf(pdf_path: str):
    """Extrahiert eingebettete ZUGFeRD / Factur-X XML-Dateien aus einem PDF."""
    try:
        reader = PdfReader(pdf_path)
        if hasattr(reader, "attachments") and reader.attachments:
            for filename, content_list in reader.attachments.items():
                fname_lower = filename.lower()
                if fname_lower.endswith(".xml") or "factur" in fname_lower or "zugferd" in fname_lower or "xrechnung" in fname_lower:
                    raw = content_list[0] if isinstance(content_list, list) and content_list else content_list
                    if isinstance(raw, bytes):
                        return raw.decode("utf-8-sig", errors="replace")
        root = reader.trailer.get("/Root", {})
        if hasattr(root, "get_object"):
            root = root.get_object()
        names = root.get("/Names", {})
        if hasattr(names, "get_object"):
            names = names.get_object()
        ef = names.get("/EmbeddedFiles", {})
        if hasattr(ef, "get_object"):
            ef = ef.get_object()
        ef_names = ef.get("/Names", [])
        if hasattr(ef_names, "get_object"):
            ef_names = ef_names.get_object()
        for i in range(0, len(ef_names), 2):
            fname = str(ef_names[i]).lower()
            fspec = ef_names[i + 1].get_object()
            if fname.endswith(".xml") and "/EF" in fspec:
                ef_dict = fspec["/EF"].get_object()
                stream = (ef_dict.get("/F") or ef_dict.get("/UF")).get_object()
                data = stream.get_data()
                return data.decode("utf-8-sig", errors="replace")
    except Exception:
        pass
    return None


def detect_invoice(path: str):
    """
    Erkennt den Typ einer Eingangsrechnung.
    Rückgabe: (kind, xml_string_or_None, detail_info)
    kind: 'ZUGFeRD', 'XRechnung' oder 'Other'
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xml":
        try:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                xml_str = f.read()
            if "<" in xml_str and ("CrossIndustryInvoice" in xml_str or "Invoice" in xml_str or "CreditNote" in xml_str):
                return "XRechnung", xml_str, "XML-Rechnung erkannt"
            return "Other", None, "XML-Datei (kein bekanntes e-Rechnungsformat)"
        except Exception as e:
            return "Other", None, f"XML nicht lesbar: {e}"

    if ext == ".pdf":
        xml_str = _extract_xml_from_pdf(path)
        if xml_str and ("CrossIndustryInvoice" in xml_str or "Invoice" in xml_str):
            return "ZUGFeRD", xml_str, "ZUGFeRD / Factur-X Hybrid-PDF erkannt"
        return "Other", None, "Standard-PDF (ohne eingebettetes e-Rechnungs-XML)"

    return "Other", None, f"Sonstiges Dateiformat ({ext})"


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _find_text(elem, path_list) -> str:
    """Sucht rekursiv nach einer Pfad-Sequenz aus lokalen Tag-Namen."""
    if elem is None:
        return ""
    current = [elem]
    for step in path_list:
        next_elems = []
        for c in current:
            for child in c:
                if _local_name(child.tag) == step:
                    next_elems.append(child)
        current = next_elems
        if not current:
            return ""
    for candidate in current:
        if candidate.text and candidate.text.strip():
            return candidate.text.strip()
    return ""


def _findall_seq(elem, path_list):
    """Gibt alle Elemente zurück, die der Tag-Sequenz entsprechen."""
    if elem is None:
        return []
    current = [elem]
    for step in path_list:
        next_elems = []
        for c in current:
            for child in c:
                if _local_name(child.tag) == step:
                    next_elems.append(child)
        current = next_elems
        if not current:
            return []
    return current


def parse_einvoice(xml_str: str, kind: str = "XRechnung"):
    """
    Liest CII- und UBL-XML-Rechnungen aus und führt eine formelle & rechnerische
    Plausibilitätsprüfung nach EN 16931 / § 14 Abs. 4 UStG durch.
    Rückgabe: (data_dict, errors_list)
    """
    data = {
        "supplier": "",
        "supplier_street": "",
        "supplier_zip": "",
        "supplier_city": "",
        "supplier_tax_id": "",
        "supplier_email": "",
        "buyer": "",
        "number": "",
        "date": "",
        "due_date": "",
        "delivery_date": "",
        "currency": "EUR",
        "iban": "",
        "net": "0.00",
        "tax": "0.00",
        "gross": "0.00",
        "taxes": {},
        "lines": [],
    }
    errors = []

    if not xml_str:
        return data, ["Die XML-Daten sind leer oder konnten nicht extrahiert werden."]

    try:
        root = ET.fromstring(xml_str.strip())
    except Exception as e:
        return data, [f"XML-Strukturfehler (Datei nicht wohlgeformt): {e}"]

    root_name = _local_name(root.tag)
    line_sum = Decimal("0.00")

    if "CrossIndustryInvoice" in root_name:
        data["number"] = _find_text(root, ["ExchangedDocument", "ID"])
        raw_date = _find_text(root, ["ExchangedDocument", "IssueDateTime", "DateTimeString"])
        data["date"] = normalize_date_de(raw_date)

        seller = (_findall_seq(root, ["SupplyChainTradeTransaction", "ApplicableHeaderTradeAgreement", "SellerTradeParty"]) or [None])[0]
        if seller is not None:
            data["supplier"] = _find_text(seller, ["Name"])
            data["supplier_street"] = _find_text(seller, ["PostalTradeAddress", "LineOne"])
            data["supplier_zip"] = _find_text(seller, ["PostalTradeAddress", "PostcodeCode"])
            data["supplier_city"] = _find_text(seller, ["PostalTradeAddress", "CityName"])
            data["supplier_email"] = (
                _find_text(seller, ["DefinedTradeContact", "EmailURIUniversalCommunication", "URIID"])
                or _find_text(seller, ["URIUniversalCommunication", "URIID"])
            )
            tax_regs = _findall_seq(seller, ["SpecifiedTaxRegistration", "ID"])
            if tax_regs and tax_regs[0].text:
                data["supplier_tax_id"] = tax_regs[0].text.strip()

        buyer = (_findall_seq(root, ["SupplyChainTradeTransaction", "ApplicableHeaderTradeAgreement", "BuyerTradeParty"]) or [None])[0]
        if buyer is not None:
            data["buyer"] = _find_text(buyer, ["Name"])

        deliv_raw = _find_text(root, ["SupplyChainTradeTransaction", "ApplicableHeaderTradeDelivery", "ActualDeliverySupplyChainEvent", "OccurrenceDateTime", "DateTimeString"])
        p_start = _find_text(root, ["SupplyChainTradeTransaction", "ApplicableHeaderTradeSettlement", "BillingSpecifiedPeriod", "StartDateTime", "DateTimeString"])
        p_end = _find_text(root, ["SupplyChainTradeTransaction", "ApplicableHeaderTradeSettlement", "BillingSpecifiedPeriod", "EndDateTime", "DateTimeString"])
        if p_start and p_end:
            data["delivery_date"] = f"{normalize_date_de(p_start)} - {normalize_date_de(p_end)}"
        elif deliv_raw:
            data["delivery_date"] = normalize_date_de(deliv_raw)

        settlement = (_findall_seq(root, ["SupplyChainTradeTransaction", "ApplicableHeaderTradeSettlement"]) or [None])[0]
        if settlement is not None:
            data["currency"] = _find_text(settlement, ["InvoiceCurrencyCode"]) or "EUR"
            data["iban"] = _find_text(settlement, ["SpecifiedTradeSettlementPaymentMeans", "PayeePartyCreditorFinancialAccount", "IBANID"])
            due_raw = _find_text(settlement, ["SpecifiedTradePaymentTerms", "DueDateDateTime", "DateTimeString"])
            data["due_date"] = normalize_date_de(due_raw)

            for tax_el in _findall_seq(settlement, ["ApplicableTradeTax"]):
                rate_str = _find_text(tax_el, ["RateApplicablePercent"])
                calc_amt = _d(_find_text(tax_el, ["CalculatedAmount"]))
                rate_key = str(int(_d(rate_str))) if _d(rate_str) == int(_d(rate_str)) else str(_d(rate_str))
                data["taxes"][rate_key] = data["taxes"].get(rate_key, Decimal("0.00")) + calc_amt

            summation = (_findall_seq(settlement, ["SpecifiedTradeSettlementHeaderMonetarySummation"]) or [None])[0]
            if summation is not None:
                net_val = _find_text(summation, ["TaxBasisTotalAmount"]) or _find_text(summation, ["LineTotalAmount"])
                tax_val = _find_text(summation, ["TaxTotalAmount"])
                gross_val = _find_text(summation, ["GrandTotalAmount"]) or _find_text(summation, ["DuePayableAmount"])
                data["net"] = str(_d(net_val))
                data["tax"] = str(_d(tax_val))
                data["gross"] = str(_d(gross_val))

        for item in _findall_seq(root, ["SupplyChainTradeTransaction", "IncludedSupplyChainTradeLineItem"]):
            pos_id = _find_text(item, ["AssociatedDocumentLineDocument", "LineID"])
            name = _find_text(item, ["SpecifiedTradeProduct", "Name"])
            qty = _d(_find_text(item, ["SpecifiedLineTradeDelivery", "BilledQuantity"]), "1.00")
            price = _d(_find_text(item, ["SpecifiedLineTradeAgreement", "NetPriceProductTradePrice", "ChargeAmount"]))
            line_net = _d(_find_text(item, ["SpecifiedLineTradeSettlement", "SpecifiedTradeSettlementLineMonetarySummation", "LineTotalAmount"]))
            rate = _find_text(item, ["SpecifiedLineTradeSettlement", "ApplicableTradeTax", "RateApplicablePercent"])
            line_sum += line_net
            data["lines"].append({"pos": pos_id, "name": name, "qty": str(qty), "price": str(price), "net": str(line_net), "rate": rate})

    elif root_name in ("Invoice", "CreditNote"):
        data["number"] = _find_text(root, ["ID"])
        data["date"] = normalize_date_de(_find_text(root, ["IssueDate"]))
        data["due_date"] = normalize_date_de(_find_text(root, ["DueDate"]))
        data["currency"] = _find_text(root, ["DocumentCurrencyCode"]) or "EUR"

        seller = (_findall_seq(root, ["AccountingSupplierParty", "Party"]) or [None])[0]
        if seller is not None:
            data["supplier"] = _find_text(seller, ["PartyLegalEntity", "RegistrationName"]) or _find_text(seller, ["PartyName", "Name"])
            data["supplier_street"] = _find_text(seller, ["PostalAddress", "StreetName"])
            data["supplier_zip"] = _find_text(seller, ["PostalAddress", "PostalZone"])
            data["supplier_city"] = _find_text(seller, ["PostalAddress", "CityName"])
            data["supplier_email"] = _find_text(seller, ["Contact", "ElectronicMail"]) or _find_text(seller, ["EndpointID"])
            data["supplier_tax_id"] = _find_text(seller, ["PartyTaxScheme", "CompanyID"])

        buyer = (_findall_seq(root, ["AccountingCustomerParty", "Party"]) or [None])[0]
        if buyer is not None:
            data["buyer"] = _find_text(buyer, ["PartyLegalEntity", "RegistrationName"]) or _find_text(buyer, ["PartyName", "Name"])

        deliv_date = _find_text(root, ["Delivery", "ActualDeliveryDate"])
        p_start = _find_text(root, ["InvoicePeriod", "StartDate"])
        p_end = _find_text(root, ["InvoicePeriod", "EndDate"])
        if p_start and p_end:
            data["delivery_date"] = f"{normalize_date_de(p_start)} - {normalize_date_de(p_end)}"
        elif deliv_date:
            data["delivery_date"] = normalize_date_de(deliv_date)

        data["iban"] = _find_text(root, ["PaymentMeans", "PayeeFinancialAccount", "ID"])

        for sub in _findall_seq(root, ["TaxTotal", "TaxSubtotal"]):
            rate_str = _find_text(sub, ["TaxCategory", "Percent"])
            calc_amt = _d(_find_text(sub, ["TaxAmount"]))
            rate_key = str(int(_d(rate_str))) if _d(rate_str) == int(_d(rate_str)) else str(_d(rate_str))
            data["taxes"][rate_key] = data["taxes"].get(rate_key, Decimal("0.00")) + calc_amt

        tax_total_str = _find_text(root, ["TaxTotal", "TaxAmount"])
        monetary = (_findall_seq(root, ["LegalMonetaryTotal"]) or [None])[0]
        if monetary is not None:
            net_val = _find_text(monetary, ["TaxExclusiveAmount"]) or _find_text(monetary, ["LineExtensionAmount"])
            gross_val = _find_text(monetary, ["TaxInclusiveAmount"]) or _find_text(monetary, ["PayableAmount"])
            data["net"] = str(_d(net_val))
            data["gross"] = str(_d(gross_val))
        data["tax"] = str(_d(tax_total_str))

        line_tag = "CreditNoteLine" if root_name == "CreditNote" else "InvoiceLine"
        for item in _findall_seq(root, [line_tag]):
            pos_id = _find_text(item, ["ID"])
            name = _find_text(item, ["Item", "Name"]) or _find_text(item, ["Item", "Description"])
            qty = _d(_find_text(item, ["InvoicedQuantity"]) or _find_text(item, ["CreditedQuantity"]), "1.00")
            price = _d(_find_text(item, ["Price", "PriceAmount"]))
            line_net = _d(_find_text(item, ["LineExtensionAmount"]))
            rate = _find_text(item, ["Item", "ClassifiedTaxCategory", "Percent"])
            line_sum += line_net
            data["lines"].append({"pos": pos_id, "name": name, "qty": str(qty), "price": str(price), "net": str(line_net), "rate": rate})
    else:
        return data, [f"Unbekanntes XML-Wurzelelement '{root_name}'. Erwartet wurde CrossIndustryInvoice oder UBL Invoice."]

    if not data["supplier"]:
        errors.append("Name des Rechnungsausstellers (BT-27) fehlt.")
    if not data["number"]:
        errors.append("Rechnungsnummer (BT-1) fehlt.")
    if not data["date"] or not re.match(r"^\d{2}\.\d{2}\.\d{4}$", data["date"]):
        errors.append("Gültiges Rechnungsdatum (BT-2) fehlt.")
    if not data["supplier_tax_id"]:
        errors.append("Steuernummer oder USt-IdNr. des Ausstellers (BT-31/BT-32) fehlt.")
    if not data["lines"]:
        errors.append("Die Rechnung enthält keine auslesbaren Rechnungspositionen (BG-25).")

    net_d = _d(data["net"])
    tax_d = _d(data["tax"])
    gross_d = _d(data["gross"])

    if tax_d == Decimal("0.00") and data["taxes"]:
        tax_d = sum(data["taxes"].values(), Decimal("0.00"))
        data["tax"] = str(tax_d)

    if abs((net_d + tax_d) - gross_d) > Decimal("0.05"):
        errors.append(f"Summenfehler im Belegkopf: Netto ({_money(net_d)} €) + USt ({_money(tax_d)} €) ergibt nicht Brutto ({_money(gross_d)} €).")

    if data["lines"] and abs(line_sum - net_d) > Decimal("0.05"):
        errors.append(f"Positionssumme ({_money(line_sum)} €) weicht vom Netto-Gesamtbetrag ({_money(net_d)} €) ab.")

    return data, errors


def error_notice(data: dict, errors: list):
    """Erstellt einen kopierbaren E-Mail-Betreff und Text für fehlerhafte Eingangsrechnungen."""
    nr = data.get("number") or "ohne Nummer"
    dat = data.get("date") or "ohne Datum"
    subject = f"Bitte um Rechnungskorrektur – Rechnung {nr} vom {dat}"
    err_bullets = "\n".join(f"- {e}" for e in errors)
    body = (
        f"Sehr geehrte Damen und Herren,\n\n"
        f"bei der automatisierten formellen und rechnerischen Prüfung Ihrer elektronischen Rechnung "
        f"(Nr.: {nr} vom {dat}) sind folgende Unstimmigkeiten nach EN 16931 / § 14 Abs. 4 UStG aufgefallen:\n\n"
        f"{err_bullets}\n\n"
        f"Wir bitten Sie um Überprüfung und Zusendung einer berichtigten elektronischen Rechnung.\n\n"
        f"Mit freundlichen Grüßen"
    )
    return subject, body


def make_readable_pdf(data: dict, out_path: str):
    """Erzeugt eine übersichtliche PDF-Leseabschrift für eine XRechnung."""
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 15)
    c.drawString(45, y, f"Leseabschrift zur XRechnung {data.get('number', '')}")
    y -= 18
    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(45, y, "Hinweis: Dies ist eine automatisch generierte Leseabschrift. Rechtlich maßgeblich ist die archivierte XML-Originaldatei.")
    c.setFillColorRGB(0, 0, 0)
    y -= 25

    c.setFont("Helvetica-Bold", 10)
    c.drawString(45, y, "Rechnungsaussteller:")
    c.drawString(320, y, "Rechnungsdetails:")
    y -= 14

    c.setFont("Helvetica", 9.5)
    c.drawString(45, y, data.get("supplier", ""))
    c.drawString(320, y, f"Rechnungs-Nr.: {data.get('number', '')}")
    y -= 13
    c.drawString(45, y, data.get("supplier_street", ""))
    c.drawString(320, y, f"Rechnungsdatum: {data.get('date', '')}")
    y -= 13
    c.drawString(45, y, f"{data.get('supplier_zip', '')} {data.get('supplier_city', '')}".strip())
    c.drawString(320, y, f"Leistungsdatum: {data.get('delivery_date', '') or '-'}")
    y -= 13
    c.drawString(45, y, f"USt-IdNr./StNr.: {data.get('supplier_tax_id', '')}")
    c.drawString(320, y, f"Fälligkeit: {data.get('due_date', '') or '-'}")
    if data.get("iban"):
        y -= 13
        c.drawString(320, y, f"IBAN: {data.get('iban', '')}")

    y -= 25
    c.line(45, y, width - 45, y)
    y -= 15

    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(45, y, "Pos.")
    c.drawString(85, y, "Bezeichnung")
    c.drawRightString(360, y, "Menge")
    c.drawRightString(440, y, "Einzelpreis")
    c.drawRightString(490, y, "USt.")
    c.drawRightString(width - 45, y, "Netto")
    y -= 6
    c.line(45, y, width - 45, y)
    y -= 14

    c.setFont("Helvetica", 9)
    for line in data.get("lines", []):
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)
        c.drawString(45, y, str(line.get("pos", ""))[:6])
        c.drawString(85, y, str(line.get("name", ""))[:45])
        c.drawRightString(360, y, _money(line.get("qty", "1")))
        c.drawRightString(440, y, f"{_money(line.get('price', '0'))} €")
        c.drawRightString(490, y, f"{line.get('rate', '19')}%")
        c.drawRightString(width - 45, y, f"{_money(line.get('net', '0'))} €")
        y -= 14

    y -= 10
    c.line(320, y, width - 45, y)
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(320, y, "Netto Gesamt:")
    c.drawRightString(width - 45, y, f"{_money(data.get('net', '0'))} €")
    y -= 14
    c.drawString(320, y, "Umsatzsteuer:")
    c.drawRightString(width - 45, y, f"{_money(data.get('tax', '0'))} €")
    y -= 15
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(320, y, "Brutto Gesamt:")
    c.drawRightString(width - 45, y, f"{_money(data.get('gross', '0'))} €")

    c.save()
    return out_path


def write_journal(journal_base_folder: str, record: dict) -> str:
    """Schreibt einen Datensatz in das Monats-Eingangsjournal (einj/<Jahr>/erYYYYMM.csv)."""
    r_date = normalize_date_de(record.get("Rechnungsdatum", ""))
    if re.match(r"^\d{2}\.\d{2}\.\d{4}$", r_date):
        month = r_date[3:5]
        year = r_date[6:10]
    else:
        now = datetime.now()
        month = now.strftime("%m")
        year = now.strftime("%Y")

    year_dir = os.path.join(journal_base_folder, year)
    os.makedirs(year_dir, exist_ok=True)
    csv_path = os.path.join(year_dir, f"er{year}{month}.csv")

    existing_rows = []
    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                existing_rows = list(csv.DictReader(f, delimiter=";"))
        except Exception:
            existing_rows = []

    row = {k: record.get(k, "") for k in JOURNAL_FIELDS}
    existing_rows.append(row)

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=JOURNAL_FIELDS, delimiter=";")
        writer.writeheader()
        for r in existing_rows:
            writer.writerow({k: r.get(k, "") for k in JOURNAL_FIELDS})
    return csv_path


def create_journal_pdf(journal_base_folder: str, year: str, month: str, firma_name: str = ""):
    """Erzeugt das PDF-Eingangsjournal inkl. klickbarer Links auf die archivierten Originalbelege."""
    if not os.path.isdir(journal_base_folder):
        return None

    year = str(year).strip()
    targets = [f"er{year}{m:02d}.csv" for m in range(1, 13)] if month == "Alle Monate" else [f"er{year}{month}.csv"]
    zeit_str = year if month == "Alle Monate" else f"{month}.{year}"

    rows = []
    for fname in targets:
        p1 = os.path.join(journal_base_folder, year, fname)
        p2 = os.path.join(journal_base_folder, fname)
        pfad = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
        if pfad:
            with open(pfad, "r", encoding="utf-8-sig") as f:
                for r in csv.DictReader(f, delimiter=";"):
                    rows.append(r)

    if not rows:
        return None

    out_dir = os.path.join(journal_base_folder, year)
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, f"Eingangsjournal_{zeit_str.replace('.', '_')}.pdf")

    width, height = landscape(A4)

    def _render(c_obj, is_final=False, total_pages=1):
        page_num = 1

        def draw_header():
            c_obj.setFont("Helvetica-Bold", 15)
            c_obj.drawString(35, height - 45, f"Eingangsrechnungsjournal - {zeit_str} - {firma_name}")
            c_obj.setFont("Helvetica-Bold", 9)
            y_h = height - 75
            c_obj.drawString(35, y_h, "ER-Nr.")
            c_obj.drawString(95, y_h, "RE-Datum")
            c_obj.drawString(160, y_h, "Lieferant")
            c_obj.drawString(310, y_h, "Ext. RE-Nr.")
            c_obj.drawString(410, y_h, "Format")
            c_obj.drawRightString(520, y_h, "Netto")
            c_obj.drawRightString(585, y_h, "19% USt")
            c_obj.drawRightString(645, y_h, "7% USt")
            c_obj.drawRightString(720, y_h, "Brutto")
            c_obj.drawString(735, y_h, "VSt.")
            c_obj.drawString(768, y_h, "Beleg")
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

        sum_n = sum_19 = sum_7 = sum_b = Decimal("0.00")

        for r in rows:
            if y < 60:
                c_obj.showPage()
                page_num += 1
                y = draw_header()
                if is_final:
                    draw_footer()

            n = _d(r.get("Netto", "0"))
            m19 = _d(r.get("MwSt_19", "0"))
            m7 = _d(r.get("MwSt_7", "0"))
            b = _d(r.get("Brutto", "0"))
            sum_n += n
            sum_19 += m19
            sum_7 += m7
            sum_b += b

            c_obj.setFont("Helvetica", 8.5)
            c_obj.drawString(35, y, r.get("Interne ER-Nr.", ""))
            c_obj.drawString(95, y, r.get("Rechnungsdatum", ""))
            lief = r.get("Lieferant", "")
            c_obj.drawString(160, y, lief[:25] + "..." if len(lief) > 28 else lief)
            ext_nr = r.get("Externe Rechnungsnummer", "")
            c_obj.drawString(310, y, ext_nr[:16] + "..." if len(ext_nr) > 18 else ext_nr)
            c_obj.drawString(410, y, r.get("Format", "")[:10])
            c_obj.drawRightString(520, y, f"{_money(n)} €")
            c_obj.drawRightString(585, y, f"{_money(m19)} €")
            c_obj.drawRightString(645, y, f"{_money(m7)} €")
            c_obj.drawRightString(720, y, f"{_money(b)} €")
            c_obj.drawString(735, y, r.get("Vorsteuer geprüft", ""))

            arch_file = r.get("Archivdatei", "")
            if arch_file:
                c_obj.setFillColorRGB(0.12, 0.32, 0.55)
                c_obj.drawString(768, y, "Datei öffnen")
                c_obj.setFillColorRGB(0, 0, 0)
                if is_final:
                    file_url = "file:///" + os.path.abspath(arch_file).replace("\\", "/")
                    c_obj.linkURL(file_url, (766, y - 2, 818, y + 9), relative=0)

            y -= 15

        c_obj.line(35, y + 8, 815, y + 8)
        y -= 8
        c_obj.setFont("Helvetica-Bold", 9)
        c_obj.drawString(35, y, "GESAMTSUMMEN:")
        c_obj.drawRightString(520, y, f"{_money(sum_n)} €")
        c_obj.drawRightString(585, y, f"{_money(sum_19)} €")
        c_obj.drawRightString(645, y, f"{_money(sum_7)} €")
        c_obj.drawRightString(720, y, f"{_money(sum_b)} €")
        return page_num

    dummy = canvas.Canvas(BytesIO(), pagesize=landscape(A4))
    total_p = _render(dummy, is_final=False)
    c_final = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    _render(c_final, is_final=True, total_pages=total_p)
    c_final.save()
    return pdf_path
