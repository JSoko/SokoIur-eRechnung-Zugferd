# SokoIur-eRechnung-Zugferd
Programm zur Erstellung von Rechnungen im Zugpferd-Format. Auch zum Aufruf durch Drittprogramme

Kompilieren mit

`pyinstaller  --noconfirm --onefile --windowed --icon "SokoIur.ico" --add-data "SokoIur.ico;." --name "SokoIur_eRechnung" main.py`

<img width="1200" height="1096" alt="image" src="https://github.com/user-attachments/assets/1744e5fb-d7f8-4827-8114-61c516adb296" />

# SokoIur eRechnung - Handbuch
**Version: 2.000141**

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
- [14. Import-Format (Beispiel rechnung.csv)](#14-import-format-beispiel-rechnungcsv)
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

## 2. Haftungsausschluss, Support & Datenschutz
Das Programm „SokoIur eRechnung“ wird Ihnen unentgeltlich zur Verfügung gestellt. Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit wird ausdrücklich ausgeschlossen.

> **Kontakt:** Webseite: [https://erech.6078.de](https://erech.6078.de) | E-Mail: SokoIur@6078.de

## 3. Programmbeschreibung & Aufruf (CLI / GUI)
SokoIur eRechnung ist ein Rechnungstool zur Erstellung elektronischer Rechnungen. Es kann komplett über die grafische Oberfläche (GUI) gesteuert werden oder als "Druck-Engine" für externe Programme fungieren.

### Aufruf über Kommandozeile (CLI):
*   `SokoIur_eRechnung.exe --auto [Parameter]` -> Generiert direkt unsichtbar im Hintergrund
*   `SokoIur_eRechnung.exe --edit [Parameter]` -> Öffnet die GUI mit vorgefüllten Daten.

## 12. DATEV-Export & Buchhaltung
SokoIur eRechnung bietet eine integrierte Exportfunktion für die Finanzbuchhaltung (Stapelverarbeitung im ASCII-CSV / EXTF-Format). 

> **WICHTIGER HINWEIS (BETA-FUNKTION):** 
> Bitte übergeben Sie diese Daten zunächst zwingend nur probeweise und mit Testdaten an Ihren Steuerberater, um den fehlerfreien Import sicherzustellen.

### 12.2 DATEV-Export erzeugen
In den Reitern **📊 AUSGANG** und **📊 EINGANG** erzeugt der Button **„📈 DATEV-Export erzeugen“** eine DATEV-konforme ASCII-CSV-Datei für den gewählten Monat oder das gesamte Jahr. Rechnungen mit unterschiedlichen Steuersätzen werden automatisch centgenau zerlegt.

---
© Joachim Sokolowski, Offenbacher Str. 99, 63263 Neu-Isenburg
