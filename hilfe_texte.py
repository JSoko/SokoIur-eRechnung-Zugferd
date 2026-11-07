"""
hilfe_texte.py
--------------
Statische Texte und Dokumentation.
Dieses Modul hält die Anleitungen, den Haftungsausschluss und die Hilfetexte bereit,
welche in der grafischen Oberfläche im Reiter "Hilfe & Doku" angezeigt werden.
"""
# hilfe_texte.py

def get_doku_text(version_string):
    return f"""SokoIur eRechnung
Version: {version_string}

1. INSTALLATION & ERSTEINRICHTUNG
===========================================
Die Anwendung (.exe) ist vollständig portabel und kann in einem beliebigen Ordner auf Ihrem PC oder auf einem freigegebenen Netzwerklaufwerk abgelegt werden.

Automatische Einrichtung:
Beim ersten Start legt das Programm alle benötigten Ordner (z.B. für PDFs und Auswertungen) sowie leere Konfigurations-Dateien (.csv) automatisch für die aktuelle Firma an. Sie müssen nichts zwingend vorab manuell konfigurieren. 

Briefbogen:
Legen Sie in denselben Ordner eine Datei namens "briefbogen.pdf". Diese wird als Hintergrund für die Rechnung verwendet. 
Tipp: Verfügt Ihr Briefbogen über zwei Seiten, nutzt das Programm für die erste Rechnungsseite die erste Seite des Briefbogens. Für alle Folgeseiten nutzt es die zweite Seite. Wenn Ihr Briefbogen nur aus einer Seite besteht, deckt das Programm auf Folgeseiten den oberen Kopfbereich automatisch unsichtbar ab, sodass nur die Fußzeile erhalten bleibt.

2. HAFTUNGSAUSSCHLUSS & DATENSCHUTZ
===========================================
Das Programm "SokoIur eRechnung" wird Ihnen unentgeltlich (als Gefälligkeit / Schenkung) zur Verfügung gestellt. 
Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische Umsetzung der komplexen ZUGFeRD/XRechnung-Spezifikationen, wird hiermit ausdrücklich ausgeschlossen. 
Es wird ausdrücklich darauf hingewiesen, dass auch für das Anerkennen der erstellten Rechnungen durch die Adressaten oder die Finanzämter keinerlei Gewähr oder Haftung übernommen wird.
Die Haftung ist gemäß § 521 BGB auf Vorsatz und grobe Fahrlässigkeit beschränkt. Die Nutzung im geschäftlichen Verkehr erfolgt auf Ihre eigene Gefahr. Bitte prüfen Sie erzeugte Rechnungen stichprobenartig.

Datenschutz / Verbindungen:
Das Programm arbeitet komplett lokal. Ausschließlich zur Updateprüfung, die NICHT automatisch durchgeführt sondern durch den entsprechenden Button vom Benutzer angestoßen wird, wird eine Datenverbindung zu GitHub benötigt und aufgebaut.

3. PROGRAMMBESCHREIBUNG & AUFRUF (CLI / GUI)
===========================================
SokoIur eRechnung ist ein Rechnungstool zur Erstellung ZUGFeRD-konformer PDFs. 
Es kann entweder komplett über die grafische Oberfläche (GUI) gesteuert werden, oder 
es fungiert als "Druck-Engine" für externe Programme.

Aufruf über Kommandozeile (CLI):
erechnung_generator.exe --auto [Parameter]   -> Generiert direkt unsichtbar im Hintergrund
erechnung_generator.exe --edit [Parameter]   -> Öffnet die GUI (Manuelle Eingabe) mit den übergebenen Daten, ohne die Rechnungsnummer automatisch hochzuzählen.

Beispiel für einen CLI-Aufruf:
erechnung_generator.exe --edit --profil "Firma 1" --rechnung "C:\\Temp\\meine_rechnung.csv" --auswertungen "C:\\Temp\\Auswertungen"

Verfügbare CLI-Parameter (überschreiben temporär das aktive Profil):
  --profil         Name des Firmenprofils (z.B. "Firma 1").
  --firma          Pfad zur firma.csv.
  --rechnung       Pfad zur rechnung.csv.
  --briefbogen     Pfad zur briefbogen.pdf.
  --zusatz         Pfad zur zusatz.csv.
  --gruss          Pfad zur gruss.csv.
  --header         Pfad zur header.csv.
  --einleitung     Pfad zur einleitung.csv.
  --ausgabe        Ordner für fertiggestellte PDFs.
  --auswertungen   Ordner für das Rechnungs-Journal.
  --jahr           Zwingt das Programm in ein spezielles Rechnungsjahr.
  --no-open        Verhindert das automatische Öffnen der PDF nach der Erstellung.

4. ORDNERSTRUKTUR UND DATEIEN
===========================================
Das Programm verwendet eine feste Ordnerstruktur, die sich an einem von Ihnen in den Einstellungen gewählten "Daten-Grundpfad" orientiert.

Netzwerkbetrieb & Versionsschutz:
Das Programm (.exe) selbst kann lokal auf verschiedenen Rechnern installiert sein, während der Datenspeicherpfad auf einem freigegebenen Netzwerklaufwerk liegt. So greifen alle Nutzer auf denselben Datenbestand zu.
WICHTIG: Sobald ein Rechner mit einer neueren Programmversion auf die Netzwerkdaten zugreift, wird diese Version in einer unsichtbaren Datei namens "erech.txt" im Daten-Grundpfad hinterlegt. Versucht danach ein Rechner mit einer älteren Programmversion auf diese Daten zuzugreifen, wird der Zugriff zum Schutz vor Datenkorruption blockiert. Das Programm bietet Ihnen dann automatisch an, sich über GitHub auf die aktuelle Version zu aktualisieren, bevor Sie weiterarbeiten können.

Der Ordner für die jeweilige Firma wird automatisch anhand des Firmennamens (ohne Leerzeichen) im Grundpfad generiert. Innerhalb dieses Firmenordners wird folgende Struktur angelegt:

- / (Firmen-Hauptordner) : Hier liegen alle zentralen Stammdaten.
  - firma.csv, rechnung.csv, kunden.csv, produkte.csv, zusatz.csv, gruss.csv, header.csv, einleitung.csv sowie der briefbogen.pdf.
- /ausw/ : Dieser Ordner sammelt alle Dateien und Journale für die Auswertungen.
- /are/ : Hier werden alle Ausgangsrechnungen als fertige PDFs archiviert, automatisch sortiert in Jahresunterordner (z.B. "2026"). Bei einem Jahreswechsel generiert das Programm den neuen Ordner selbstständig. 

5. JAHRESWECHSEL
===========================================
Zum Jahreswechsel (z.B. von 2026 auf 2027) haben Sie zwei Möglichkeiten:
A) Neues Profil anlegen:
Klicken Sie oben auf "+ Neu" und nennen Sie es z.B. "Firma 2027". Das Programm legt automatisch neue, komplett leere Ausgabe- und Auswertungs-Ordner für Sie an.
B) Vorhandenes Profil anpassen:
Gehen Sie in die "Einstellungen", ändern Sie das "Aktuelle Rechnungsjahr" im Dropdown z.B. auf 2027. Die Ordner werden bei Bestätigung generiert.
Um Journale der Vorjahre auszudrucken, wechseln Sie in den Reiter "Auswertungen" und ändern das Jahres-Dropdown einfach auf das alte Jahr (z.B. "2026").

6. MANDANTEN & DATENBANKEN
===========================================
Mandantenfähigkeit (Firmen):
Sie können oben links über das Dropdown-Menü bis zu 5 verschiedene Firmenprofile anlegen. Jede Firma verwaltet ihre eigenen Dateipfade.
WICHTIG: Wenn Sie eine Firma anlegen oder bearbeiten, müssen für eine gültige ZUGFeRD eRechnung mindestens Name, PLZ, Ort, IBAN und USt-Id (bzw. Steuernummer) eingegeben werden!

Firma löschen:
Um ein Profil zu löschen, klicken Sie auf "Löschen".
Das Sicherheitspasswort ist ein kleines Rätsel: Wie lautet die 5-stellige Haupt-Postleitzahl von Neu-Isenburg?

Kundenbank & Produktebank:
Ihre erfassten Kunden und Produkte werden gespeichert. In der Rechnungserfassung dient die "Bezeichnung" und das Suchen-Feld als Auto-Fill für diese Bestände.

7. RECHNUNGSPOSITIONEN & LEISTUNGSZEITRAUM
===========================================
WICHTIG: Ist im Kopf UND in der Position ein Zeitraum angegeben, muss der Positionszeitraum ZWINGEND kalendarisch INNERHALB des Kopf-Zeitraums liegen. (Tipp: Ist Start- und Enddatum identisch, wird auf dem PDF automatisch nur ein einzelnes Datum gedruckt).
Negative Preise (Rabatte) werden automatisch normgerecht berechnet.

8. DATUMSEINGABEN
===========================================
Zulässige Formate: TTMMJJ, TT,MM,JJ, TT.MM.JJJJ, TT,MM,JJJJ oder JJJJ-MM-TT.

9. TEXTFORMATIERUNGEN
===========================================
Zeilenumbruch in der CSV: ~cr
Fett drucken:  ~f Ihr Text f~
Kursiv drucken:~k Ihr Text k~

10. JOURNAL & AUSWERTUNGEN
===========================================
Das Programm erstellt bei jedem Speichervorgang im Hintergrund eine Monats-CSV (z.B. re202611.csv). 
Im Reiter "Auswertungen" können Sie daraus mit einem Klick ein sauberes PDF-Journal erzeugen.

11. GITHUB & UPDATES
===========================================
Der Quellcode des Programms ist auf GitHub einsehbar:
https://github.com/JSoko/SokoIur-eRechnung-Zugferd/releases/new

Neue Versionen können Sie hier herunterladen:
https://github.com/JSoko/SokoIur-eRechnung-Zugferd/releases

12. LIZENZEN & DRITTPARTY-MODULE
===========================================
Dieses Programm wurde in Python geschrieben und nutzt für bestimmte Funktionen Open-Source-Bibliotheken von Drittanbietern. Nachfolgend finden Sie eine Auflistung der verwendeten Hauptkomponenten sowie Links zu deren jeweiligen Lizenzbedingungen:

- Python (Programmiersprache)
  Lizenz: Python Software Foundation License (PSF)
  Link: https://docs.python.org/3/license.html

- CustomTkinter (Für das Design der Benutzeroberfläche)
  Lizenz: MIT License
  Link: https://github.com/TomSchimansky/CustomTkinter/blob/master/LICENSE

- ReportLab (Für die PDF-Generierung des Rechnungslayouts)
  Lizenz: BSD License
  Link: https://bitbucket.org/rptlab/reportlab/src/master/LICENSE.txt

- pypdf (Für das Einbetten der ZUGFeRD XML-Datei in das PDF)
  Lizenz: BSD 3-Clause License
  Link: https://github.com/py-pdf/pypdf/blob/main/LICENSE
"""

HILFE_KAPITEL = [
    ("1. Installation", "1. INSTALLATION"),
    ("2. Haftung", "2. HAFTUNGSAUSSCHLUSS"),
    ("3. CLI & GUI", "3. PROGRAMMBESCHREIBUNG"),
    ("4. Ordnerstruktur", "4. ORDNERSTRUKTUR"),
    ("5. Jahreswechsel", "5. JAHRESWECHSEL"),
    ("6. Mandanten", "6. MANDANTEN"),
    ("7. Positionen", "7. RECHNUNGSPOSITIONEN"),
    ("8. Datumseingaben", "8. DATUMSEINGABEN"),
    ("9. Formatierungen", "9. TEXTFORMATIERUNGEN"),
    ("10. Journal", "10. JOURNAL"),
    ("11. Updates", "11. GITHUB"),
    ("12. Lizenzen", "12. LIZENZEN")
]
