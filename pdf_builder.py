"""
pdf_builder.py
--------------
Generierung des visuellen PDF-Dokuments (Rechnungslayout) mittels ReportLab.
"""
import html
import re
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from config import *
from utils import *
from crud import *


def _prepare_rich_text(text: str) -> str:
    """
    Wandelt HTML-Entities (inkl. &shy; und \u00ad) sowie <b>/<i>/<strong>/<em>
    in interne Formatmarker (~f/f~ und ~k/k~) um.
    """
    s = str(text or "")
    s = s.replace("&shy;", "\u00ad")
    s = html.unescape(s)
    s = s.replace("\u00ad", "")

    s = re.sub(r"<\s*b\s*>", "~f", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*/\s*b\s*>", "f~", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*strong\s*>", "~f", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*/\s*strong\s*>", "f~", s, flags=re.IGNORECASE)

    s = re.sub(r"<\s*i\s*>", "~k", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*/\s*i\s*>", "k~", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*em\s*>", "~k", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*/\s*em\s*>", "k~", s, flags=re.IGNORECASE)
    return s


def _font_for_state(is_bold: bool, is_italic: bool, base_font: str = "Helvetica") -> str:
    if base_font.startswith("Helvetica"):
        if is_bold and is_italic:
            return "Helvetica-BoldOblique"
        if is_bold:
            return "Helvetica-Bold"
        if is_italic:
            return "Helvetica-Oblique"
        return "Helvetica"
    return base_font


def _measure_formatted_width(c, text: str, size: float, base_font: str = "Helvetica") -> float:
    is_bold = False
    is_italic = False
    width = 0.0
    tokens = re.split(r"(~f|f~|~k|k~)", _prepare_rich_text(text))
    for tok in tokens:
        if tok == "~f":
            is_bold = True
        elif tok == "f~":
            is_bold = False
        elif tok == "~k":
            is_italic = True
        elif tok == "k~":
            is_italic = False
        elif tok:
            font = _font_for_state(is_bold, is_italic, base_font)
            width += c.stringWidth(tok, font, size)
    return width


def zeichne_blocksatz_zeile(c, x, y, text, width_limit, size=10, font="Helvetica"):
    """Zeichnet eine einzelne Textzeile im Blocksatz über die gegebene Breite."""
    c.setFont(font, size)
    woerter = text.split()
    if len(woerter) <= 1:
        c.drawString(x, y, text)
        return


def zeichne_formatierten_blocksatz_zeile(c, x, y, text, width_limit, size=10):
    """Zeichnet formatierten Text im Blocksatz."""
    prep = _prepare_rich_text(text)
    woerter = prep.split()
    if len(woerter) <= 1:
        zeichne_formatierten_text(c, x, y, prep, size, align="left")
        return

    woerter_breite = sum(_measure_formatted_width(c, w, size, "Helvetica") for w in woerter)
    gesamt_freiraum = width_limit - woerter_breite

    if gesamt_freiraum <= 0 or len(woerter) <= 1:
        zeichne_formatierten_text(c, x, y, prep, size, align="left")
        return

    extra_abstand = gesamt_freiraum / (len(woerter) - 1)
    current_x = x
    active_bold = False
    active_italic = False

    for wort in woerter:
        prefix = ("~f" if active_bold else "") + ("~k" if active_italic else "")
        zeichne_formatierten_text(c, current_x, y, prefix + wort, size, align="left")

        for tok in re.split(r"(~f|f~|~k|k~)", wort):
            if tok == "~f":
                active_bold = True
            elif tok == "f~":
                active_bold = False
            elif tok == "~k":
                active_italic = True
            elif tok == "k~":
                active_italic = False

        current_x += _measure_formatted_width(c, wort, size, "Helvetica") + extra_abstand


def zeichne_formatierten_text(c, x, y, text, size=10, align="left"):
    is_bold = False
    is_italic = False
    normalized_text = _prepare_rich_text(text)
    tokens = re.split(r"(~f|f~|~k|k~)", normalized_text)

    total_width = _measure_formatted_width(c, normalized_text, size, "Helvetica")

    if align == "center":
        current_x = (A4[0] / 2.0) - (total_width / 2.0)
    elif align == "right":
        current_x = x - total_width
    else:
        current_x = x

    is_bold = False
    is_italic = False
    for token in tokens:
        if token == "~f":
            is_bold = True
            continue
        if token == "f~":
            is_bold = False
            continue
        if token == "~k":
            is_italic = True
            continue
        if token == "k~":
            is_italic = False
            continue
        if not token:
            continue

        font = _font_for_state(is_bold, is_italic, "Helvetica")
        c.setFont(font, size)
        c.drawString(current_x, y, token)
        current_x += c.stringWidth(token, font, size)


def split_text_to_lines(text, width_limit, c, font="Helvetica", size=10):
    prep = _prepare_rich_text(text)
    words = prep.split()
    if not words:
        return [""]
    lines = []
    current_line = ""
    active_bold = False
    active_italic = False

    def _apply_word_state(w_str):
        nonlocal active_bold, active_italic
        for t in re.split(r"(~f|f~|~k|k~)", w_str):
            if t == "~f":
                active_bold = True
            elif t == "f~":
                active_bold = False
            elif t == "~k":
                active_italic = True
            elif t == "k~":
                active_italic = False

    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        if _measure_formatted_width(c, test_line, size, font) <= width_limit:
            current_line = test_line
            _apply_word_state(word)
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            _apply_word_state(word)
    if current_line:
        lines.append(current_line)
    return lines


def generiere_rechnung_text_pdf(
    firma,
    kopf,
    positionen,
    gesamt_netto,
    gesamt_steuer,
    gesamt_brutto,
    zusatztexte,
    gruss_text,
    header_text,
    einleitung_text,
    vor_gruss_text="",
    briefkopf_rechte_spalte=True,
):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    breite, hoehe = A4
    page_num = 1

    steuersaetze = set(safe_float(p.get("Steuersatz", 19.0)) for p in positionen)
    show_vat = (0.0 in steuersaetze) or (len(steuersaetze) > 1)

    x_lines = [90, 290, 345, 415, 475] if show_vat else [90, 305, 365, 450]

    def draw_table_header(y_pos):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(60, y_pos, "Pos.")
        c.drawString(100, y_pos, "Bezeichnung")
        if show_vat:
            c.drawRightString(330, y_pos, "Menge")
            c.drawRightString(400, y_pos, "EP Netto")
            c.drawRightString(460, y_pos, "USt.")
            c.drawRightString(530, y_pos, "Gesamt")
        else:
            c.drawRightString(360, y_pos, "Menge")
            c.drawRightString(440, y_pos, "Einzelpreis")
            c.drawRightString(530, y_pos, "Gesamt")

        y_top = y_pos + 10
        y_bot = y_pos - 5
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        c.line(60, y_bot, 530, y_bot)
        for x in x_lines:
            c.line(x, y_top, x, y_bot)
        c.setStrokeColorRGB(0, 0, 0)
        return y_bot - 13

    def check_page_break(y, req_height, draw_header=False):
        nonlocal page_num
        if y - req_height < 100:
            c.showPage()
            page_num += 1
            c.setFillColorRGB(1, 1, 1)
            c.rect(0, hoehe - 140, breite, 140, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 10)
            c.drawCentredString(breite / 2.0, hoehe - 50, f"- {page_num} -")

            new_y = hoehe - 120
            if draw_header:
                return draw_table_header(new_y)
            return new_y
        return y

    if str(firma.get("Falzmarken", "1")).lower() in ["true", "1", "ja", "yes"]:
        c.saveState()
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.line(0, hoehe - 421, 20, hoehe - 421)
        c.line(0, hoehe - 297.6, 10, hoehe - 297.6)
        c.line(0, hoehe - 595.3, 10, hoehe - 595.3)
        c.restoreState()

    c.setFont("Helvetica", 7)
    absender_name = (firma.get("Absenderzeile") or "").strip() or firma.get("FirmaName", "")
    absender_zeile = f"{absender_name}, {firma.get('Strasse','')}, {firma.get('PLZ','')} {firma.get('Ort','')}"
    while len(absender_zeile) > 10 and c.stringWidth(absender_zeile, "Helvetica", 7) > 235:
        absender_zeile = absender_zeile[:-4] + "..."
    c.drawString(60, hoehe - 130, absender_zeile)

    c.setFont("Helvetica", 9)
    y_adresse = hoehe - 145

    k_name = kopf.get("KundeName", "")
    name_lines = split_text_to_lines(k_name, 230, c, "Helvetica", 9)

    for zeile in name_lines:
        c.drawString(60, y_adresse, zeile)
        y_adresse -= 10

    c.drawString(60, y_adresse, kopf.get("KundeStrasse", ""))
    y_adresse -= 10

    c.drawString(60, y_adresse, f"{kopf.get('KundePLZ', '')} {kopf.get('KundeOrt', '')}")
    y_adresse -= 10

    if kopf.get("KundeLand", "") != "DE":
        c.drawString(60, y_adresse, kopf.get("KundeLand", ""))
        y_adresse -= 10

    y_tabelle = hoehe - 240

    if header_text:
        for zeile in header_text.split("\n"):
            zeichne_formatierten_text(c, 0, y_tabelle, zeile, 12, align="center")
            y_tabelle -= 18
        y_tabelle -= 10

    volle_kopf_breite = breite - 120
    max_kopf_breite = (volle_kopf_breite * (2.0 / 3.0)) if bool(briefkopf_rechte_spalte) else volle_kopf_breite

    r_nr = kopf.get("Rechnungsnummer", "")
    r_dat = formatiere_datum_lesbar(kopf.get("Rechnungsdatum", ""))
    f_dat = formatiere_datum_lesbar(kopf.get("Faelligkeitsdatum", ""))

    rech_zeile = f"Rechnung Nr.: {r_nr}  |  Datum: {r_dat}"
    for z_line in split_text_to_lines(rech_zeile, max_kopf_breite, c, "Helvetica-Bold", 11):
        zeichne_formatierten_text(c, 60, y_tabelle, f"~f{z_line}f~", 11, align="left")
        y_tabelle -= 13

    kdnr = kopf.get("KundeNr", "").strip()
    az = kopf.get("Aktenzeichen", "").strip()
    k_az_raw = kopf.get("KundeAktenzeichen", "").strip()
    k_az = "" if k_az_raw.lower() in ("-", "n/a") else k_az_raw
    lz = parse_lz_lesbar(kopf.get("LeistungszeitraumKopf", ""))

    teile_zeile1 = []
    if kdnr:
        teile_zeile1.append(f"Kunden-Nr.: {kdnr}")
    if az:
        teile_zeile1.append(f"Unser Zeichen: {az}")
    if k_az:
        teile_zeile1.append(f"Ihr Zeichen: {k_az}")

    str_zeile1 = " | ".join(teile_zeile1)
    str_lz = f"Leistungszeitraum: {lz}" if lz else ""

    str_komplett = str_zeile1
    if str_lz:
        str_komplett = f"{str_zeile1} | {str_lz}" if str_zeile1 else str_lz

    c.setFont("Helvetica", 10)
    if str_komplett:
        for z_line in split_text_to_lines(str_komplett, max_kopf_breite, c, "Helvetica", 10):
            c.drawString(60, y_tabelle, z_line)
            y_tabelle -= 12
        y_tabelle -= 5

    r_vermerk = kopf.get("Rechnungsvermerk", "").strip()
    if r_vermerk:
        for absatz in r_vermerk.split("\n"):
            for v_line in split_text_to_lines(absatz, 470, c, "Helvetica-Bold", 9.5):
                y_tabelle = check_page_break(y_tabelle, 14, False)
                zeichne_formatierten_text(c, 60, y_tabelle, f"~f{v_line}f~", 9.5, align="left")
                y_tabelle -= 12
        y_tabelle -= 5

    y_tabelle -= 5

    if einleitung_text:
        for absatz in einleitung_text.split("\n"):
            wrapped_lines = split_text_to_lines(absatz, 470, c, "Helvetica", 10)
            for idx, wrap_line in enumerate(wrapped_lines):
                y_tabelle = check_page_break(y_tabelle, 15, False)
                is_last = (idx == len(wrapped_lines) - 1)
                if is_last or len(wrap_line.split()) <= 1:
                    zeichne_formatierten_text(c, 60, y_tabelle, wrap_line, 10, align="left")
                else:
                    zeichne_formatierten_blocksatz_zeile(c, 60, y_tabelle, wrap_line, 470, 10)
                y_tabelle -= 12
        y_tabelle -= 10
    else:
        y_tabelle -= 10

    y_tabelle = check_page_break(y_tabelle, 20, False)
    y_tabelle = draw_table_header(y_tabelle)

    text_w = 180 if show_vat else 190
    line_height = 11

    for pos_index, pos in enumerate(positionen):
        menge = safe_float(pos["Menge"], 1.0)
        preis = safe_float(pos["EinzelpreisNetto"], 0.0)
        steuersatz_pos = safe_float(pos.get("Steuersatz", 19.0))

        einheit_raw = pos.get("Einheit", "C62").strip()
        einheit_codes = [c_item.strip() for c_item in re.findall(r"\(([^()]*)\)", einheit_raw) if len(c_item.strip()) >= 2]
        if einheit_codes:
            code = einheit_codes[-1]
        elif einheit_raw.lower() in ("monat", "monate", "monat(e)"):
            code = "MON"
        elif einheit_raw.lower() in ("tag", "tage", "tag(e)"):
            code = "DAY"
        elif einheit_raw.lower() in ("stunde", "stunden", "stunde(n)"):
            code = "HUR"
        else:
            code = einheit_raw
        einheit_lesbar = EINHEITEN_MAPPING.get(code, code)
        if code == "MON":
            einheit_lesbar = "Monat" if menge == 1 else "Monate"
        menge_str = f"{f_num(menge)} {einheit_lesbar}"

        bez_lines = split_text_to_lines(pos["Bezeichnung"], text_w, c, "Helvetica", 9)
        lz_pos_str = parse_lz_lesbar(pos.get("LeistungszeitraumPos", ""))

        req_height = (len(bez_lines) * line_height) + (12 if lz_pos_str else 0) + 12
        y_tabelle = check_page_break(y_tabelle, req_height, True)

        y_row_top = y_tabelle + 13

        c.setFont("Helvetica", 9)
        c.drawString(60, y_tabelle, str(pos["PosNr"]))

        if show_vat:
            c.drawRightString(330, y_tabelle, menge_str)
            c.drawRightString(400, y_tabelle, f_curr(preis))
            c.drawRightString(460, y_tabelle, f"{f_num(steuersatz_pos)}%")
            c.drawRightString(530, y_tabelle, f_curr(menge * preis))
        else:
            c.drawRightString(360, y_tabelle, menge_str)
            c.drawRightString(440, y_tabelle, f_curr(preis))
            c.drawRightString(530, y_tabelle, f_curr(menge * preis))

        for i, b_line in enumerate(bez_lines):
            zeichne_formatierten_text(c, 100, y_tabelle - (i * line_height), b_line, 9, align="left")

        y_bottom_of_text = y_tabelle - ((len(bez_lines) - 1) * line_height)

        if lz_pos_str:
            y_bottom_of_text -= 12
            zeichne_formatierten_text(c, 100, y_bottom_of_text, f"~kLeistungszeitraum: {lz_pos_str}k~", 8)

        y_row_bottom = y_bottom_of_text - 6

        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        for x in x_lines:
            c.line(x, y_row_top, x, y_row_bottom)

        if pos_index < len(positionen) - 1:
            c.line(60, y_row_bottom, 530, y_row_bottom)
            c.setStrokeColorRGB(0, 0, 0)
            y_tabelle = y_row_bottom - 13
        else:
            c.setStrokeColorRGB(0, 0, 0)
            y_tabelle = y_row_bottom - 5

    y_tabelle -= 6
    y_tabelle = check_page_break(y_tabelle, 80, False)
    y_totals_start = y_tabelle

    c.setFont("Helvetica", 10)
    c.line(380, y_tabelle + 10, 530, y_tabelle + 10)
    c.drawString(380, y_tabelle - 5, "Netto Gesamt:")
    c.drawRightString(530, y_tabelle - 5, f_curr(gesamt_netto))
    y_tabelle -= 12

    _, _, _, steuer_gruppen_netto = berechne_summen(positionen)
    steuer_gruppen = {satz: round_kaufm(n_sum * (satz / 100.0)) for satz, n_sum in steuer_gruppen_netto.items()}

    for satz, s_wert in sorted(steuer_gruppen.items()):
        c.drawString(380, y_tabelle - 5, f"zzgl. {f_num(satz)}% USt.:")
        c.drawRightString(530, y_tabelle - 5, f_curr(s_wert))
        y_tabelle -= 12

    c.setFont("Helvetica-Bold", 10)
    c.drawString(380, y_tabelle - 5, "Rechnungsbetrag:")
    c.drawRightString(530, y_tabelle - 5, f_curr(gesamt_brutto))
    y_tabelle -= 30

    show_girocode = str(firma.get("Girocode", "1")).lower() in ["true", "1", "ja", "yes"]
    iban = firma.get("IBAN", "")
    bic = firma.get("BIC", "")
    kontoinhaber = firma.get("Kontoinhaber", "")
    if iban and show_girocode:
        empfaenger = (kontoinhaber if kontoinhaber else firma.get("FirmaName", ""))[:70]
        betrag = f"{gesamt_brutto:.2f}"
        zweck_teile = []
        if r_nr.strip():
            zweck_teile.append(r_nr.strip())
        if r_dat.strip():
            zweck_teile.append(r_dat.strip())
        if az:
            zweck_teile.append(az)
        if kdnr:
            zweck_teile.append(kdnr)
        zweck = " ".join(zweck_teile).replace("\n", " ").replace("\r", "")[:140]
        epc_data = f"BCD\n002\n1\nSCT\n{bic}\n{empfaenger}\n{iban}\nEUR{betrag}\n\n\n{zweck}"
        try:
            import qrcode
            from reportlab.lib.utils import ImageReader

            qr_code = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=5,
                border=1,
            )
            qr_code.add_data(epc_data)
            qr_code.make(fit=True)
            qr_image = qr_code.make_image(fill_color="black", back_color="white").get_image()

            size = 65.0
            x_pos = 60
            y_pos = y_totals_start - size - 5
            c.setLineWidth(0.5)
            c.setStrokeColorRGB(0, 0, 0)
            box_x, box_y = x_pos - 3, y_pos - 3
            box_w, box_h = size + 48, size + 6
            c.roundRect(box_x, box_y, box_w, box_h, 4, stroke=1, fill=0)

            text_center_x = x_pos + size + 22
            mitte_y = y_pos + (size / 2.0)
            icon_x, icon_y = text_center_x - 6, mitte_y + 9
            c.roundRect(icon_x, icon_y, 12, 18, 2, stroke=1, fill=0)
            c.rect(icon_x + 2, icon_y + 3, 8, 12, stroke=1, fill=0)
            c.circle(text_center_x, icon_y + 16, 0.5, stroke=1, fill=1)
            c.setFont("Helvetica-Oblique", 7)
            c.drawCentredString(text_center_x, mitte_y - 1, "Scannen")
            c.drawCentredString(text_center_x, mitte_y - 9, "und")
            c.drawCentredString(text_center_x, mitte_y - 17, "Bezahlen")
            c.drawImage(ImageReader(qr_image), x_pos, y_pos, width=size, height=size, mask="auto")

            if y_tabelle > box_y - 15:
                y_tabelle = box_y - 15
        except ImportError:
            try:
                from reportlab.graphics.barcode.qr import QrCodeWidget
                from reportlab.graphics.shapes import Drawing
                from reportlab.graphics import renderPDF

                qr_code = QrCodeWidget(epc_data)
                qr_code.barLevel = "M"
                bounds = qr_code.getBounds()
                width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
                drawing = Drawing(width, height)
                drawing.add(qr_code)
                size = 65.0
                x_pos = 60
                y_pos = y_totals_start - size - 5
                c.setLineWidth(0.5)
                c.setStrokeColorRGB(0, 0, 0)
                box_x, box_y = x_pos - 3, y_pos - 3
                box_w, box_h = size + 48, size + 6
                c.roundRect(box_x, box_y, box_w, box_h, 4, stroke=1, fill=0)
                text_center_x = x_pos + size + 22
                mitte_y = y_pos + (size / 2.0)
                icon_x, icon_y = text_center_x - 6, mitte_y + 9
                c.roundRect(icon_x, icon_y, 12, 18, 2, stroke=1, fill=0)
                c.rect(icon_x + 2, icon_y + 3, 8, 12, stroke=1, fill=0)
                c.circle(text_center_x, icon_y + 16, 0.5, stroke=1, fill=1)
                c.setFont("Helvetica-Oblique", 7)
                c.drawCentredString(text_center_x, mitte_y - 1, "Scannen")
                c.drawCentredString(text_center_x, mitte_y - 9, "und")
                c.drawCentredString(text_center_x, mitte_y - 17, "Bezahlen")
                c.saveState()
                c.translate(x_pos, y_pos)
                c.scale(size / width if width else 1, size / height if height else 1)
                renderPDF.draw(drawing, c, 0, 0)
                c.restoreState()
                if y_tabelle > box_y - 15:
                    y_tabelle = box_y - 15
            except Exception:
                pass
        except Exception:
            pass

    if zusatztexte:
        for z in zusatztexte:
            raw_lines = z["text"].split("\n")
            wrapped_lines = []
            for rl in raw_lines:
                wrapped_lines.extend(split_text_to_lines(rl, 470, c, "Helvetica", 8.5))

            req_h = len(wrapped_lines) * 12 + (12 if z["pos"] != "0" else 0)
            y_tabelle = check_page_break(y_tabelle, req_h, False)

            if z["pos"] != "0":
                pos_str = z["pos"].strip()
                if "," in pos_str:
                    ueberschrift = f"Anmerkungen zu Positionen {pos_str}:"
                else:
                    ueberschrift = f"Anmerkung zu Position {pos_str}:"

                c.setFont("Helvetica-Bold", 8.5)
                c.drawString(60, y_tabelle, ueberschrift)
                y_tabelle -= 12

            for zeile in wrapped_lines:
                y_tabelle = check_page_break(y_tabelle, 12, False)
                zeichne_formatierten_text(c, 60, y_tabelle, zeile, 8.5)
                y_tabelle -= 12
            y_tabelle -= 5

    z_csv = kopf.get("Zusatztext", "").strip()
    if z_csv:
        raw_lines = z_csv.split("\\n")
        wrapped_lines = []
        for rl in raw_lines:
            wrapped_lines.extend(split_text_to_lines(rl, 470, c, "Helvetica", 10))

        y_tabelle = check_page_break(y_tabelle, len(wrapped_lines) * 15, False)
        for zeile in wrapped_lines:
            zeichne_formatierten_text(c, 60, y_tabelle, zeile, 10)
            y_tabelle -= 12
        y_tabelle -= 10

    y_tabelle -= 10
    y_tabelle = check_page_break(y_tabelle, 80, False)

    c.setFont("Helvetica", 10)
    if gesamt_brutto < 0:
        c.drawString(60, y_tabelle, "Dieser Beleg weist ein Guthaben zu Ihren Gunsten aus.")
        c.drawString(60, y_tabelle - 15, "Eine Zahlung Ihrerseits ist nicht erforderlich.")
        y_tabelle -= 45
    elif gesamt_brutto == 0:
        c.drawString(60, y_tabelle, "Der Rechnungsbetrag beläuft sich auf 0,00 €.")
        c.drawString(60, y_tabelle - 15, "Eine Zahlung Ihrerseits ist nicht erforderlich.")
        y_tabelle -= 45
    else:
        bank_name = firma.get("BankName", "")
        iban = firma.get("IBAN", "")
        bic = firma.get("BIC", "")
        kontoinhaber = firma.get("Kontoinhaber", "")
        is_raten = str(kopf.get("Ratenzahlung", "")).lower() in ["true", "1", "ja", "yes"]

        if is_raten:
            zahl_text = f"Bitte überweisen Sie bis zum {f_dat} unter Angabe der Rechnungsnummer auf folgendes Konto bei der {bank_name} oder nehmen Sie bis zu diesem Termin monatliche Ratenzahlungen auf."
        else:
            zahl_text = f"Bitte unter Angabe der Rechnungsnummer bis zum {f_dat} auf folgendes Konto bei der {bank_name} überweisen:"

        zahl_lines = split_text_to_lines(zahl_text, 470, c)

        for zl in zahl_lines:
            zeichne_formatierten_text(c, 60, y_tabelle, zl, 10)
            y_tabelle -= 12

        if kontoinhaber:
            kto_line = f"Kontoinhaber: {kontoinhaber}  |  IBAN: {iban}  |  BIC: {bic}"
            c.setFont("Helvetica", 10)
            if c.stringWidth(kto_line, "Helvetica", 10) <= 470:
                c.drawString(60, y_tabelle, kto_line)
                y_tabelle -= 12
            else:
                c.setFont("Helvetica", 8)
                if c.stringWidth(kto_line, "Helvetica", 8) <= 470:
                    c.drawString(60, y_tabelle, kto_line)
                    y_tabelle -= 12
                else:
                    c.setFont("Helvetica", 10)
                    c.drawString(60, y_tabelle, f"Kontoinhaber: {kontoinhaber}")
                    y_tabelle -= 12
                    c.drawString(60, y_tabelle, f"IBAN: {iban}  |  BIC: {bic}")
                    y_tabelle -= 12
        else:
            c.setFont("Helvetica", 10)
            c.drawString(60, y_tabelle, f"IBAN: {iban}  |  BIC: {bic}")
            y_tabelle -= 12

        c.setFont("Helvetica", 10)
        y_tabelle -= 10

    if vor_gruss_text:
        for absatz in vor_gruss_text.split("\n"):
            wrapped_lines = split_text_to_lines(absatz, 470, c, "Helvetica", 10)
            for idx, wrap_line in enumerate(wrapped_lines):
                y_tabelle = check_page_break(y_tabelle, 15, False)
                is_last = (idx == len(wrapped_lines) - 1)
                if is_last or len(wrap_line.split()) <= 1:
                    zeichne_formatierten_text(c, 60, y_tabelle, wrap_line, 10, align="left")
                else:
                    zeichne_formatierten_blocksatz_zeile(c, 60, y_tabelle, wrap_line, 470, 10)
                y_tabelle -= 12
        y_tabelle -= 10

    if gruss_text:
        raw_lines = gruss_text.split("\n")
        wrapped_lines = []
        for rl in raw_lines:
            wrapped_lines.extend(split_text_to_lines(rl, 470, c, "Helvetica", 10))

        y_tabelle = check_page_break(y_tabelle, len(wrapped_lines) * 15, False)
        for zeile in wrapped_lines:
            zeichne_formatierten_text(c, 60, y_tabelle, zeile, 10)
            y_tabelle -= 12

    c.save()
    packet.seek(0)
    return packet
