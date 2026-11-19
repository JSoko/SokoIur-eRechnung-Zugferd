"""
xml_processor.py
----------------
Generierung der XML-Struktur nach EN 16931 (ZUGFeRD/XRechnung).
"""
import re
from config import *
from utils import *
from crud import *

def esc_xml(text):
    if text is None: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def clean_xml_text(text):
    text = re.sub(r'~f|f~|~k|k~', '', str(text))
    return esc_xml(text)

def generiere_en16931_xml(firma, kopf, positionen, zusatztexte, gruss_text, header_text, einleitung_text, vor_gruss_text=""):
    r_nr = kopf.get('Rechnungsnummer', '')
    kunde_name_xml = esc_xml(kopf.get('KundeName', '').strip())
    if not kunde_name_xml: kunde_name_xml = "Nicht angegeben"
    
    # EN 16931 BT-52 Pflichtfeld: Falls Ort fehlt, Dummy-Wert eintragen
    kunde_ort = kopf.get('KundeOrt', '').strip()
    if not kunde_ort: kunde_ort = "Fehlt"
    
    r_datum, f_datum = formatiere_datum(kopf.get('Rechnungsdatum', '')), formatiere_datum(kopf.get('Faelligkeitsdatum', ''))
    iban_clean = re.sub(r'\s+', '', firma.get('IBAN', ''))
    bic_clean = re.sub(r'\s+', '', firma.get('BIC', ''))
    
    gesamt_netto, gesamt_steuer, gesamt_brutto, steuer_gruppen_netto = berechne_summen(positionen)
    rc_mode = kopf.get('ReverseCharge', 'Nein').strip()
    kunde_ustid = kopf.get('KundeUStId', '').strip()
    xml_positionen = ""
    
    for pos in positionen:
        menge = safe_float(pos['Menge'], 1.0)
        preis = safe_float(pos['EinzelpreisNetto'], 0.0)
        steuersatz = safe_float(pos.get('Steuersatz', 19.0), 19.0)
        
        pos_netto = round_kaufm(menge * preis)
        
        einheit_raw = str(pos.get('Einheit', 'C62')).strip()
        einheit_codes = re.findall(r'\(([^()]*)\)', einheit_raw)
        einheit_code = einheit_codes[-1].strip() if einheit_codes else einheit_raw
        if not einheit_code.isalnum(): einheit_code = "C62"
        
        if steuersatz > 0:
            cat_code = "S"
        elif rc_mode == "EU":
            cat_code = "AE"   # Reverse Charge (EU)
        elif rc_mode == "Drittland":
            cat_code = "O"    # Nicht steuerbar (Drittland)
        else:
            cat_code = "E"    # Steuerbefreit Inland
        
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

    xml_tax_totals = ""
    for satz, netto_sum in steuer_gruppen_netto.items():
        steuer_sum = round_kaufm(netto_sum * (satz / 100.0))
        exemption_xml = ""
        if satz > 0:
            cat_code = "S"
        elif rc_mode == "EU":
            cat_code = "AE"
            exemption_xml = (
                "<ram:ExemptionReason>Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge)</ram:ExemptionReason>"
                "<ram:ExemptionReasonCode>VATEX-EU-AE</ram:ExemptionReasonCode>"
            )
        elif rc_mode == "Drittland":
            cat_code = "O"
            exemption_xml = (
                "<ram:ExemptionReason>Nicht steuerbare Leistung im Drittland</ram:ExemptionReason>"
                "<ram:ExemptionReasonCode>VATEX-EU-O</ram:ExemptionReasonCode>"
            )
        else:
            cat_code = "E"

        xml_tax_totals += f"""
            <ram:ApplicableTradeTax>
                <ram:CalculatedAmount>{steuer_sum:.2f}</ram:CalculatedAmount>
                <ram:TypeCode>VAT</ram:TypeCode>
                {exemption_xml}
                <ram:BasisAmount>{netto_sum:.2f}</ram:BasisAmount>
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
    if vor_gruss_text: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(vor_gruss_text)}</ram:Content></ram:IncludedNote>\n"
    if gruss_text: xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(gruss_text)}</ram:Content></ram:IncludedNote>\n"
    
    z_bed = kopf.get('Zahlungsbedingungen', '').strip()
    xml_payment_terms = f"<ram:SpecifiedTradePaymentTerms><ram:Description>{clean_xml_text(z_bed)}</ram:Description><ram:DueDateDateTime><udt:DateTimeString format=\"102\">{f_datum}</udt:DateTimeString></ram:DueDateDateTime></ram:SpecifiedTradePaymentTerms>" if z_bed else f"<ram:SpecifiedTradePaymentTerms><ram:DueDateDateTime><udt:DateTimeString format=\"102\">{f_datum}</udt:DateTimeString></ram:DueDateDateTime></ram:SpecifiedTradePaymentTerms>"
    
    r_vermerk = kopf.get('Rechnungsvermerk', '').strip()
    if r_vermerk:
        xml_notes_str += f"<ram:IncludedNote><ram:Content>{clean_xml_text(r_vermerk)}</ram:Content><ram:SubjectCode>REG</ram:SubjectCode></ram:IncludedNote>\n"
    
    xml_buyer_ref = f"<ram:BuyerReference>{esc_xml(kopf.get('KundeAktenzeichen', '').strip())}</ram:BuyerReference>" if kopf.get('KundeAktenzeichen', '').strip() else ""
    xml_buyer_id = f"<ram:ID>{esc_xml(kopf.get('KundeNr', '').strip())}</ram:ID>" if kopf.get('KundeNr', '').strip() else ""

    xrechnung_specification_id = "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"
    business_process_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

    seller_contact_name = firma.get('Ansprechpartner', '').strip() or firma.get('FirmaName', '').strip()
    seller_email = firma.get('Email', '').strip()
    seller_phone = firma.get('Telefon', '').strip()
    xml_seller_contact = f"<ram:DefinedTradeContact><ram:PersonName>{esc_xml(seller_contact_name)}</ram:PersonName>"
    if seller_phone:
        xml_seller_contact += f"<ram:TelephoneUniversalCommunication><ram:CompleteNumber>{esc_xml(seller_phone)}</ram:CompleteNumber></ram:TelephoneUniversalCommunication>"
    if seller_email:
        xml_seller_contact += f"<ram:EmailURIUniversalCommunication><ram:URIID>{esc_xml(seller_email)}</ram:URIID></ram:EmailURIUniversalCommunication>"
    xml_seller_contact += "</ram:DefinedTradeContact>"

    seller_endpoint = seller_email
    seller_endpoint_scheme = firma.get('EndpointScheme', '').strip() or ('EM' if seller_endpoint else '')
    buyer_endpoint = kopf.get('KundeEndpoint', '').strip() or kopf.get('KundeEmail', '').strip()
    buyer_endpoint_scheme = kopf.get('KundeEndpointScheme', '').strip() or ('EM' if buyer_endpoint and '@' in buyer_endpoint else '')
    xml_seller_endpoint = (f'<ram:URIUniversalCommunication><ram:URIID schemeID="{esc_xml(seller_endpoint_scheme)}">{esc_xml(seller_endpoint)}</ram:URIID></ram:URIUniversalCommunication>' if seller_endpoint and seller_endpoint_scheme else '')
    xml_buyer_endpoint = (f'<ram:URIUniversalCommunication><ram:URIID schemeID="{esc_xml(buyer_endpoint_scheme)}">{esc_xml(buyer_endpoint)}</ram:URIID></ram:URIUniversalCommunication>' if buyer_endpoint and buyer_endpoint_scheme else '')
    xml_buyer_tax = (f'<ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">{esc_xml(kunde_ustid)}</ram:ID></ram:SpecifiedTaxRegistration>' if kunde_ustid else '')
    
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
                <ram:PostalTradeAddress><ram:PostcodeCode>{esc_xml(kopf.get('KundePLZ',''))}</ram:PostcodeCode><ram:LineOne>{esc_xml(kopf.get('KundeStrasse',''))}</ram:LineOne><ram:CityName>{esc_xml(kunde_ort)}</ram:CityName><ram:CountryID>{esc_xml(kopf.get('KundeLand','DE'))}</ram:CountryID></ram:PostalTradeAddress>
                {xml_buyer_endpoint}
                {xml_buyer_tax}
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
            {xml_payment_terms}
            <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                <ram:LineTotalAmount>{gesamt_netto:.2f}</ram:LineTotalAmount><ram:TaxBasisTotalAmount>{gesamt_netto:.2f}</ram:TaxBasisTotalAmount>
                <ram:TaxTotalAmount currencyID="EUR">{gesamt_steuer:.2f}</ram:TaxTotalAmount><ram:GrandTotalAmount>{gesamt_brutto:.2f}</ram:GrandTotalAmount><ram:DuePayableAmount>{gesamt_brutto:.2f}</ram:DuePayableAmount>
            </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        </ram:ApplicableHeaderTradeSettlement>
    </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
"""