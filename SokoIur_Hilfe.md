# SokoIur eRechnung - Handbuch
**Version: 2.000149**

## Inhaltsverzeichnis
- [1. Installation & Ersteinrichtung](#1-installation--ersteinrichtung)
- [2. Haftungsausschluss, Support & Datenschutz](#2-haftungsausschluss-support--datenschutz)
- [2.1 Lizenzerklärung](#21-lizenzerklärung)
- [3. Programmbeschreibung & Aufruf (CLI / GUI)](#3-programmbeschreibung--aufruf-cli--gui)
- [3.1 Die Benutzeroberfläche (Tabs) im Detail](#31-die-benutzeroberfläche-tabs-im-detail)
- [3.2 Die Kommandozeilenparameter (CLI) im Detail](#32-die-kommandozeilenparameter-cli-im-detail)
- [3.3 Programmfunktionen, Verwendungsszenarien & Anwendungsfälle](#33-programmfunktionen-verwendungsszenarien--anwendungsfälle)
- [4. Ordnerstruktur und Dateien](#4-ordnerstruktur-und-dateien)
- [5. Jahreswechsel](#5-jahreswechsel)
- [6. Mandanten & Datenbanken](#6-mandanten--datenbanken)
- [7. Rechnungspositionen, Leistungszeitraum & Duplikate](#7-rechnungspositionen-leistungszeitraum--duplikate)
- [8. Rechnungsformate, Papierrechnung & elektronische Empfängeradresse](#8-rechnungsformate-papierrechnung--elektronische-empfängeradresse)
- [9. Datumseingaben](#9-datumseingaben)
- [10. Standardtexte & Formatierungen](#10-standardtexte--formatierungen)
- [11. Eingangsrechnungen erfassen und auswerten](#11-eingangsrechnungen-erfassen-und-auswerten)
- [11.8 Hinweise zur revisionssicheren Archivierung (Ausblick)](#118-hinweise-zur-revisionssicheren-archivierung-ausblick)
- [12. DATEV-Export & Buchhaltung](#12-datev-export--buchhaltung)
- [13. GitHub & Updates](#13-github--updates)
- [14. Import-Formate (CSV)](#14-import-formate-csv)
- [15. Lizenzen & Drittparty-Module](#15-lizenzen--drittparty-module)

## 1. Installation & Ersteinrichtung
Die Anwendung (`.exe`) kann in einem beliebigen Ordner auf Ihrem PC abgelegt werden – auch in systemgeschützten Verzeichnissen wie `C:\Programme`. Lokale Geräteeinstellungen speichert das Programm automatisch sicher in Ihrem Windows-Benutzerverzeichnis (`%LOCALAPPDATA%\SokoIur_eRechnung`), sodass keine Administratorrechte für den täglichen Betrieb nötig sind.

### Ersteinrichtung und Datenspeicherort:
Beim allerersten Start des Programms werden Sie aufgefordert, einen Grundpfad für die Datenspeicherung auszuwählen.

> **WICHTIG:** Dieser Ordner darf sich aus Sicherheits- und Updategründen NICHT innerhalb oder unterhalb des Programmordners befinden!
> Wenn Sie das Programm von mehreren Rechnern aus nutzen möchten, wählen Sie hier zwingend ein freigegebenes Netzwerklaufwerk aus.

Anschließend legt das Programm dort alle benötigten Unterordner und leeren Konfigurations-Dateien (`.csv`) automatisch für Ihre erste Firma an.

### Briefbogen hinterlegen:
Um Ihr eigenes Rechnungsdesign (Logo, Fußzeile etc.) als Hintergrund für die Rechnungen zu verwenden, wechseln Sie in den Reiter **⚙️ Einst.** und klicken Sie im Bereich der Firmendaten auf den Button **„📄 Briefbogen hinterlegen“**. Wählen Sie dort einfach Ihre PDF-Vorlage aus.
Tipp: Verfügt Ihr Briefbogen über zwei Seiten, nutzt das Programm für die erste Rechnungsseite die erste Seite des Briefbogens. Für alle Folgeseiten nutzt es die zweite Seite.

## 2. Haftungsausschluss, Support & Datenschutz
Das Programm „SokoIur eRechnung“ wird Ihnen unentgeltlich zur Verfügung gestellt. Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische Umsetzung der ZUGFeRD- und XRechnung-Spezifikationen, wird ausdrücklich ausgeschlossen.

> **Kontakt:** Webseite: [https://erech.6078.de](https://erech.6078.de) | E-Mail: SokoIur@6078.de

## 2.1 Lizenzerklärung
1. **Nutzungsrechte:** Das Programm (ausführbare Datei) wird als Freeware/Donationware bereitgestellt. Die private und gewerbliche Nutzung ist kostenfrei gestattet.
2. **Weitergabe:** Die Software darf unverändert kostenlos weitergegeben werden. Kommerzieller Vertrieb ist untersagt.
3. **Quellcode:** Der Quellcode ist auf GitHub einsehbar. Die .exe darf nicht dekompiliert oder manipuliert werden.
4. **Drittkomponenten:** Dieses Programm nutzt Open-Source-Bibliotheken (Python, CustomTkinter, ReportLab, pypdf, qrcode).

## 3. Programmbeschreibung & Aufruf (CLI / GUI)
SokoIur eRechnung ist ein Rechnungstool zur Erstellung elektronischer Rechnungen. Es kann komplett über die grafische Oberfläche (GUI) gesteuert werden oder als "Druck-Engine" für externe Programme fungieren.

### Aufruf über Kommandozeile (CLI):
*   `SokoIur_eRechnung.exe --auto [Parameter]` -> Generiert direkt unsichtbar im Hintergrund
*   `SokoIur_eRechnung.exe --edit [Parameter]` -> Öffnet die GUI (Manuelle Eingabe) mit vorgefüllten Daten.

## 3.1 Die Benutzeroberfläche (Tabs) im Detail
*   **📝 ERSTELLEN (Ausgangsrechnungen):** Erfassen und Generieren eigener Ausgangsrechnungen.
*   **📥 ERFASSEN (Eingangsrechnungen):** Prüfung und Archivierung von Lieferantenrechnungen.
*   **📊 AUSGANG (Ausgangsjournal):** Auswertung geschriebener Rechnungen als PDF, CSV oder DATEV-Export.
*   **📊 EINGANG (Eingangsjournal):** Verwalten, Durchsuchen und Stornieren von Eingangsrechnungen.
*   **⚙️ Einst. (Einstellungen):** Konfiguration von Firmen, DATEV-Konten und Stammdaten.
*   **ℹ️ Info:** Dokumentation, Statistiken und Update-Suche.

## 3.2 Die Kommandozeilenparameter (CLI) im Detail
*   `--auto`: Startet die Rechnungserstellung vollautomatisch unsichtbar im Hintergrund.
*   `--edit`: Startet die grafische Oberfläche zur manuellen Nachbearbeitung (inkl. Schutz vor versehentlichem Beenden).
*   `--profil "Name"`: Wählt das Firmenprofil aus (bricht mit Fehler ab, falls Profil unbekannt).
*   `--renr "RE-Nummer"`: Überschreibt die in der CSV enthaltene Rechnungsnummer.
*   `--kunde-az "Aktenzeichen"`: Überschreibt das Aktenzeichen des Kunden.
*   `--rechnung "Pfad"`: Pfad zur einzulesenden `rechnung.csv`.
*   `--kopie "Pfad"`: Zusätzliches Zielverzeichnis für eine Kopie.

## 3.3 Programmfunktionen, Verwendungsszenarien & Anwendungsfälle
*   **Stand-alone vs. Druck-Engine:** Ideal als alleiniges Rechnungswerkzeug für Handwerker oder als CLI-Tool zur Ergänzung von Branchensoftware.
*   **B2G (Behörden):** Pflicht zur XRechnung. E-Mail/Leitweg-ID sowie Schema `0204` eintragen und XRechnung erzeugen.
*   **B2B (Geschäftskunden):** Erfüllt die E-Rechnungspflicht durch die ZUGFeRD-Funktion. Eine Hybrid-PDF enthält das geforderte XML.
*   **Storno & Girocode:** Minusbeträge erzeugen automatische Stornotexte. Der Girocode generiert scannbare EPC-QR-Codes.

## 4. Ordnerstruktur und Dateien
Das Programm trennt strikt zwischen Programmdateien (Installation), lokalen Einstellungen (AppData) und Ihren Firmendaten (Daten-Grundpfad). In den Firmendaten werden automatisch Ordner für Journale (`aausw`, `eausw`) und Archive angelegt.

## 5. Jahreswechsel
Ändern Sie in den "Einstellungen" einfach das "Aktuelle Rechnungsjahr" im Dropdown oder legen Sie ein neues Firmenprofil an.

## 6. Mandanten & Datenbanken
Sie können im Reiter "Einst." verschiedene Firmenprofile verwalten. Das Programm synchronisiert neue Firmen automatisch über den geteilten Daten-Grundpfad.

## 7. Rechnungspositionen, Leistungszeitraum & Duplikate
Ist im Kopf UND in der Position ein Zeitraum angegeben, muss der Positionszeitraum zwingend innerhalb des Kopf-Zeitraums liegen.

## 8. Rechnungsformate, Papierrechnung & elektronische Empfängeradresse
Das Programm unterstützt ZUGFeRD (Hybrid-PDF mit XML), reine XRechnung (XML + Begleit-PDF) und Papierrechnungen (nur als Übergangslösung).

## 9. Datumseingaben
Zulässige Formate: `TTMMJJ`, `TT,MM,JJ`, `TT.MM.JJJJ`, `TT,MM,JJJJ` oder `JJJJ-MM-TT`.

## 10. Standardtexte & Formatierungen
Über "Texte bearbeiten" (`Alt+T`) legen Sie Zahlungsbedingungen (BT-20) und Rechnungsvermerke (BT-22) fest. 
Formatierungs-Kürzel: Zeilenumbruch `~cr`, Fett `~f Text f~`, Kursiv `~k Text k~`.

## 11. Eingangsrechnungen erfassen und auswerten
Legen Sie neue Eingangsrechnungen in den Ordner `reneu`. Das Programm prüft diese automatisiert. Fehlerhafte Belege werden abgewiesen. Nach der erfolgreichen Erfassung wird der Beleg im Archiv (`rchn`) gespeichert und im Journal (`eausw`) vermerkt.

## 11.8 Hinweise zur revisionssicheren Archivierung (Ausblick)
Zur Erfüllung der GoBD wird empfohlen, die generierten Verzeichnisse (`rchn` und `are`) automatisch in einen **WORM-Onlinespeicher** (z.B. via Nextcloud) zu synchronisieren, der eine nachträgliche Veränderung technisch ausschließt.

## 12. DATEV-Export & Buchhaltung
SokoIur eRechnung bietet eine integrierte Exportfunktion für die Finanzbuchhaltung (Stapelverarbeitung im ASCII-CSV / EXTF-Format). 

> **WICHTIGER HINWEIS (BETA-FUNKTION):** 
> Bitte übergeben Sie diese Daten zunächst zwingend nur probeweise und mit Testdaten an Ihren Steuerberater, um den fehlerfreien Import sicherzustellen.

### 12.1 Konfiguration (SKR03 / SKR04)
Unter **⚙️ Einst. -> Firmendaten** finden Sie die DATEV-Konten. Es können Standardkonten (SKR03/SKR04) geladen werden. Erlöse werden für Ausgangsrechnungen, Aufwände für Eingangsrechnungen genutzt.

### 12.2 DATEV-Export erzeugen
In den Reitern **📊 AUSGANG** und **📊 EINGANG** erzeugt der Button **„📈 DATEV-Export erzeugen“** eine DATEV-konforme ASCII-CSV-Datei für den gewählten Monat oder das gesamte Jahr. Rechnungen mit unterschiedlichen Steuersätzen werden automatisch centgenau zerlegt.

## 13. GitHub & Updates
Quellcode und Releases sind auf GitHub einsehbar. Über die Update-Funktion wird die neue Version direkt in Ihr Netzlaufwerk geladen, um die Verteilung an alle Arbeitsplätze zu erleichtern.

## 14. Import-Formate (CSV)
SokoIur eRechnung bietet den Import von Kunden- und Produktdaten sowie das Einlesen von Rechnungsentwürfen an. Alle CSV-Dateien müssen durch ein Semikolon (`;`) getrennt sein.

### 14.1 Kundendaten Importieren
Wenn die Spalte `KundeNr` in der Import-Datei identisch mit einem bestehenden Kunden in der Datenbank ist, werden dessen Daten überschrieben (Update). Ansonsten wird der Kunde neu angelegt. Die CSV muss folgende Kopfzeile aufweisen:
`Name;Strasse;PLZ_Ort;Land;KundeNr;Aktenzeichen;KundeAktenzeichen;Endpoint;EndpointScheme`

### 14.2 Produktdaten Importieren
Importierte Produkte werden an die bestehende Liste angehängt. Die CSV muss folgende Kopfzeile aufweisen:
`Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz`

### 14.3 Rechnungsentwürfe (rechnung.csv)
Die `rechnung.csv` für den externen CLI-Aufruf benötigt feste Spalten. Die Kopfdaten werden in jeder Zeile wiederholt, lediglich die Positionsdaten ändern sich je Zeile.

## 15. Lizenzen & Drittparty-Module
Dieses Programm wurde in Python geschrieben und nutzt folgende Open-Source-Bibliotheken. Wir danken den Entwicklern für ihre Arbeit:

* **Python:** [Python Software Foundation License (PSFL)](https://docs.python.org/3/license.html)
* **CustomTkinter:** [MIT License](https://github.com/TomSchimansky/CustomTkinter/blob/master/LICENSE)
* **ReportLab:** [BSD License](https://www.reportlab.com/open_source/license/)
* **pypdf:** [BSD-3-Clause License](https://github.com/py-pdf/pypdf/blob/main/LICENSE)
* **qrcode:** [BSD-3-Clause License](https://github.com/lincolnloop/python-qrcode/blob/master/LICENSE)

---
© Joachim Sokolowski, Offenbacher Str. 99, 63263 Neu-Isenburg
