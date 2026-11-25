
"""
crud.py
-------
Datenzugriffsschicht (Data Access Layer) für CSV-Dateien und Textvorlagen.
Lese- und Schreiboperationen für Firmen, Rechnungen, Kunden und Produkte.
"""
import os
import csv
import tempfile

def atomic_save_csv(pfad, fieldnames, rows, delimiter=';'):
    """
    Schreibt CSV-Daten atomar (absturzsicher), indem zuerst in eine 
    temporäre Datei im selben Ordner geschrieben und diese dann umbenannt wird.
    """
    dir_name = os.path.dirname(os.path.abspath(pfad))
    os.makedirs(dir_name, exist_ok=True)
    
    # Temporäre Datei im selben Verzeichnis erstellen
    fd, temp_path = tempfile.mkstemp(dir=dir_name, text=True)
    try:
        with os.fdopen(fd, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)
            
        # Atomarer Austausch (überschreibt das Ziel sicher in einem Schritt)
        os.replace(temp_path, pfad)
    except Exception as e:
        # Bei einem Fehler die Temp-Datei aufräumen
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise e
        
def create_csv_if_missing(filename, header_str):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8-sig') as f:
            if header_str: f.write(header_str + "\n")

def ensure_utf8_csv(pfad):
    """Prüft ob eine CSV UTF-8 ist, falls nicht (z.B. ANSI/Excel), wird sie konvertiert."""
    if not pfad or not os.path.exists(pfad):
        return
    try:
        with open(pfad, 'r', encoding='utf-8-sig') as f:
            f.read()
    except UnicodeDecodeError:
        with open(pfad, 'r', encoding='windows-1252') as f:
            inhalt = f.read()
        with open(pfad, 'w', encoding='utf-8-sig') as f:
            f.write(inhalt)

def lade_firma(pfad):
    try:
        with open(pfad, mode='r', encoding='utf-8-sig') as f:
            reader = list(csv.DictReader(f, delimiter=';'))
            if reader:
                return reader[0]
    except Exception:
        pass
    return {
        'FirmaName': 'Bitte Firmendaten konfigurieren',
        'Absenderzeile': '',
        'Strasse': '',
        'PLZ': '',
        'Ort': '',
        'Land': 'DE',
        'UStId': '',
        'Steuernummer': '',
        'BankName': '',
        'IBAN': '',
        'BIC': '',
        'Kontoinhaber': '',
        'Girocode': '1',
    }

def speichere_firma(pfad, daten):
    fieldnames = [
        'FirmaName', 'Absenderzeile', 'Strasse', 'PLZ', 'Ort', 'Land',
        'UStId', 'Steuernummer', 'BankName', 'IBAN', 'BIC',
        'Kontoinhaber', 'Girocode', 'Falzmarken', 'Email', 'Telefon'
    ]
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
    fieldnames = ['Name', 'Strasse', 'PLZ_Ort', 'Land', 'KundeNr', 'UStId', 'Aktenzeichen', 'KundeAktenzeichen', 'Endpoint', 'EndpointScheme']
    cleaned_rows = []
    for row in (kunden_liste or []):
        r_copy = dict(row)
        if not str(r_copy.get('UStId', '')).strip() and str(r_copy.get('KundeUStId', '')).strip():
            r_copy['UStId'] = str(r_copy.get('KundeUStId', '')).strip()
        cleaned_rows.append({fn: str(r_copy.get(fn, '') or '').strip() for fn in fieldnames})
    atomic_save_csv(pfad, fieldnames, cleaned_rows, delimiter=';')
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(cleaned_rows)

def speichere_kunde(pfad, kunde_daten, original_kunde=None):
    kunden = lade_kunden(pfad)
    neu_daten = dict(kunde_daten or {})
    neu_name = str(neu_daten.get('Name', '')).strip()
    neu_nr = str(neu_daten.get('KundeNr', '')).strip()
    neu_ustid = str(neu_daten.get('UStId', '')).strip()

    if original_kunde is not None:
        orig_name = str(original_kunde.get('Name', '')).strip()
        orig_nr = str(original_kunde.get('KundeNr', '')).strip()
        key_changed = (neu_nr != orig_nr) or (neu_name.lower() != orig_name.lower())

        if not key_changed:
            # Weder Kundennummer noch Name geändert -> bestehenden Datensatz aktualisieren
            updated = False
            for k in kunden:
                if (
                    str(k.get('Name', '')).strip().lower() == orig_name.lower()
                    and str(k.get('KundeNr', '')).strip() == orig_nr
                ):
                    if not neu_ustid:
                        neu_daten['UStId'] = str(k.get('UStId', '')).strip()
                    k.update(neu_daten)
                    updated = True
                    break
            if not updated:
                kunden.append(neu_daten)
        else:
            # Kundennummer und/oder Name geändert -> als neuen Datensatz anlegen (oder ggf. gleichnamigen/-nummerigen aktualisieren)
            existing_match = None
            for k in kunden:
                k_name = str(k.get('Name', '')).strip().lower()
                k_nr = str(k.get('KundeNr', '')).strip()
                if (neu_nr and k_nr == neu_nr) or (not neu_nr and k_name == neu_name.lower()):
                    existing_match = k
                    break
            if existing_match is not None:
                if not neu_ustid:
                    neu_daten['UStId'] = str(existing_match.get('UStId', '')).strip()
                existing_match.update(neu_daten)
            else:
                kunden.append(neu_daten)
    else:
        updated = False
        for k in kunden:
            k_name = str(k.get('Name', '')).strip().lower()
            k_nr = str(k.get('KundeNr', '')).strip()
            matched = (neu_nr and k_nr == neu_nr) or (k_name == neu_name.lower())
            if matched:
                if not neu_ustid:
                    neu_daten['UStId'] = str(k.get('UStId', '')).strip()
                k.update(neu_daten)
                updated = True
                break
        if not updated:
            kunden.append(neu_daten)

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
    atomic_save_csv(pfad, fieldnames, produkte_liste, delimiter=';')
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(produkte_liste)
        
def loesche_kunde(pfad, kunden_name):
    kunden = lade_kunden(pfad)
    kunden_neu = [k for k in kunden if k['Name'].strip().lower() != kunden_name.strip().lower()]
    speichere_alle_kunden(pfad, kunden_neu)

def speichere_produkt(pfad, produkt_daten):
    produkte = lade_produkte(pfad)
    updated = False
    for p in produkte:
        if p['Bezeichnung'].strip().lower() == produkt_daten['Bezeichnung'].strip().lower():
            p.update(produkt_daten)
            updated = True
            break
    if not updated:
        produkte.append(produkt_daten)
    speichere_alle_produkte(pfad, produkte)

def loesche_produkt(pfad, bezeichnung):
    produkte = lade_produkte(pfad)
    produkte_neu = [p for p in produkte if p['Bezeichnung'].strip().lower() != bezeichnung.strip().lower()]
    speichere_alle_produkte(pfad, produkte_neu)
