"""
pdf_zugferd.py
--------------
Generierungs-Engine für Rechnungen im ZUGFeRD- und XRechnung-Format.
Verwendet eine zentrale XML-Generierung nach EN 16931 (CII-Standard) für beide Formate.
"""
import os
import re
import csv
import shutil
import tempfile
from io import BytesIO
from datetime import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, ArrayObject, StreamObject

from config import *
from utils import *
from crud import *
from audit import write_audit_log
from xml_processor import esc_xml, clean_xml_text, generiere_en16931_xml
from pdf_builder import generiere_rechnung_text_pdf
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle

def erstelle_xrechnung(
    firma,
    rechnung_daten,
    brief_pfad,
    zusatztexte,
    gruss_text,
    header_text,
    einleitung_text,
    ausgabe_ordner,
    auswertungen_ordner,
    rechnungsjahr,
    vor_gruss_text="",
    briefkopf_rechte_spalte=True,
):
    kopf, positionen = rechnung_daten['kopf'], rechnung_daten['positionen']
    r_nr = kopf.get('Rechnungsnummer', '')
    
    # 1. XML über die gemeinsame Funktion generieren
    xml_content = generiere_en16931_xml(firma, kopf, positionen, zusatztexte, gruss_text, header_text, einleitung_text, vor_gruss_text)
    
    # 2. Begleit-PDF mit rechtlichem Hinweis generieren
    hinweis_text = "~kHinweis: Dies ist eine Begleitdatei zur XRechnungsdatei und maßgeblich ist die X-Rechnungsdatei.k~"
    gruss_erweitert = f"{gruss_text}\n\n{hinweis_text}" if gruss_text else hinweis_text

    netto, steuer, brutto, _ = berechne_summen(positionen)

    text_pdf_stream = generiere_rechnung_text_pdf(
        firma,
        kopf,
        positionen,
        netto,
        steuer,
        brutto,
        zusatztexte,
        gruss_erweitert,
        header_text,
        einleitung_text,
        vor_gruss_text,
        briefkopf_rechte_spalte=briefkopf_rechte_spalte,
    )
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
    
def erstelle_papierrechnung(
    firma,
    rechnung_daten,
    brief_pfad,
    zusatztexte,
    gruss_text,
    header_text,
    einleitung_text,
    ausgabe_ordner,
    auswertungen_ordner,
    rechnungsjahr,
    vor_gruss_text="",
    briefkopf_rechte_spalte=True,
):
    """Erstellt ausschließlich eine visuelle PDF-Rechnung ohne XML-Anhang."""
    kopf, positionen = rechnung_daten['kopf'], rechnung_daten['positionen']
    r_nr = kopf.get('Rechnungsnummer', '')
    netto, steuer, brutto, _ = berechne_summen(positionen)
    text_pdf = PdfReader(
        generiere_rechnung_text_pdf(
            firma,
            kopf,
            positionen,
            netto,
            steuer,
            brutto,
            zusatztexte,
            gruss_text,
            header_text,
            einleitung_text,
            vor_gruss_text,
            briefkopf_rechte_spalte=briefkopf_rechte_spalte,
        )
    )
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

def erstelle_testrechnung(
    firma,
    rechnung_daten,
    brief_pfad,
    zusatztexte,
    gruss_text,
    header_text,
    einleitung_text,
    vor_gruss_text="",
    briefkopf_rechte_spalte=True,
):
    """Erstellt eine Vorschau-PDF ohne Rechnungsnummer im Temp-Verzeichnis. Es erfolgt kein Journaleintrag."""
    import tempfile
    
    kopf, positionen = rechnung_daten['kopf'], rechnung_daten['positionen']
    
    # Rechnungsnummer für die visuelle Ausgabe unterdrücken
    kopf['Rechnungsnummer'] = ""
    
    netto, steuer, brutto, _ = berechne_summen(positionen)
    
    text_pdf = PdfReader(
        generiere_rechnung_text_pdf(
            firma,
            kopf,
            positionen,
            netto,
            steuer,
            brutto,
            zusatztexte,
            gruss_text,
            header_text,
            einleitung_text,
            vor_gruss_text,
            briefkopf_rechte_spalte=briefkopf_rechte_spalte,
        )
    )
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
            
    # Im Temp-Ordner speichern
    temp_dir = tempfile.gettempdir()
    ausgabe_datei = os.path.join(temp_dir, "Testrechnung_Vorschau.pdf")
    
    with open(ausgabe_datei, "wb") as out_pdf:
        writer.write(out_pdf)
        
    return ausgabe_datei

def erstelle_zugferd_pdf(
    firma,
    rechnung_daten,
    brief_pfad,
    zusatztexte,
    gruss_text,
    header_text,
    einleitung_text,
    ausgabe_ordner,
    auswertungen_ordner,
    rechnungsjahr,
    vor_gruss_text="",
    briefkopf_rechte_spalte=True,
):
    kopf, positionen = rechnung_daten['kopf'], rechnung_daten['positionen']
    r_nr = kopf.get('Rechnungsnummer', '')
    
    # 1. XML über die gemeinsame Funktion generieren
    xml_content = generiere_en16931_xml(firma, kopf, positionen, zusatztexte, gruss_text, header_text, einleitung_text, vor_gruss_text)
    
    r_datum, f_datum = formatiere_datum(kopf.get('Rechnungsdatum', '')), formatiere_datum(kopf.get('Faelligkeitsdatum', ''))
    
    gesamt_netto, gesamt_steuer, gesamt_brutto, _ = berechne_summen(positionen)

    text_pdf_stream = generiere_rechnung_text_pdf(
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
        vor_gruss_text,
        briefkopf_rechte_spalte=briefkopf_rechte_spalte,
    )
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
            
            existing_rows = []
            header = ["Rechnungsnummer", "Datum", "Empfaenger", "Netto", "MwSt_19", "MwSt_7", "MwSt_0", "Brutto", "Bezahlt"]
            existing_paid_status = ""
            
            if os.path.exists(journal_path):
                with open(journal_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f, delimiter=';')
                    for idx, row in enumerate(reader):
                        # Header überspringen
                        if idx == 0 and row and row[0] == "Rechnungsnummer":
                            continue
                        # Alte Zeile mit dieser Rechnungsnummer merken & ignorieren (wird überschrieben)
                        if row and row[0] == str(r_nr):
                            if len(row) >= 9:
                                existing_paid_status = row[8]
                            continue
                        while len(row) < 9:
                            row.append("")
                        existing_rows.append(row[:9])
                        
            # Neue Zeile anhängen (Bezahlt-Status bleibt bei Korrektur erhalten)
            new_row = [
                r_nr, 
                date_obj.strftime("%d.%m.%Y"), 
                kopf.get('KundeName', ''), 
                f"{gesamt_netto:.2f}".replace('.', ','), 
                f"{st_19:.2f}".replace('.', ','), 
                f"{st_7:.2f}".replace('.', ','), 
                f"{st_0:.2f}".replace('.', ','), 
                f"{gesamt_brutto:.2f}".replace('.', ','),
                existing_paid_status
            ]
            existing_rows.append(new_row)
            
            # Alles neu schreiben
            with open(journal_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer_j = csv.writer(f, delimiter=';')
                writer_j.writerow(header)
                writer_j.writerows(existing_rows)
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
        vor_gruss = lade_textdatei(act_prof.get('vor_gruss_csv', ''))
        header = lade_textdatei(act_prof['header_csv'])
        einleitung = lade_textdatei(act_prof['einleitung_csv'])
        
        akt_jahr = act_prof.get("aktuelles_rechnungsjahr", str(datetime.now().year))
        briefkopf_rechte_spalte = bool(act_prof.get("briefkopf_rechte_spalte", True))
        
        for r_nr, daten in rechnungen.items():
            if config.get("cli_renr"):
                r_nr = config.get("cli_renr")
                daten['kopf']['Rechnungsnummer'] = r_nr
            if config.get("cli_kunde_az"):
                daten['kopf']['KundeAktenzeichen'] = config.get("cli_kunde_az")
            if config.get("cli_zahlungsbedingungen"):
                daten['kopf']['Zahlungsbedingungen'] = config.get("cli_zahlungsbedingungen")
            elif not daten['kopf'].get('Zahlungsbedingungen', '').strip():
                daten['kopf']['Zahlungsbedingungen'] = act_prof.get('zahlungsbedingungen_default', '').strip()
            if config.get("cli_rechnungsvermerk"):
                daten['kopf']['Rechnungsvermerk'] = config.get("cli_rechnungsvermerk")
            elif not daten['kopf'].get('Rechnungsvermerk', '').strip():
                daten['kopf']['Rechnungsvermerk'] = act_prof.get('rechnungsvermerk_default', '').strip()
                
            valid, msg = check_lz_logic(daten['kopf'], daten['positionen'])
            if not valid:
                print(f"❌ Fehler bei RE '{r_nr}': {msg}\nWird übersprungen.")
                continue
            pdf_pfad = erstelle_zugferd_pdf(
                firma,
                daten,
                act_prof['briefbogen_pdf'],
                zusatztexte,
                gruss,
                header,
                einleitung,
                act_prof['ausgabe_ordner'],
                act_prof['auswertungen_ordner'],
                akt_jahr,
                vor_gruss,
                briefkopf_rechte_spalte=briefkopf_rechte_spalte,
            )
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
            
            # Audit-Log für CLI (--auto)
            if config.get("is_cli_auto"):
                base_data_path = config.get("base_data_path", "")
                if base_data_path:
                    firm_dir = os.path.join(base_data_path, act_prof["profil_name"].replace(" ", "_"))
                    write_audit_log(firm_dir, "Ausgang", "Erstellt (--auto)", r_nr, "Automatische Erzeugung via Kommandozeile", "CLI (--auto)")
            
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