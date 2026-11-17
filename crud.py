"""
crud.py
-------
Datenzugriffsschicht (Data Access Layer) für CSV-Dateien und Textvorlagen.
Lese- und Schreiboperationen für Firmen, Rechnungen, Kunden und Produkte.
"""
import os
import csv

def create_csv_if_missing(filename, header_str):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8-sig') as f:
            if header_str: f.write(header_str + "\n")

def ensure_utf8_csv(pfad):
    """Prüft ob eine CSV UTF-8 ist, falls nicht (z.B. ANSI/Excel), wird sie konvertiert."""
    if not pfad or not os.path.exists(pfad):
        return
    try:
        # Testweise als UTF-8 lesen
        with open(pfad, 'r', encoding='utf-8-sig') as f:
            f.read()
    except UnicodeDecodeError:
        # Wenn es knallt, als Windows-1252 (Standard Excel/ANSI) lesen und überschreiben
        with open(pfad, 'r', encoding='windows-1252') as f:
            inhalt = f.read()
        with open(pfad, 'w', encoding='utf-8-sig') as f:
            f.write(inhalt)

def lade_firma(pfad):
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            reader = list(csv.DictReader(f, delimiter=';'))
            if reader: return reader[0]
    except: pass
    return {'FirmaName': 'Bitte Firmendaten konfigurieren', 'Strasse': '', 'PLZ': '', 'Ort': '', 'Land': 'DE', 'UStId': '', 'Steuernummer': '', 'BankName': '', 'IBAN': '', 'BIC': '', 'Kontoinhaber': '', 'Girocode': '1'}

def speichere_firma(pfad, daten):
    fieldnames = ['FirmaName', 'Strasse', 'PLZ', 'Ort', 'Land', 'UStId', 'Steuernummer', 'BankName', 'IBAN', 'BIC', 'Kontoinhaber', 'Girocode', 'Falzmarken', 'Email', 'Telefon']
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerow(daten)

def lade_rechnungen(pfad):
    rechnungen = {}
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f, delimiter=';'):
                r_nr = row['Rechnungsnummer']
                if r_nr not in rechnungen: rechnungen[r_nr] = {'kopf': row, 'positionen': []}
                rechnungen[r_nr]['positionen'].append(row)
    except: pass
    return rechnungen

def lade_zusatz_csv(pfad):
    texte = []
    if not os.path.exists(pfad): return texte
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.split(';', 1)
                if len(parts) == 2:
                    texte.append({'pos': parts[0].strip(), 'text': parts[1].strip().replace('~cr', '\n')})
    except: pass
    return texte

def lade_textdatei(pfad):
    if not os.path.exists(pfad): return ""
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            return f.read().strip().replace('~cr', '\n')
    except: return ""

def speichere_textdatei(pfad, text):
    if not pfad: return
    try:
        with open(pfad, 'w', encoding='utf-8-sig') as f:
            f.write(text.replace('\n', '~cr').strip())
    except: pass

def lade_kunden(pfad):
    kunden = []
    if not os.path.exists(pfad): return kunden
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f, delimiter=';'):
                kunden.append(row)
    except: pass
    return kunden

def speichere_alle_kunden(pfad, kunden_liste):
    fieldnames = ['Name', 'Strasse', 'PLZ_Ort', 'Land', 'KundeNr', 'Aktenzeichen', 'KundeAktenzeichen', 'Endpoint', 'EndpointScheme']
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(kunden_liste)

def speichere_kunde(pfad, kunde_daten):
    kunden = lade_kunden(pfad)
    updated = False
    for k in kunden:
        if k['Name'].strip().lower() == kunde_daten['Name'].strip().lower():
            k.update(kunde_daten)
            updated = True
            break
    if not updated:
        kunden.append(kunde_daten)
    speichere_alle_kunden(pfad, kunden)

def lade_produkte(pfad):
    produkte = []
    if not os.path.exists(pfad): return produkte
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f, delimiter=';'):
                produkte.append(row)
    except: pass
    return produkte

def speichere_alle_produkte(pfad, produkte_liste):
    fieldnames = ['Bezeichnung', 'Menge', 'Einheit', 'EinzelpreisNetto', 'Steuersatz']
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(produkte_liste)