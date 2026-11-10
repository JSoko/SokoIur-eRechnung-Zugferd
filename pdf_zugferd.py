"""
pdf_zugferd.py
--------------
Generierungs-Engine für Rechnungen im ZUGFeRD- und XRechnung-Format.
Verwendet eine zentrale XML-Generierung nach EN 16931 (CII-Standard) für beide Formate.
"""
import os
import re
import csv
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, ArrayObject, StreamObject
from datenbank import *

def esc_xml(text):
    if text is None: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def clean_xml_text(text):
    text = re.sub(r'~f|f~|~k|k~', '', str(text))
    return esc_xml(text)

def zeichne_formatierten_text(c, x, y, text, size=10, align="left"):
    is_bold = False
    is_italic = False
    tokens = re.split(r'(~f|f~|~k|k~)', text)
    
    total_width = 0
    for token in tokens:
        if token in ('~f', 'f~', '~k', 'k~', ''): continue
        if is_bold and is_italic: font = "Helvetica-BoldOblique"
        elif is_bold: font = "Helvetica-Bold"
        elif is_italic: font = "Helvetica-Oblique"
        else: font = "Helvetica"
        total_width += c.stringWidth(token, font, size)
        
    if align == "center": current_x = (A4[0] / 2.0) - (total_width / 2.0)
    elif align == "right": current_x = x - total_width
    else: current_x = x
        
    is_bold = False
    is_italic = False
    for token in tokens:
        if token == '~f': is_bold = True; continue
        if token == 'f~': is_bold = False; continue
        if token == '~k': is_italic = True; continue
        if token == 'k~': is_italic = False; continue
        if not token: continue

        if is_bold and is_italic: font = "Helvetica-BoldOblique"
        elif is_bold: font = "Helvetica-Bold"
        elif is_italic: font = "Helvetica-Oblique"
        else: font = "Helvetica"

        c.setFont(font, size)
        c.drawString(current_x, y, token)
        current_x += c.stringWidth(token, font, size)

def split_text_to_lines(text, width_limit, c, font="Helvetica", size=10):
    c.setFont(font, size)
    words = str(text).split()
    if not words: return [""]
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font, size) <= width_limit:
            current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    return lines

def generiere_rechnung_text_pdf(firma, kopf, positionen, gesamt_netto, gesamt_steuer, gesamt_brutto, zusatztexte, gruss_text, header_text, einleitung_text):
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    breite, hoehe = A4
    page_num = 1
    
    steuersaetze = set(safe_float(p.get('Steuersatz', 19.0)) for p in positionen)
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
    
    
    if str(firma.get('Falzmarken', '1')).lower() in ['true', '1', 'ja', 'yes']:
        c.saveState()
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.5, 0.5, 0.5)  # Dezentes Grau
        
        # Lochmarke (Mitte bei exakt 148,5 mm = 421 pt)
        c.line(0, hoehe - 421, 20, hoehe - 421)
        
        # Obere Falzmarke (105 mm = 297,6 pt)
        c.line(0, hoehe - 297.6, 10, hoehe - 297.6)
        
        # Untere Falzmarke (210 mm = 595,3 pt)
        c.line(0, hoehe - 595.3, 10, hoehe - 595.3)
        c.restoreState()
        
    c.setFont("Helvetica", 7)
    c.drawString(60, hoehe - 130, f"{firma.get('FirmaName','')}, {firma.get('Strasse','')}, {firma.get('PLZ','')} {firma.get('Ort','')}")
    
    c.setFont("Helvetica", 9)
    y_adresse = hoehe - 145
    
    # 1. Kundenname umbrechen, falls er nicht ins Sichtfenster (max. 230 pt) passt
    k_name = kopf.get('KundeName', '')
    name_lines = split_text_to_lines(k_name, 230, c, "Helvetica", 9)
    
    for zeile in name_lines:
        c.drawString(60, y_adresse, zeile)
        y_adresse -= 10  # Sehr kompakter Zeilenabstand (1,1-fach)
        
    # 2. Restliche Adresse mit demselben kompakten Abstand anhängen
    c.drawString(60, y_adresse, kopf.get('KundeStrasse', ''))
    y_adresse -= 10
    
    c.drawString(60, y_adresse, f"{kopf.get('KundePLZ', '')} {kopf.get('KundeOrt', '')}")
    y_adresse -= 10
    
    if kopf.get('KundeLand', '') != 'DE': 
        c.drawString(60, y_adresse, kopf.get('KundeLand', ''))
        y_adresse -= 10
        
    y_tabelle = hoehe - 240
    
    if header_text:
        for zeile in header_text.split('\n'):
            zeichne_formatierten_text(c, 0, y_tabelle, zeile, 12, align="center")
            y_tabelle -= 18
        y_tabelle -= 10
    
    r_nr = kopf.get('Rechnungsnummer','')
    r_dat = formatiere_datum_lesbar(kopf.get('Rechnungsdatum',''))
    f_dat = formatiere_datum_lesbar(kopf.get('Faelligkeitsdatum',''))
    
    rech_zeile = f"Rechnung Nr.: {r_nr}  |  Datum: {r_dat}  |  Fällig bis: {f_dat}"
    zeichne_formatierten_text(c, 60, y_tabelle, f"~f{rech_zeile}f~", 11, align="left")
    y_tabelle -= 12
    
    kdnr = kopf.get('KundeNr', '').strip()
    az = kopf.get('Aktenzeichen', '').strip()
    k_az = kopf.get('KundeAktenzeichen', '').strip()
    lz = parse_lz_lesbar(kopf.get('LeistungszeitraumKopf', ''))

    teile_zeile1 = []
    if kdnr: teile_zeile1.append(f"Kunden-Nr.: {kdnr}")
    if az: teile_zeile1.append(f"Unser Zeichen: {az}")
    if k_az: teile_zeile1.append(f"Ihr Zeichen: {k_az}")
    
    str_zeile1 = " | ".join(teile_zeile1)
    str_lz = f"Leistungszeitraum: {lz}" if lz else ""
    
    str_komplett = str_zeile1
    if str_lz:
        str_komplett = f"{str_zeile1} | {str_lz}" if str_zeile1 else str_lz
        
    c.setFont("Helvetica", 10)
    if str_zeile1 and str_lz and c.stringWidth(str_komplett, "Helvetica", 10) > 400:
        c.drawString(60, y_tabelle, str_zeile1)
        y_tabelle -= 12
        c.drawString(60, y_tabelle, str_lz)
        y_tabelle -= 12
    else:
        if str_komplett:
            c.drawString(60, y_tabelle, str_komplett)
            y_tabelle -= 12
            
    if str_komplett: y_tabelle -= 5
    y_tabelle -= 5
    
    if einleitung_text:
        for zeile in einleitung_text.split('\n'):
            y_tabelle = check_page_break(y_tabelle, 15, False)
            zeichne_formatierten_text(c, 60, y_tabelle, zeile, 10, align="left")
            y_tabelle -= 12
        y_tabelle -= 10
    else: y_tabelle -= 10

    y_tabelle = check_page_break(y_tabelle, 20, False)
    y_tabelle = draw_table_header(y_tabelle)
    
    text_w = 180 if show_vat else 190
    line_height = 11 
    
    for pos_index, pos in enumerate(positionen):
        menge = safe_float(pos['Menge'], 1.0)
        preis = safe_float(pos['EinzelpreisNetto'], 0.0)
        steuersatz_pos = safe_float(pos.get('Steuersatz', 19.0))
        
        einheit_raw = pos.get('Einheit', 'C62').strip()
        einheit_codes = re.findall(r'\(([^()]*)\)', einheit_raw)
        code = einheit_codes[-1].strip() if einheit_codes else einheit_raw
        einheit_lesbar = EINHEITEN_MAPPING.get(code, code)
        menge_str = f"{f_num(menge)} {einheit_lesbar}"
        
        bez_lines = split_text_to_lines(pos['Bezeichnung'], text_w, c, "Helvetica", 9)
        lz_pos_str = parse_lz_lesbar(pos.get('LeistungszeitraumPos', ''))
        
        req_height = (len(bez_lines) * line_height) + (12 if lz_pos_str else 0) + 12
        y_tabelle = check_page_break(y_tabelle, req_height, True)
        
        y_row_top = y_tabelle + 13
        
        c.setFont("Helvetica", 9)
        c.drawString(60, y_tabelle, str(pos['PosNr']))
        
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
            c.drawString(100, y_tabelle - (i * line_height), b_line)
            
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
    
    steuer_gruppen = {}
    for pos in positionen:
        satz = safe_float(pos.get('Steuersatz', 19.0))
        st = safe_float(pos['Menge'], 1.0) * safe_float(pos['EinzelpreisNetto'], 0.0) * (satz / 100.0)
        if satz > 0:
            if satz not in steuer_gruppen: steuer_gruppen[satz] = 0.0
            steuer_gruppen[satz] += st
            
    for satz, s_wert in sorted(steuer_gruppen.items()):
        c.drawString(380, y_tabelle - 5, f"zzgl. {f_num(satz)}% USt.:")
        c.drawRightString(530, y_tabelle - 5, f_curr(s_wert))
        y_tabelle -= 12
        
    c.setFont("Helvetica-Bold", 10)
    c.drawString(380, y_tabelle - 5, "Rechnungsbetrag:")
    c.drawRightString(530, y_tabelle - 5, f_curr(gesamt_brutto))
    y_tabelle -= 30
    
    show_girocode = str(firma.get('Girocode', '1')).lower() in ['true', '1', 'ja', 'yes']
    iban = firma.get('IBAN', '')
    bic = firma.get('BIC', '')
    kontoinhaber = firma.get('Kontoinhaber', '')
    if iban and show_girocode:
        # Kein Import aus reportlab.graphics.barcode: Einige schlanke ReportLab-
        # Installationen enthalten code128 nicht, obwohl ein QR-Code benötigt wird.
        empfaenger = (kontoinhaber if kontoinhaber else firma.get('FirmaName', ''))[:70]
        betrag = f"{gesamt_brutto:.2f}"
        zweck_teile = []
        if r_nr.strip(): zweck_teile.append(r_nr.strip())
        if r_dat.strip(): zweck_teile.append(r_dat.strip())
        if az: zweck_teile.append(az)
        if kdnr: zweck_teile.append(kdnr)
        zweck = " ".join(zweck_teile).replace('\n', ' ').replace('\r', '')[:140]
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
            c.drawImage(ImageReader(qr_image), x_pos, y_pos, width=size, height=size, mask='auto')

            if y_tabelle > box_y - 15:
                y_tabelle = box_y - 15
        except ImportError:
            # Fallback für schlanke Installationen ohne das externe Paket
            # „qrcode“. Direkter Import des QR-Moduls vermeidet die in manchen
            # ReportLab-Bundles fehlenden linearen Barcode-Module (z. B. code128).
            try:
                from reportlab.graphics.barcode.qr import QrCodeWidget
                from reportlab.graphics.shapes import Drawing
                from reportlab.graphics import renderPDF

                qr_code = QrCodeWidget(epc_data)
                qr_code.barLevel = 'M'
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
            except Exception as e:
                print(f"Girocode konnte nicht erstellt werden: {e}")
        except Exception as e:
            print(f"Girocode konnte nicht erstellt werden: {e}")

    
    if zusatztexte:
        for z in zusatztexte:
            lines = z['text'].split('\n')
            req_h = len(lines) * 13 + (12 if z['pos'] != '0' else 0)
            y_tabelle = check_page_break(y_tabelle, req_h, False)
            
            if z['pos'] != '0': 
                pos_str = z['pos'].strip()
                # Unterscheidung ob eine oder mehrere Positionen
                if "," in pos_str:
                    ueberschrift = f"Anmerkungen zu Positionen {pos_str}:"
                else:
                    ueberschrift = f"Anmerkung zu Position {pos_str}:"
                
                # Kleinere Schriftgröße für die Überschrift (8.5 pt fett)
                c.setFont("Helvetica-Bold", 8.5)
                c.drawString(60, y_tabelle, ueberschrift)
                y_tabelle -= 12
                
            for zeile in lines:
                # Kleinere Schriftgröße für den Text (8.5 pt normal) und etwas engerer Zeilenabstand (12 statt 15)
                zeichne_formatierten_text(c, 60, y_tabelle, zeile, 8.5)
                y_tabelle -= 12
            y_tabelle -= 5

    z_csv = kopf.get('Zusatztext', '').strip()
    if z_csv:
        lines = z_csv.split('\\n')
        y_tabelle = check_page_break(y_tabelle, len(lines) * 15, False)
        for zeile in lines:
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
        bank_name = firma.get('BankName', '')
        iban = firma.get('IBAN', '')
        bic = firma.get('BIC', '')
        kontoinhaber = firma.get('Kontoinhaber', '')
        is_raten = str(kopf.get('Ratenzahlung', '')).lower() in ['true', '1', 'ja', 'yes']
        
        if is_raten:
            zahl_text = f"Bitte überweisen Sie bis zum {f_dat} auf folgendes Konto bei der {bank_name} oder nehmen Sie bis zu diesem Termin monatliche Ratenzahlungen auf."
        else:
            zahl_text = f"Bitte überweisen Sie bis zum {f_dat} auf folgendes Konto bei der {bank_name}:"
            
        zahl_lines = split_text_to_lines(zahl_text, 470, c)
        
        for zl in zahl_lines:
            c.drawString(60, y_tabelle, zl)
            y_tabelle -= 12
            
        # --- NEU: Intelligente Bankdaten-Formatierung (Normal -> Kleiner Font -> Umbruch) ---
        if kontoinhaber:
            kto_line = f"Kontoinhaber: {kontoinhaber}  |  IBAN: {iban}  |  BIC: {bic}"
            
            # Versuch 1: Passt es in Standardfont (10 pt)?
            c.setFont("Helvetica", 10)
            if c.stringWidth(kto_line, "Helvetica", 10) <= 470:
                c.drawString(60, y_tabelle, kto_line)
                y_tabelle -= 12
            else:
                # Versuch 2: Passt es in kleinerem Font (8 pt) in eine Zeile?
                c.setFont("Helvetica", 8)
                if c.stringWidth(kto_line, "Helvetica", 8) <= 470:
                    c.drawString(60, y_tabelle, kto_line)
                    y_tabelle -= 12
                else:
                    # Versuch 3: Passt auch mit kleinerem Font nicht -> Zeilenumbruch vor IBAN im Standardfont (10 pt)
                    c.setFont("Helvetica", 10)
                    c.drawString(60, y_tabelle, f"Kontoinhaber: {kontoinhaber}")
                    y_tabelle -= 12
                    c.drawString(60, y_tabelle, f"IBAN: {iban}  |  BIC: {bic}")
                    y_tabelle -= 12
        else:
            c.setFont("Helvetica", 10)
            c.drawString(60, y_tabelle, f"IBAN: {iban}  |  BIC: {bic}")
            y_tabelle -= 12
            
        c.setFont("Helvetica", 10)  # Zurück auf Standard für nachfolgende Texte
        y_tabelle -= 10
              
    
    y_vor_gruss = y_tabelle
    
    if gruss_text:
        lines = gruss_text.split('\n')
        y_tabelle = check_page_break(y_tabelle, len(lines) * 15, False)
        y_vor_gruss = y_tabelle
        for zeile in lines:
            zeichne_formatierten_text(c, 60, y_tabelle, zeile, 10)
            y_tabelle -= 12
    c.save()
    packet.seek(0)
    return packet

def generiere_en16931_xml(firma, kopf, positionen, zusatztexte, gruss_text, header_text, einleitung_text):
    """Zentrale, gemeinsame Hilfsfunktion für die EN 16931 konforme CII-XML-Erstellung."""
    r_nr = kopf.get('Rechnungsnummer', '')
    kunde_name_xml = esc_xml(kopf.get('KundeName', '').strip())
    if not kunde_name_xml: kunde_name_xml = "Nicht angegeben"
    
    r_datum, f_datum = formatiere_datum(kopf.get('Rechnungsdatum', '')), formatiere_datum(kopf.get('Faelligkeitsdatum', ''))
    iban_clean = re.sub(r'\s+', '', firma.get('IBAN', ''))
    bic_clean = re.sub(r'\s+', '', firma.get('BIC', ''))
    
    gesamt_netto = gesamt_steuer = 0.0
    xml_positionen = ""
    steuer_gruppen = {}
    
    for pos in positionen:
        menge = safe_float(pos['Menge'], 1.0)
        preis = safe_float(pos['EinzelpreisNetto'], 0.0)
        steuersatz = safe_float(pos.get('Steuersatz', 19.0), 19.0)
        
        pos_netto = menge * preis
        pos_steuer = pos_netto * (steuersatz / 100.0)
        gesamt_netto += pos_netto
        gesamt_steuer += pos_steuer
        
        if steuersatz not in steuer_gruppen: steuer_gruppen[steuersatz] = {'netto': 0.0, 'steuer': 0.0}
        steuer_gruppen[steuersatz]['netto'] += pos_netto
        steuer_gruppen[steuersatz]['steuer'] += pos_steuer
        
        einheit_raw = str(pos.get('Einheit', 'C62')).strip()
        # Bei Anzeigen wie „Stunde(n) (HUR)“ ist der letzte Klammerwert der
        # UN/ECE-Einheitencode; der erste („n“) wäre unzulässig.
        einheit_codes = re.findall(r'\(([^()]*)\)', einheit_raw)
        einheit_code = einheit_codes[-1].strip() if einheit_codes else einheit_raw
        if not einheit_code.isalnum(): einheit_code = "C62"
        
        cat_code = "S" if steuersatz > 0 else "E"
        
        if preis < 0:
            preis_xml = abs(preis)
            menge_xml = pos_netto / preis_xml if preis_xml != 0 else 0.0
        else:
            preis_xml = preis
            menge_xml = menge
        
        lz_pos_raw = pos.get('LeistungszeitraumPos', '').strip()
        xml_billing_period_pos = ""
        if lz_pos_raw:
            if "|" in lz_pos_raw:
                start_d, end_d = lz_pos_raw.split('|')
                xml_billing_period_pos = f"""
                <ram:BillingSpecifiedPeriod>
                    <ram:StartDateTime><udt:DateTimeString format="102">{formatiere_datum(start_d)}</udt:DateTimeString></ram:StartDateTime>
                    <ram:EndDateTime><udt:DateTimeString format="102">{formatiere_datum(end_d)}</udt:DateTimeString></ram:EndDateTime>
                </ram:BillingSpecifiedPeriod>"""
            else:
                s_date = formatiere_datum(lz_pos_raw)
                xml_billing_period_pos = f"""
                <ram:BillingSpecifiedPeriod>
                    <ram:StartDateTime><udt:DateTimeString format="102">{s_date}</udt:DateTimeString></ram:StartDateTime>
                    <ram:EndDateTime><udt:DateTimeString format="102">{s_date}</udt:DateTimeString></ram:EndDateTime>
                </ram:BillingSpecifiedPeriod>"""
        
        xml_positionen += f"""
        <ram:IncludedSupplyChainTradeLineItem>
            <ram:AssociatedDocumentLineDocument>
                <ram:LineID>{esc_xml(pos.get('PosNr', ''))}</ram:LineID>
            </ram:AssociatedDocumentLineDocument>
            <ram:SpecifiedTradeProduct>
                <ram:Name>{esc_xml(pos.get('Bezeichnung', ''))}</ram:Name>
            </ram:SpecifiedTradeProduct>
            <ram:SpecifiedLineTradeAgreement>
                <ram:NetPriceProductTradePrice>
                    <ram:ChargeAmount>{preis_xml:.2f}</ram:ChargeAmount>
                </ram:NetPriceProductTradePrice>
            </ram:SpecifiedLineTradeAgreement>
            <ram:SpecifiedLineTradeDelivery>
                <ram:BilledQuantity unitCode="{esc_xml(einheit_code)}">{menge_xml:.2f}</ram:BilledQuantity>
            </ram:SpecifiedLineTradeDelivery>
            <ram:SpecifiedLineTradeSettlement>
                <ram:ApplicableTradeTax>
                    <ram:TypeCode>VAT</ram:TypeCode>
                    <ram:CategoryCode>{cat_code}</ram:CategoryCode>
                    <ram:RateApplicablePercent>{steuersatz:.2f}</ram:RateApplicablePercent>
                </ram:ApplicableTradeTax>
                {xml_billing_period_pos}
                <ram:SpecifiedTradeSettlementLineMonetarySummation>
                    <ram:LineTotalAmount>{pos_netto:.2f}</ram:LineTotalAmount>
                </ram:SpecifiedTradeSettlementLineMonetarySummation>
            </ram:SpecifiedLineTradeSettlement>
        </ram:IncludedSupplyChainTradeLineItem>"""

    gesamt_brutto = gesamt_netto + gesamt_steuer

    xml_tax_totals = ""
    for satz, werte in steuer_gruppen.items():
        cat_code = "S" if satz > 0 else "E"
        xml_tax_totals += f"""
            <ram:ApplicableTradeTax>
                <ram:CalculatedAmount>{werte['steuer']:.2f}</ram:CalculatedAmount>
                <ram:TypeCode>VAT</ram:TypeCode>
                <ram:BasisAmount>{werte['netto']:.2f}</ram:BasisAmount>
                <ram:CategoryCode>{cat_code}</ram:CategoryCode>
                <ram:RateApplicablePercent>{satz:.2f}</ram:RateApplicablePercent>
            </ram:ApplicableTradeTax>"""
            
    lz_kopf = kopf.get('LeistungszeitraumKopf', '').strip()
    xml_delivery_event = ""
    xml_billing_period_header = ""

    if lz_kopf:
        if "|" in lz_kopf:
            start_d, end_d = lz_kopf.split('|')
            xml_billing_period_header = f"""
            <ram:BillingSpecifiedPeriod>
                <ram:StartDateTime><udt:DateTimeString format="102">{formatiere_datum(start_d)}</udt:DateTimeString></ram:StartDateTime>
                <ram:EndDateTime><udt:DateTimeString format="102">{formatiere_datum(end_d)}</udt:DateTimeString></ram:EndDateTime>
            </ram:BillingSpecifiedPeriod>"""
            xml_delivery_event = f"""<ram:ActualDeliverySupplyChainEvent><ram:OccurrenceDateTime><udt:DateTimeString format="102">{r_datum}</udt:DateTimeString></ram:OccurrenceDateTime></ram:ActualDeliverySupplyChainEvent>"""
        else:
            deliv_d_xml = formatiere_datum(lz_kopf)
            xml_delivery_event = f"""<ram:ActualDeliverySupplyChainEvent><ram:OccurrenceDateTime><udt:DateTimeString format="102">{deliv_d_xml}</udt:DateTimeString></ram:OccurrenceDateTime></ram:ActualDeliverySupplyChainEvent>"""
    else:
        xml_delivery_event = f"""<ram:ActualDeliverySupplyChainEvent><ram:OccurrenceDateTime><udt:DateTimeString format="102">{r_datum}</udt:DateTimeString></ram:OccurrenceDateTime></ram:ActualDeliverySupplyChainEvent>"""
    
    xml_notes_str = ""
    if kopf.get('Aktenzeichen', '').strip(): 
        xml_notes_str += f"<ram:IncludedNote><ram:Content>Unser Zeichen: {clean_xml_text(kopf.get('Aktenzeichen', ''))}</ram:Content></ram:IncludedNote>\n"
    if header_text: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(header_text)}</ram:Content></ram:IncludedNote>\n"
    if einleitung_text: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(einleitung_text)}</ram:Content></ram:IncludedNote>\n"
    for z in zusatztexte:
        pre = f"Zu Position(en) {z['pos']}:\n" if z['pos'] != '0' else ""
        xml_notes_str += f"<ram:IncludedNote><ram:Content>{pre}{clean_xml_text(z['text'])}</ram:Content></ram:IncludedNote>\n"
    z_csv = kopf.get('Zusatztext', '').strip()
    if z_csv: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(z_csv.replace('\\n', '\n'))}</ram:Content></ram:IncludedNote>\n"
    if gruss_text: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(gruss_text)}</ram:Content></ram:IncludedNote>\n"
    
    z_bed = kopf.get('Zahlungsbedingungen', '').strip()
    xml_payment_terms = f"<ram:Description>{clean_xml_text(z_bed)}</ram:Description>" if z_bed else ""
    
    r_vermerk = kopf.get('Rechnungsvermerk', '').strip()
    if r_vermerk:
        xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(r_vermerk)}</ram:Content><ram:SubjectCode>REG</ram:SubjectCode></ram:IncludedNote>\n"
    
    xml_buyer_ref = f"<ram:BuyerReference>{esc_xml(kopf.get('KundeAktenzeichen', '').strip())}</ram:BuyerReference>" if kopf.get('KundeAktenzeichen', '').strip() else ""
    xml_buyer_id = f"<ram:ID>{esc_xml(kopf.get('KundeNr', '').strip())}</ram:ID>" if kopf.get('KundeNr', '').strip() else ""

    # XRechnung 3.0: BT-24 (Spezifikationskennung) und BT-23 (Geschäftsprozess).
    # Der Prozesswert ist der für die europäische EN-16931-Rechnung verwendete
    # Peppol-Billing-Prozess; die Spezifikationskennung selbst ist XRechnung.
    xrechnung_specification_id = "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"
    business_process_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

    # BR-DE-2: Verkäuferkontakt (BG-6). Als Kontaktbezeichnung wird ein
    # ausdrücklich gepflegter Ansprechpartner verwendet, sonst der Firmenname.
    seller_contact_name = firma.get('Ansprechpartner', '').strip() or firma.get('FirmaName', '').strip()
    seller_email = firma.get('Email', '').strip()
    seller_phone = firma.get('Telefon', '').strip()
    xml_seller_contact = f"<ram:DefinedTradeContact><ram:PersonName>{esc_xml(seller_contact_name)}</ram:PersonName>"
    if seller_phone:
        xml_seller_contact += f"<ram:TelephoneUniversalCommunication><ram:CompleteNumber>{esc_xml(seller_phone)}</ram:CompleteNumber></ram:TelephoneUniversalCommunication>"
    if seller_email:
        xml_seller_contact += f"<ram:EmailURIUniversalCommunication><ram:URIID>{esc_xml(seller_email)}</ram:URIID></ram:EmailURIUniversalCommunication>"
    xml_seller_contact += "</ram:DefinedTradeContact>"

    # Elektronische Adressen (BT-34/BT-49). E-Mail ist der Standardfall;
    # bei öffentlichen Auftraggebern kann alternativ eine Leitweg-ID in
    # KundeEndpoint samt KundeEndpointScheme (regelmäßig 0204) übergeben werden.
    seller_endpoint = seller_email
    seller_endpoint_scheme = firma.get('EndpointScheme', '').strip() or ('EM' if seller_endpoint else '')
    buyer_endpoint = kopf.get('KundeEndpoint', '').strip() or kopf.get('KundeEmail', '').strip()
    buyer_endpoint_scheme = kopf.get('KundeEndpointScheme', '').strip() or ('EM' if buyer_endpoint and '@' in buyer_endpoint else '')
    xml_seller_endpoint = (f'<ram:URIUniversalCommunication><ram:URIID schemeID="{esc_xml(seller_endpoint_scheme)}">{esc_xml(seller_endpoint)}</ram:URIID></ram:URIUniversalCommunication>' if seller_endpoint and seller_endpoint_scheme else '')
    xml_buyer_endpoint = (f'<ram:URIUniversalCommunication><ram:URIID schemeID="{esc_xml(buyer_endpoint_scheme)}">{esc_xml(buyer_endpoint)}</ram:URIID></ram:URIUniversalCommunication>' if buyer_endpoint and buyer_endpoint_scheme else '')
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
    <rsm:ExchangedDocumentContext>
        <ram:BusinessProcessSpecifiedDocumentContextParameter><ram:ID>{business_process_id}</ram:ID></ram:BusinessProcessSpecifiedDocumentContextParameter>
        <ram:GuidelineSpecifiedDocumentContextParameter><ram:ID>{xrechnung_specification_id}</ram:ID></ram:GuidelineSpecifiedDocumentContextParameter>
    </rsm:ExchangedDocumentContext>
    <rsm:ExchangedDocument><ram:ID>{esc_xml(r_nr)}</ram:ID><ram:TypeCode>380</ram:TypeCode><ram:IssueDateTime><udt:DateTimeString format="102">{r_datum}</udt:DateTimeString></ram:IssueDateTime>{xml_notes_str.strip()}</rsm:ExchangedDocument>
    <rsm:SupplyChainTradeTransaction>
        {xml_positionen}
        <ram:ApplicableHeaderTradeAgreement>
            {xml_buyer_ref}
            <ram:SellerTradeParty>
                <ram:Name>{esc_xml(firma.get('FirmaName', ''))}</ram:Name>
                {xml_seller_contact}
                <ram:PostalTradeAddress><ram:PostcodeCode>{esc_xml(firma.get('PLZ', ''))}</ram:PostcodeCode><ram:LineOne>{esc_xml(firma.get('Strasse', ''))}</ram:LineOne><ram:CityName>{esc_xml(firma.get('Ort', ''))}</ram:CityName><ram:CountryID>{esc_xml(firma.get('Land', 'DE'))}</ram:CountryID></ram:PostalTradeAddress>
                {xml_seller_endpoint}
                <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">{esc_xml(firma.get('UStId', ''))}</ram:ID></ram:SpecifiedTaxRegistration>
            </ram:SellerTradeParty>
            <ram:BuyerTradeParty>
                {xml_buyer_id}
                <ram:Name>{kunde_name_xml}</ram:Name>
                <ram:PostalTradeAddress><ram:PostcodeCode>{esc_xml(kopf.get('KundePLZ',''))}</ram:PostcodeCode><ram:LineOne>{esc_xml(kopf.get('KundeStrasse',''))}</ram:LineOne><ram:CityName>{esc_xml(kopf.get('KundeOrt',''))}</ram:CityName><ram:CountryID>{esc_xml(kopf.get('KundeLand','DE'))}</ram:CountryID></ram:PostalTradeAddress>
                {xml_buyer_endpoint}
            </ram:BuyerTradeParty>
        </ram:ApplicableHeaderTradeAgreement>
        <ram:ApplicableHeaderTradeDelivery>
            {xml_delivery_event}
        </ram:ApplicableHeaderTradeDelivery>
        <ram:ApplicableHeaderTradeSettlement>
            <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
            <ram:SpecifiedTradeSettlementPaymentMeans>
                <ram:TypeCode>58</ram:TypeCode>
                <ram:PayeePartyCreditorFinancialAccount><ram:IBANID>{esc_xml(iban_clean)}</ram:IBANID></ram:PayeePartyCreditorFinancialAccount>
                <ram:PayeeSpecifiedCreditorFinancialInstitution><ram:BICID>{esc_xml(bic_clean)}</ram:BICID></ram:PayeeSpecifiedCreditorFinancialInstitution>
            </ram:SpecifiedTradeSettlementPaymentMeans>
            {xml_tax_totals}
            {xml_billing_period_header}
            <ram:SpecifiedTradePaymentTerms>
                {xml_payment_terms}
                <ram:DueDateDateTime><udt:DateTimeString format="102">{f_datum}</udt:DateTimeString></ram:DueDateDateTime>
            </ram:SpecifiedTradePaymentTerms>
            <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                <ram:LineTotalAmount>{gesamt_netto:.2f}</ram:LineTotalAmount><ram:TaxBasisTotalAmount>{gesamt_netto:.2f}</ram:TaxBasisTotalAmount>
                <ram:TaxTotalAmount currencyID="EUR">{gesamt_steuer:.2f}</ram:TaxTotalAmount><ram:GrandTotalAmount>{gesamt_brutto:.2f}</ram:GrandTotalAmount><ram:DuePayableAmount>{gesamt_brutto:.2f}</ram:DuePayableAmount>
            </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        </ram:ApplicableHeaderTradeSettlement>
    </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>"""

def erstelle_xrechnung(firma, rechnung_daten, brief_pfad, zusatztexte, gruss_text, header_text, einleitung_text, ausgabe_ordner, auswertungen_ordner, rechnungsjahr):
    kopf, positionen = rechnung_daten['kopf'], rechnung_daten['positionen']
    r_nr = kopf.get('Rechnungsnummer', '')
    
    # 1. XML über die gemeinsame Funktion generieren
    xml_content = generiere_en16931_xml(firma, kopf, positionen, zusatztexte, gruss_text, header_text, einleitung_text)
    
    # 2. Begleit-PDF mit rechtlichem Hinweis generieren
    hinweis_text = "~kHinweis: Dies ist eine Begleitdatei zur XRechnungsdatei und maßgeblich ist die X-Rechnungsdatei.k~"
    gruss_erweitert = f"{gruss_text}\n\n{hinweis_text}" if gruss_text else hinweis_text

    # Summen für den PDF-Aufbau ermitteln
    netto = sum(safe_float(p['Menge'], 1.0) * safe_float(p['EinzelpreisNetto'], 0.0) for p in positionen)
    steuer = sum(safe_float(p['Menge'], 1.0) * safe_float(p['EinzelpreisNetto'], 0.0) * (safe_float(p.get('Steuersatz', 19.0), 19.0)/100.0) for p in positionen)
    brutto = netto + steuer

    text_pdf_stream = generiere_rechnung_text_pdf(firma, kopf, positionen, netto, steuer, brutto, zusatztexte, gruss_erweitert, header_text, einleitung_text)
    text_pdf = PdfReader(text_pdf_stream)
    writer = PdfWriter()
    writer._header = b"%PDF-1.7"
    
    try:
        briefbogen_pfad = brief_pfad if os.path.exists(brief_pfad) else None
        if briefbogen_pfad:
            brief_reader = PdfReader(briefbogen_pfad)
            seite_1 = brief_reader.pages[0]
            seite_1.merge_page(text_pdf.pages[0])
            writer.add_page(seite_1)
            for i in range(1, len(text_pdf.pages)):
                brief_reader_neu = PdfReader(briefbogen_pfad)
                weitere_seite = brief_reader_neu.pages[1] if len(brief_reader_neu.pages) > 1 else brief_reader_neu.pages[0]
                weitere_seite.merge_page(text_pdf.pages[i])
                writer.add_page(weitere_seite)
        else:
            for page in text_pdf.pages: writer.add_page(page)
    except Exception as e:
        for page in text_pdf.pages: writer.add_page(page)

    jahr_ausgabe = os.path.join(ausgabe_ordner, str(rechnungsjahr))
    os.makedirs(jahr_ausgabe, exist_ok=True)
    
    xml_datei = os.path.join(jahr_ausgabe, f"Rechnung_{r_nr}.xml")
    pdf_datei = os.path.join(jahr_ausgabe, f"Rechnung_{r_nr}_Begleit.pdf")
    
    with open(xml_datei, "w", encoding="utf-8") as f_xml:
        f_xml.write(xml_content)
        
    with open(pdf_datei, "wb") as out_pdf:
        writer.write(out_pdf)
        
    return xml_datei, pdf_datei
    
def erstelle_papierrechnung(firma, rechnung_daten, brief_pfad, zusatztexte, gruss_text, header_text, einleitung_text, ausgabe_ordner, auswertungen_ordner, rechnungsjahr):
    """Erstellt ausschließlich eine visuelle PDF-Rechnung ohne XML-Anhang."""
    kopf, positionen = rechnung_daten['kopf'], rechnung_daten['positionen']
    r_nr = kopf.get('Rechnungsnummer', '')
    netto = sum(safe_float(p['Menge'], 1.0) * safe_float(p['EinzelpreisNetto'], 0.0) for p in positionen)
    steuer = sum(safe_float(p['Menge'], 1.0) * safe_float(p['EinzelpreisNetto'], 0.0) * (safe_float(p.get('Steuersatz', 19.0), 19.0) / 100.0) for p in positionen)
    brutto = netto + steuer
    text_pdf = PdfReader(generiere_rechnung_text_pdf(firma, kopf, positionen, netto, steuer, brutto, zusatztexte, gruss_text, header_text, einleitung_text))
    writer = PdfWriter()
    writer._header = b"%PDF-1.7"
    try:
        briefbogen_pfad = brief_pfad if os.path.exists(brief_pfad) else None
        if briefbogen_pfad:
            brief_reader = PdfReader(briefbogen_pfad)
            erste_seite = brief_reader.pages[0]
            erste_seite.merge_page(text_pdf.pages[0])
            writer.add_page(erste_seite)
            for i in range(1, len(text_pdf.pages)):
                brief_reader_neu = PdfReader(briefbogen_pfad)
                weitere_seite = brief_reader_neu.pages[1] if len(brief_reader_neu.pages) > 1 else brief_reader_neu.pages[0]
                weitere_seite.merge_page(text_pdf.pages[i])
                writer.add_page(weitere_seite)
        else:
            for page in text_pdf.pages:
                writer.add_page(page)
    except Exception:
        for page in text_pdf.pages:
            writer.add_page(page)
    jahr_ausgabe = os.path.join(ausgabe_ordner, str(rechnungsjahr))
    os.makedirs(jahr_ausgabe, exist_ok=True)
    ausgabe_datei = os.path.join(jahr_ausgabe, f"Rechnung_{r_nr}_Papier.pdf")
    with open(ausgabe_datei, "wb") as out_pdf:
        writer.write(out_pdf)
    return ausgabe_datei

def erstelle_zugferd_pdf(firma, rechnung_daten, brief_pfad, zusatztexte, gruss_text, header_text, einleitung_text, ausgabe_ordner, auswertungen_ordner, rechnungsjahr):
    kopf, positionen = rechnung_daten['kopf'], rechnung_daten['positionen']
    r_nr = kopf.get('Rechnungsnummer', '')
    
    # 1. XML über die gemeinsame Funktion generieren
    xml_content = generiere_en16931_xml(firma, kopf, positionen, zusatztexte, gruss_text, header_text, einleitung_text)
    
    r_datum, f_datum = formatiere_datum(kopf.get('Rechnungsdatum', '')), formatiere_datum(kopf.get('Faelligkeitsdatum', ''))
    
    gesamt_netto = sum(safe_float(p['Menge'], 1.0) * safe_float(p['EinzelpreisNetto'], 0.0) for p in positionen)
    gesamt_steuer = sum(safe_float(p['Menge'], 1.0) * safe_float(p['EinzelpreisNetto'], 0.0) * (safe_float(p.get('Steuersatz', 19.0), 19.0)/100.0) for p in positionen)
    gesamt_brutto = gesamt_netto + gesamt_steuer

    text_pdf_stream = generiere_rechnung_text_pdf(firma, kopf, positionen, gesamt_netto, gesamt_steuer, gesamt_brutto, zusatztexte, gruss_text, header_text, einleitung_text)
    text_pdf = PdfReader(text_pdf_stream)
    writer = PdfWriter()
    writer._header = b"%PDF-1.7"
    
    try:
        briefbogen_pfad = brief_pfad if os.path.exists(brief_pfad) else None
        if briefbogen_pfad:
            brief_reader = PdfReader(briefbogen_pfad)
            seite_1 = brief_reader.pages[0]
            seite_1.merge_page(text_pdf.pages[0])
            writer.add_page(seite_1)
            for i in range(1, len(text_pdf.pages)):
                brief_reader_neu = PdfReader(briefbogen_pfad) 
                weitere_seite = brief_reader_neu.pages[1] if len(brief_reader_neu.pages) > 1 else brief_reader_neu.pages[0]
                weitere_seite.merge_page(text_pdf.pages[i])
                writer.add_page(weitere_seite)
        else:
            for page in text_pdf.pages: writer.add_page(page)
    except Exception as e:
        for page in text_pdf.pages: writer.add_page(page)

    # XML als ZUGFeRD-Attachment einbetten
    writer.add_attachment("factur-x.xml", xml_content.encode("utf-8"))
    
    xmp_xml = f"""<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">
      <pdfaid:part>3</pdfaid:part>
      <pdfaid:conformance>B</pdfaid:conformance>
    </rdf:Description>
    <rdf:Description rdf:about="" xmlns:fx="urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#">
      <fx:DocumentType>INVOICE</fx:DocumentType>
      <fx:DocumentFileName>factur-x.xml</fx:DocumentFileName>
      <fx:Version>1.0</fx:Version>
      <fx:ConformanceLevel>EN 16931</fx:ConformanceLevel>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""

    try:
        metadata_stream = StreamObject()
        metadata_stream._data = xmp_xml.encode("utf-8")
        metadata_stream.update({
            NameObject("/Type"): NameObject("/Metadata"),
            NameObject("/Subtype"): NameObject("/XML")
        })
        xmp_ref = writer._add_object(metadata_stream)
        writer._root_object.update({NameObject("/Metadata"): xmp_ref})
        
        for obj in writer._objects:
            if isinstance(obj, DictionaryObject) and obj.get(NameObject("/Type")) == "/Filespec":
                f_val = obj.get(NameObject("/F"))
                if f_val and str(f_val) == "factur-x.xml":
                    obj.update({NameObject("/AFRelationship"): NameObject("/Data")})
                    af_array = ArrayObject([obj.indirect_reference])
                    writer._root_object.update({NameObject("/AF"): af_array})
                    break
    except Exception as e:
        pass

    jahr_ausgabe = os.path.join(ausgabe_ordner, str(rechnungsjahr))
    os.makedirs(jahr_ausgabe, exist_ok=True)
    ausgabe_datei = os.path.join(jahr_ausgabe, f"Rechnung_{r_nr}.pdf")
    
    with open(ausgabe_datei, "wb") as out_pdf: writer.write(out_pdf)
    
    # Journal-Eintrag schreiben
    try:
        if r_datum and r_nr:
            date_obj = datetime.strptime(r_datum, "%Y%m%d")
            journal_filename = f"re{date_obj.strftime('%Y%m')}.csv"
            
            jahr_auswertungen = os.path.join(auswertungen_ordner, str(rechnungsjahr))
            os.makedirs(jahr_auswertungen, exist_ok=True)
            journal_path = os.path.join(jahr_auswertungen, journal_filename)
            
            # Steuersätze für Journal ermitteln
            steuer_gruppen = {}
            for pos in positionen:
                satz = safe_float(pos.get('Steuersatz', 19.0), 19.0)
                st = safe_float(pos['Menge'], 1.0) * safe_float(pos['EinzelpreisNetto'], 0.0) * (satz / 100.0)
                if satz > 0:
                    steuer_gruppen[satz] = steuer_gruppen.get(satz, 0.0) + st

            st_19 = steuer_gruppen.get(19.0, 0.0)
            st_7 = steuer_gruppen.get(7.0, 0.0)
            st_0 = steuer_gruppen.get(0.0, 0.0)
            
            file_exists = os.path.exists(journal_path)
            with open(journal_path, 'a', newline='', encoding='utf-8-sig') as f:
                writer_j = csv.writer(f, delimiter=';')
                if not file_exists:
                    writer_j.writerow(["Rechnungsnummer", "Datum", "Empfaenger", "Netto", "MwSt_19", "MwSt_7", "MwSt_0", "Brutto"])
                writer_j.writerow([r_nr, date_obj.strftime("%d.%m.%Y"), kopf.get('KundeName', ''), f"{gesamt_netto:.2f}".replace('.', ','), f"{st_19:.2f}".replace('.', ','), f"{st_7:.2f}".replace('.', ','), f"{st_0:.2f}".replace('.', ','), f"{gesamt_brutto:.2f}".replace('.', ',')])
    except Exception as e:
        print(f"Fehler beim Schreiben des Journals: {e}")
        
    return ausgabe_datei

def run_auto_generation(config):
    act_prof = config["profiles"][config["active_profile_index"]]
    if not os.path.exists(act_prof['firma_csv']): return print(f"❌ Fehler: '{act_prof['firma_csv']}' fehlt.")
    if not os.path.exists(act_prof['rechnung_csv']): return print(f"❌ Fehler: '{act_prof['rechnung_csv']}' fehlt.")
    
    try:
        firma = lade_firma(act_prof['firma_csv'])
        if config.get("cli_no_girocode"): 
            firma['Girocode'] = '0'
        elif config.get("cli_force_girocode"): 
            firma['Girocode'] = '1'
            
        if config.get("cli_kontoinhaber"):
            firma['Kontoinhaber'] = config.get("cli_kontoinhaber")
            
        rechnungen = lade_rechnungen(act_prof['rechnung_csv'])
        zusatztexte = lade_zusatz_csv(act_prof['zusatz_csv'])
        gruss = lade_textdatei(act_prof['gruss_csv'])
        header = lade_textdatei(act_prof['header_csv'])
        einleitung = lade_textdatei(act_prof['einleitung_csv'])
        
        akt_jahr = act_prof.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        
        for r_nr, daten in rechnungen.items():
            # NEU: Wenn eine Nummer übergeben wurde, überschreibe die aus der CSV
            if config.get("cli_renr"):
                r_nr = config.get("cli_renr")
                daten['kopf']['Rechnungsnummer'] = r_nr
            if config.get("cli_kunde_az"):
                daten['kopf']['KundeAktenzeichen'] = config.get("cli_kunde_az")
                
            valid, msg = check_lz_logic(daten['kopf'], daten['positionen'])
            if not valid:
                print(f"❌ Fehler bei RE '{r_nr}': {msg}\nWird übersprungen.")
                continue
            pdf_pfad = erstelle_zugferd_pdf(firma, daten, act_prof['briefbogen_pdf'], zusatztexte, gruss, header, einleitung, act_prof['ausgabe_ordner'], act_prof['auswertungen_ordner'], akt_jahr)
            print(f"✅ Erstellt: RE {r_nr}")
            kopie_dir = config.get("cli_kopie")
            if kopie_dir:
                import shutil
                try:
                    os.makedirs(kopie_dir, exist_ok=True)
                    shutil.copy2(pdf_pfad, os.path.join(kopie_dir, os.path.basename(pdf_pfad)))
                except Exception as e:
                    print(f"Fehler beim Erstellen der Kopie in {kopie_dir}: {e}")
            # Letzte Rechnungsnummer aktualisieren und renr.csv schreiben ---
            act_prof['letzte_rechnungsnummer'] = r_nr
            speichere_config(config)
            
            firm_dir = os.path.dirname(act_prof.get('firma_csv', ''))
            if firm_dir:
                renr_path = os.path.join(firm_dir, "renr.csv")
                try:
                    with open(renr_path, 'w', encoding='utf-8-sig') as f_renr:
                        f_renr.write("LetzteRechnungsnummer\n")
                        f_renr.write(f"{r_nr}\n")
                except Exception as e:
                    print(f"Fehler beim Schreiben der renr.csv: {e}")

            if not config.get("cli_no_open", False):
                try: os.startfile(pdf_pfad)
                except: pass

    except Exception as e:
        print(f"❌ Schwerer Fehler bei PDF-Erstellung: {e}")
