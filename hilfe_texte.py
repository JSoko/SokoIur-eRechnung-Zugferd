"""
hilfe_texte.py
--------------
HTML- und Markdown-Generierung für das Handbuch und Changelog.
"""

def get_doku_html(version_string):
    return rf"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SokoIur eRechnung - Handbuch</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #ffffff; }}
        h1, h2, h3 {{ color: #1f538d; }}
        h2 {{ border-bottom: 2px solid #1f538d; padding-bottom: 5px; margin-top: 40px; }}
        a {{ color: #1f538d; text-decoration: none; font-weight: bold; }}
        a:hover {{ text-decoration: underline; }}
        .toc {{ background: #f4f7f6; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #ddd; }}
        .toc ul {{ list-style-type: none; padding: 0; margin: 0; }}
        .toc li {{ margin-bottom: 8px; }}
        .toc-link {{ text-decoration: none; color: #333; font-weight: normal; }}
        .toc-link:hover {{ color: #1f538d; text-decoration: underline; }}
        code {{ background: #eee; padding: 2px 5px; border-radius: 3px; font-family: Consolas, monospace; color: #d63384; }}
        .highlight {{ background-color: #fff3cd; border-left: 4px solid #ffecb5; padding: 10px; margin: 15px 0; }}
        .warning-box {{ background-color: #f9e2e2; border-left: 4px solid #d9534f; padding: 10px; margin: 15px 0; }}
    </style>
</head>
<body>
    <h1>SokoIur eRechnung - Handbuch</h1>
    <p><strong>Version: {version_string}</strong></p>

    <div class="toc">
        <h2 style="margin-top: 0; border: none;">Inhaltsverzeichnis</h2>
        <ul>
            <li><a class="toc-link" href="#kap1">1. Installation & Ersteinrichtung</a></li>
            <li><a class="toc-link" href="#kap2">2. Haftungsausschluss, Support & Datenschutz</a></li>
            <li><a class="toc-link" href="#kap2_1">2.1 Lizenzerklärung</a></li>
            <li><a class="toc-link" href="#kap3">3. Programmbeschreibung & Aufruf (CLI / GUI)</a></li>
            <li><a class="toc-link" href="#kap3_1">3.1 Die Benutzeroberfläche (Tabs) im Detail</a></li>
            <li><a class="toc-link" href="#kap3_2">3.2 Die Kommandozeilenparameter (CLI) im Detail</a></li>
            <li><a class="toc-link" href="#kap3_3">3.3 Programmfunktionen, Verwendungsszenarien & Anwendungsfälle</a></li>
            <li><a class="toc-link" href="#kap4">4. Ordnerstruktur und Dateien</a></li>
            <li><a class="toc-link" href="#kap5">5. Jahreswechsel</a></li>
            <li><a class="toc-link" href="#kap6">6. Mandanten & Datenbanken</a></li>
            <li><a class="toc-link" href="#kap7">7. Rechnungspositionen, Leistungszeitraum & Duplikate</a></li>
            <li><a class="toc-link" href="#kap8">8. Rechnungsformate, Papierrechnung & elektronische Empfängeradresse</a></li>
            <li><a class="toc-link" href="#kap9">9. Datumseingaben</a></li>
            <li><a class="toc-link" href="#kap10">10. Standardtexte & Formatierungen</a></li>
            <li><a class="toc-link" href="#kap11">11. Eingangsrechnungen erfassen und auswerten</a></li>
            <li><a class="toc-link" href="#kap11_rev">11.8 Hinweise zur revisionssicheren Archivierung (Ausblick)</a></li>
            <li><a class="toc-link" href="#kap12">12. DATEV-Export & Buchhaltung</a></li>
            <li><a class="toc-link" href="#kap13">13. GitHub & Updates</a></li>
            <li><a class="toc-link" href="#kap14">14. Import-Format (Beispiel rechnung.csv)</a></li>
            <li><a class="toc-link" href="#kap15">15. Lizenzen & Drittparty-Module</a></li>
        </ul>
    </div>

    <h2 id="kap1">1. Installation & Ersteinrichtung</h2>
    <p>Die Anwendung (<code>.exe</code>) kann in einem beliebigen Ordner auf Ihrem PC abgelegt werden – auch in systemgeschützten Verzeichnissen wie <code>C:\Programme</code>. Lokale Geräteeinstellungen speichert das Programm automatisch sicher in Ihrem Windows-Benutzerverzeichnis (<code>%LOCALAPPDATA%\SokoIur_eRechnung</code>), sodass keine Administratorrechte für den täglichen Betrieb nötig sind.</p>
    <h3>Ersteinrichtung und Datenspeicherort:</h3>
    <p>Beim allerersten Start des Programms werden Sie aufgefordert, einen Grundpfad für die Datenspeicherung auszuwählen.</p>
    <div class="highlight">
        <strong>WICHTIG:</strong> Dieser Ordner darf sich aus Sicherheits- und Updategründen NICHT innerhalb oder unterhalb des Programmordners befinden!<br>
        Wenn Sie das Programm von mehreren Rechnern aus nutzen möchten, wählen Sie hier zwingend ein freigegebenes Netzwerklaufwerk aus.
    </div>
    <p>Anschließend legt das Programm dort alle benötigten Unterordner und leeren Konfigurations-Dateien (<code>.csv</code>) automatisch für Ihre erste Firma an.</p>
    <h3>Briefbogen hinterlegen:</h3>
    <p>Um Ihr eigenes Rechnungsdesign (Logo, Fußzeile etc.) als Hintergrund für die Rechnungen zu verwenden, wechseln Sie in den Reiter <strong>⚙️ Einst.</strong> und klicken Sie im Bereich der Firmendaten auf den Button <strong>„📄 Briefbogen hinterlegen“</strong>. Wählen Sie dort einfach Ihre PDF-Vorlage aus.</p>
    <p><em>Tipp:</em> Verfügt Ihr Briefbogen über zwei Seiten, nutzt das Programm für die erste Rechnungsseite die erste Seite des Briefbogens. Für alle Folgeseiten nutzt es die zweite Seite. Wenn Ihr Briefbogen nur aus einer Seite besteht, deckt das Programm auf Folgeseiten den oberen Kopfbereich automatisch unsichtbar ab.</p>
    
    <h2 id="kap2">2. Haftungsausschluss, Support & Datenschutz</h2>
    <h3>Haftungsausschluss</h3>
    <p>Das Programm „SokoIur eRechnung“ wird Ihnen unentgeltlich zur Verfügung gestellt. Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische Umsetzung der komplexen ZUGFeRD- und XRechnung-Spezifikationen, wird ausdrücklich ausgeschlossen.</p>
    <h3>Gewerbliche Nutzung & Support</h3>
    <p>Die Nutzung ist kostenfrei. Wenn Sie das Programm gewerblich nutzen und die Weiterentwicklung wertschätzen, können Sie eine freiwillige Zahlung leisten. Kostenloser, individueller Support kann nicht geleistet werden.</p>
    <div class="highlight">
        <strong>Kontakt:</strong> Webseite: <a href="https://erech.6078.de" target="_blank">https://erech.6078.de</a> | E-Mail: <a href="mailto:SokoIur@6078.de">SokoIur@6078.de</a>
    </div>

    <h2 id="kap2_1">2.1 Lizenzerklärung (Freeware / Donationware)</h2>
    <p><strong>1. Nutzungsrechte:</strong> Das Programm (ausführbare Datei) wird als Freeware/Donationware bereitgestellt. Die private und gewerbliche Nutzung ist kostenfrei gestattet.</p>
    <p><strong>2. Weitergabe:</strong> Die Software darf unverändert kostenlos weitergegeben werden. Kommerzieller Vertrieb ist untersagt.</p>
    <p><strong>3. Quellcode:</strong> Der Quellcode ist auf GitHub einsehbar. Die .exe darf nicht dekompiliert oder manipuliert werden.</p>
    <p><strong>4. Drittkomponenten:</strong> Dieses Programm nutzt Open-Source-Bibliotheken (Python, CustomTkinter, ReportLab, pypdf, qrcode).</p>
    
    <h2 id="kap3">3. Programmbeschreibung & Aufruf (CLI / GUI)</h2>
    <p>SokoIur eRechnung ist ein Rechnungstool zur Erstellung elektronischer Rechnungen. Es kann komplett über die grafische Oberfläche (GUI) gesteuert werden oder als "Druck-Engine" für externe Programme fungieren.</p>
    <h3>Aufruf über Kommandozeile (CLI):</h3>
    <ul>
        <li><code>SokoIur_eRechnung.exe --auto [Parameter]</code> &rarr; Generiert direkt unsichtbar im Hintergrund</li>
        <li><code>SokoIur_eRechnung.exe --edit [Parameter]</code> &rarr; Öffnet die GUI (Manuelle Eingabe) mit vorgefüllten Daten.</li>
    </ul>

    <h2 id="kap3_1">3.1 Die Benutzeroberfläche (Tabs) im Detail</h2>
    <h3>📝 ERSTELLEN (Ausgangsrechnungen schreiben)</h3>
    <p>Hier erfassen und generieren Sie Ihre eigenen Ausgangsrechnungen an Kunden inkl. automatischer Steuerberechnung.</p>
    <h3>📥 ERFASSEN (Eingangsrechnungen prüfen)</h3>
    <p>Haltautomatisierte Prüfung, Erfassung und Archivierung von Rechnungen Ihrer Lieferanten (Prüfung nach EN 16931 / § 14 UStG).</p>
    <h3>📊 AUSGANG (Ausgangsjournal)</h3>
    <p>Auswertung der geschriebenen Rechnungen als PDF, CSV oder DATEV-Export.</p>
    <h3>📊 EINGANG (Eingangsjournal & Verwaltung)</h3>
    <p>Durchsuchen, Verwalten und Auswerten der erfassten Eingangsrechnungen (Storno-Funktion inklusive).</p>
    <h3>⚙️ Einst. (Einstellungen & Stammdaten)</h3>
    <p>Zentrale Konfiguration Ihrer Firmen, Nummernkreise, DATEV-Konten und Stammdaten.</p>
    <h3>ℹ️ Info (Hilfe & Statistik)</h3>
    <p>Dokumentation, Version, Statistiken und Update-Suche.</p>
    
    <h2 id="kap3_2">3.2 Die Kommandozeilenparameter (CLI) im Detail</h2>
    <ul>
        <li><code>--auto</code>: Startet die Rechnungserstellung vollautomatisch unsichtbar im Hintergrund.</li>
        <li><code>--edit</code>: Startet die grafische Oberfläche, füllt die Maske mit übergebenen Daten vor.</li>
        <li><code>--profil "Name"</code>: Wählt das Firmenprofil aus.</li>
        <li><code>--renr "RE-Nummer"</code>: Überschreibt die in der CSV enthaltene Rechnungsnummer.</li>
        <li><code>--rechnung "Pfad"</code>: Pfad zur einzulesenden <code>rechnung.csv</code> (z.B. Export-Datei).</li>
        <li><code>--kopie "Pfad"</code>: Zusätzliches Zielverzeichnis für eine Kopie der generierten Rechnung.</li>
    </ul>

    <h2 id="kap3_3">3.3 Programmfunktionen, Verwendungsszenarien & Anwendungsfälle</h2>
    <h3>Kernfunktionen des Programms</h3>
    <ul>
        <li><strong>eRechnungserstellung:</strong> Generierung von normkonformen ZUGFeRD- (Hybrid-PDF) und XRechnungen (XML) inkl. Leseabschrift.</li>
        <li><strong>Eingangsrechnungs-Verarbeitung:</strong> Automatisierte formelle Prüfung, Duplikatskontrolle (Hash & Inhalt) und revisionsvorbereitende Archivierung von Eingangsbelegen.</li>
        <li><strong>Stammdatenverwaltung:</strong> Pflege von mehreren Firmenprofilen (Mandantenfähigkeit), Kunden-, Produkt- und Text-Datenbanken.</li>
        <li><strong>Buchhaltung & Export:</strong> Erstellung von Journalen für Ein- und Ausgang sowie direkter DATEV-Export (EXTF) inkl. automatischem Steuer-Splitting.</li>
        <li><strong>Automatisierung (CLI):</strong> Fernsteuerung über Kommandozeilenparameter zur nahtlosen Integration in Dritt-Software.</li>
        <li><strong>Netzwerkbetrieb:</strong> Lokale Installation mit zentralem Datenspeicher auf Netzlaufwerken zur parallelen Nutzung inkl. File-Locking.</li>
    </ul>

    <h3>Typische Verwendungsszenarien</h3>
    <div class="highlight">
        <strong>Szenario A: Standalone-Lösung (Freiberufler & Handwerker)</strong><br>
        Ein Unternehmer nutzt das Tool als primäres Abrechnungswerkzeug. Er pflegt Kunden und Artikel im Programm, schreibt seine Rechnungen über die Maske, prüft eingehende Belege und erzeugt am Monatsende mit einem Klick den DATEV-Export.
    </div>
    <div class="highlight">
        <strong>Szenario B: Integrierte "Druck-Engine" (Mittelstand)</strong><br>
        Ein Unternehmen nutzt eine Branchensoftware, die Rechnungen nur als einfache CSV-Liste ausgibt. SokoIur eRechnung wird per Kommandozeile (<code>--auto</code>) aufgerufen, liest die CSV ein, bettet sie in den Briefbogen ein und generiert vollautomatisch eine ZUGFeRD-PDF für den Versand, ohne dass der Anwender die GUI sieht.
    </div>

    <h3>Spezifische Anwendungsfälle (Use Cases)</h3>
    <ul>
        <li><strong>Rechnung an Behörden (B2G - XRechnung):</strong> Für Rechnungen an öffentliche Auftraggeber (Bund, Länder, Kommunen) ist das XRechnung-Format verpflichtend. Tragen Sie bei der Rechnungserstellung im Feld "E-Mail / Leitweg-ID" die vom Amt mitgeteilte <strong>Leitweg-ID</strong> ein und setzen Sie das "Endpoint-Schema" auf <code>0204</code>. Klicken Sie anschließend auf "XRechnung erstellen". Das Programm generiert die reine XML-Datei für den Upload in Portale (z.B. ZRE, OZG-RE) und zusätzlich ein übersichtliches Lese-PDF für Ihre eigenen Akten.</li>
        <li><strong>Rechnung an Geschäftskunden (B2B - E-Rechnungspflicht ab 2027/2028):</strong> Gemäß Wachstumschancengesetz gilt für inländische B2B-Umsätze schrittweise eine E-Rechnungspflicht (Übergangsregelungen bis Ende 2026 bzw. 2027 je nach Umsatz). Um diese Gesetzesvorgaben zu erfüllen, nutzen Sie idealerweise den Button <strong>"Zugpferdrechnung erstellen" (ZUGFeRD)</strong>. Hierfür reicht als Empfängeradresse die reguläre E-Mail-Adresse (Endpoint-Schema: <code>EM</code>). Sie erhalten <em>eine einzige</em> PDF-Datei, die vom Menschen gelesen werden kann und gleichzeitig die nach EN 16931 geforderten XML-Daten unsichtbar in sich trägt. Diese Datei können Sie einfach per E-Mail an Ihre Kunden versenden.</li>
        <li><strong>Stornorechnung erstellen:</strong> Über "Rechnungs-CSV wählen" wird eine alte Rechnung geladen. Die Beträge werden manuell ins Minus gesetzt und das Programm ändert bei der Generierung automatisch die Hinweistexte ("Dieser Beleg weist ein Guthaben aus...").</li>
        <li><strong>Girocode für Schnellzahler:</strong> Wird der "Girocode" in den Firmeneinstellungen aktiviert, druckt das Programm einen normierten EPC-QR-Code auf die Rechnung. Der Kunde kann diesen mit seiner Banking-App scannen, sodass IBAN, Betrag und Verwendungszweck (Rechnungsnummer) fehlerfrei übernommen werden.</li>
    </ul>

    <h2 id="kap4">4. Ordnerstruktur und Dateien</h2>
    <p>Das Programm trennt strikt zwischen Programmdateien (Installation), lokalen Einstellungen (AppData) und Ihren Firmendaten (Daten-Grundpfad auf dem Laufwerk). In den Firmendaten legt das Programm automatisch alle relevanten Ordner für Journale (<code>aausw</code>, <code>eausw</code>) und Archive an.</p>

    <h2 id="kap5">5. Jahreswechsel</h2>
    <p>Ändern Sie in den "Einstellungen" einfach das "Aktuelle Rechnungsjahr" im Dropdown oder legen Sie ein neues Firmenprofil an.</p>

    <h2 id="kap6">6. Mandanten, Datenbanken & Firmendaten</h2>
    <p>Sie können im Reiter "Einst." verschiedene Firmenprofile verwalten. Das Programm synchronisiert neue Firmen automatisch über den geteilten Daten-Grundpfad.</p>

    <h2 id="kap7">7. Rechnungspositionen, Leistungszeitraum & Duplikate</h2>
    <p>Ist im Kopf UND in der Position ein Zeitraum angegeben, muss der Positionszeitraum zwingend innerhalb des Kopf-Zeitraums liegen.</p>

    <h2 id="kap8">8. Rechnungsformate, Papierrechnung & elektronische Empfängeradresse</h2>
    <p>Das Programm unterstützt ZUGFeRD (Hybrid-PDF mit XML), reine XRechnung (XML + Begleit-PDF) und Papierrechnungen (nur als Übergangslösung).</p>

    <h2 id="kap9">9. Datumseingaben</h2>
    <p>Zulässige Formate: <code>TTMMJJ, TT,MM,JJ, TT.MM.JJJJ, TT,MM,JJJJ</code> oder <code>JJJJ-MM-TT</code>.</p>

    <h2 id="kap10">10. Standardtexte & Formatierungen</h2>
    <p>Über "Texte bearbeiten" (<code>Alt+T</code>) legen Sie Zahlungsbedingungen (BT-20) und Rechnungsvermerke (BT-22) fest. Formatierungs-Kürzel: Zeilenumbruch <code>~cr</code>, Fett <code>~f Text f~</code>, Kursiv <code>~k Text k~</code>.</p>

    <h2 id="kap11">11. Eingangsrechnungen erfassen und auswerten</h2>
    <p>Legen Sie neue Eingangsrechnungen in den Ordner <code>reneu</code>. Das Programm prüft diese automatisiert. Fehlerhafte Belege werden abgewiesen. Nach der erfolgreichen Erfassung wird der Beleg im Archiv (<code>rchn</code>) gespeichert und im Journal (<code>eausw</code>) vermerkt.</p>

    <h2 id="kap11_rev">11.8 Hinweise zur revisionssicheren Archivierung (Ausblick)</h2>
    <p>Zur Erfüllung der GoBD wird empfohlen, die generierten Verzeichnisse (<code>rchn</code> und <code>are</code>) automatisch in einen <strong>WORM-Onlinespeicher</strong> (z.B. via Nextcloud) zu synchronisieren, der eine nachträgliche Veränderung technisch ausschließt.</p>

    <h2 id="kap12">12. DATEV-Export & Buchhaltung</h2>
    <p>SokoIur eRechnung bietet eine integrierte Exportfunktion für die Finanzbuchhaltung, die speziell auf den Import in DATEV-Rechnungswesen (Stapelverarbeitung im ASCII-CSV / EXTF-Format) zugeschnitten ist.</p>
    
    <div class="warning-box">
        <strong style="color: #d9534f;">WICHTIGER HINWEIS (BETA-FUNKTION):</strong><br>
        Die DATEV-Exportfunktionen sind neu implementiert und wurden <strong>bisher nicht abschließend in einer produktiven DATEV-Umgebung getestet</strong>. Bitte übergeben Sie diese Daten zunächst zwingend nur probeweise und mit Testdaten an Ihren Steuerberater, um den fehlerfreien Import (z.B. Feldzuordnungen, Längenbeschränkungen) sicherzustellen. Für buchhalterische Schäden oder Mehraufwand wird keine Haftung übernommen!
    </div>

    <h3>12.1 Konfiguration (SKR03 / SKR04)</h3>
    <p>Wechseln Sie in den Reiter <strong>⚙️ Einst.</strong> und klicken Sie auf <strong>„📈 DATEV-Konten“</strong>. Hier können Sie die Standardkonten für die gängigen Kontenrahmen SKR03 oder SKR04 laden oder individuelle Sachkonten pflegen:</p>
    <ul>
        <li><strong>Erlöskonten (Ausgangsrechnungen):</strong> Getrennte Konten für 19%, 7% und 0% USt.</li>
        <li><strong>Aufwandskonten (Eingangsrechnungen):</strong> Getrennte Konten für 19%, 7% und 0% Vorsteuer.</li>
        <li><strong>Sammelkonten:</strong> Pflege von zentralen Debitoren- (z.B. 10000) und Kreditorenkonten (z.B. 70000), sofern Sie nicht mit Personenkonten pro Kunde arbeiten.</li>
    </ul>

    <h3>12.2 DATEV-Export erzeugen</h3>
    <p>In den Reitern <strong>📊 AUSGANG</strong> und <strong>📊 EINGANG</strong> erzeugt der Button <strong>„📈 DATEV-Export erzeugen“</strong> eine DATEV-konforme ASCII-CSV-Datei für den gewählten Monat oder das gesamte Jahr.</p>
    <p>Das Programm nimmt Ihrem Steuerberater dabei folgende Arbeit ab:</p>
    <ul>
        <li><strong>Automatisches Steuer-Splitting:</strong> Rechnungen, die Positionen mit unterschiedlichen Steuersätzen enthalten, werden automatisch centgenau zerlegt. Das Programm berechnet den anteiligen Bruttobetrag pro Steuersatz exakt zurück und erzeugt dafür jeweils eine eigene Buchungszeile.</li>
        <li><strong>Soll/Haben-Kennzeichen (S/H):</strong> Die Kennzeichen werden intelligent vergeben (Erlöse aus Ausgangsrechnungen = Haben, Aufwände aus Eingangsrechnungen = Soll).</li>
        <li><strong>Daten-Mapping:</strong> Die generierte CSV enthält die 7 Pflichtspalten, die für die DATEV-Stapelverarbeitung zwingend benötigt werden: <em>Umsatz (ohne Soll/Haben-Kz), Soll/Haben-Kennzeichen, Konto, Gegenkonto (BU-Schlüssel), Belegdatum (TTMM), Belegfeld 1 (Rechnungsnummer), Buchungstext (Lieferant/Kunde)</em>.</li>
    </ul>

    <h2 id="kap13">13. GitHub & Updates</h2>
    <p>Quellcode und Releases sind auf GitHub einsehbar. Über die Update-Funktion wird die neue Version direkt in Ihr Netzlaufwerk geladen, um die Verteilung an alle Arbeitsplätze zu erleichtern.</p>

    <h2 id="kap14">14. Import-Formate (CSV)</h2>
    <p>SokoIur eRechnung bietet den Import von Kunden- und Produktdaten sowie das Einlesen von Rechnungsentwürfen an. Alle CSV-Dateien müssen durch ein Semikolon (<code>;</code>) getrennt und im Format UTF-8 vorliegen (bei ANSI-Dateien aus Excel führt das Programm eine automatische Reparatur durch).</p>
    
    <h3>14.1 Kundendaten Importieren</h3>
    <p>Wechseln Sie in die Einstellungen und nutzen Sie den Button "Kunden importieren (CSV)". Wenn die Spalte <code>KundeNr</code> in der Import-Datei identisch mit einem bestehenden Kunden in der Datenbank ist, werden dessen Daten überschrieben (Update-Funktion). Ansonsten wird der Kunde neu angelegt. Die CSV muss folgende Kopfzeile exakt aufweisen:</p>
    <code>Name;Strasse;PLZ_Ort;Land;KundeNr;Aktenzeichen;KundeAktenzeichen;Endpoint;EndpointScheme</code>
    
    <h3>14.2 Produktdaten Importieren</h3>
    <p>Nutzen Sie in den Einstellungen den Button "Produkte importieren (CSV)". Importierte Produkte werden immer an die bestehende Liste angehängt. Die CSV muss folgende Kopfzeile exakt aufweisen:</p>
    <code>Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz</code>
    
    <h3>14.3 Rechnungsentwürfe (rechnung.csv)</h3>
    <p>Die <code>rechnung.csv</code> für den externen CLI-Aufruf benötigt feste Spalten. Die Kopfdaten werden in jeder Zeile wiederholt, lediglich die Positionsdaten ändern sich je Zeile.</p>
    <h2 id="kap15">15. Lizenzen & Drittparty-Module</h2>
    <p>Dieses Programm wurde in Python geschrieben und nutzt folgende Open-Source-Bibliotheken. Wir danken den Entwicklern für ihre Arbeit:</p>
    <ul>
        <li><strong>Python:</strong> <a href="https://docs.python.org/3/license.html" target="_blank">Python Software Foundation License (PSFL)</a></li>
        <li><strong>CustomTkinter:</strong> <a href="https://github.com/TomSchimansky/CustomTkinter/blob/master/LICENSE" target="_blank">MIT License</a></li>
        <li><strong>ReportLab:</strong> <a href="https://www.reportlab.com/open_source/license/" target="_blank">BSD License</a></li>
        <li><strong>pypdf:</strong> <a href="https://github.com/py-pdf/pypdf/blob/main/LICENSE" target="_blank">BSD-3-Clause License</a></li>
        <li><strong>qrcode:</strong> <a href="https://github.com/lincolnloop/python-qrcode/blob/master/LICENSE" target="_blank">BSD-3-Clause License</a></li>
    </ul>
    
    <hr style="border: 0; border-top: 1px solid #ddd; margin: 40px 0 20px 0;">
    <p style="text-align: center; color: #666; font-size: 0.9em;">
        &copy; Joachim Sokolowski, Offenbacher Str. 99, 63263 Neu-Isenburg
    </p>
    <br><br><br>
</body>
</html>"""

def get_doku_body_html(version_string):
    full_html = get_doku_html(version_string)
    start_marker = "<body>"
    end_marker = '<hr style="border: 0; border-top: 1px solid #ddd; margin: 40px 0 20px 0;">'
    start_pos = full_html.find(start_marker)
    end_pos = full_html.find(end_marker)
    if start_pos != -1 and end_pos != -1:
        return full_html[start_pos + len(start_marker):end_pos].strip()
    return "<p>Handbuch-Inhalt konnte nicht extrahiert werden.</p>"

def get_changelog_html(version_string):
    return rf"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Changelog - SokoIur eRechnung</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #ffffff; }}
        h1, h2, h3 {{ color: #1f538d; }}
        h2 {{ border-bottom: 2px solid #1f538d; padding-bottom: 5px; margin-top: 40px; }}
        h3 {{ margin-top: 25px; margin-bottom: 10px; color: #d63384; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 10px; }}
    </style>
</head>
<body>
    <h1>Changelog – SokoIur eRechnung</h1>
    <p><strong>Aktuelle Version: {version_string}</strong></p>

    <h2>Version 2.000146</h2>
    <h3>✨ Neue Funktionen & Datenverwaltung</h3>
    <ul>
        <li><strong>Firma leeren:</strong> Eine neue Funktion in den Einstellungen ermöglicht es, alle erfassten Buchungen, Rechnungen und Journale einer Firma vollständig zurückzusetzen. Stammdaten (Kunden, Produkte, Briefbogen) bleiben dabei unberührt.</li>
        <li><strong>CSV-Import für Kunden:</strong> Kundendaten können nun per CSV importiert werden. Anhand der Kundennummer werden bestehende Einträge automatisch überschrieben und aktualisiert, neue Kunden werden angehängt.</li>
        <li><strong>CSV-Import für Produkte:</strong> Produktdaten können ab sofort aus einer CSV-Datei importiert und an den bestehenden Stamm angehängt werden.</li>
        <li><strong>Dokumentation:</strong> Das Handbuch wurde um die genauen Import-Formate (Kopfzeilen) für Kunden und Produkte ergänzt.</li>
    </ul>

    <h2>Version 2.000134</h2>
    <h3>✨ DATEV-Export & Buchhaltung</h3>
    <ul>
        <li><strong>Automatischer DATEV-Export:</strong> In den Reitern „Ausgang“ und „Eingang“ können nun vollautomatisch DATEV-konforme ASCII-CSV-Dateien (Stapelverarbeitung) für den Steuerberater erzeugt werden.</li>
        <li><strong>Steuer-Splitting:</strong> Rechnungen mit unterschiedlichen Steuersätzen werden beim DATEV-Export automatisch centgenau zerlegt und auf die jeweils passenden Sachkonten aufgeteilt. Die Soll/Haben-Kennzeichen (S/H) werden vom System intelligent vergeben.</li>
        <li><strong>DATEV-Konfigurationsmanager:</strong> Im Reiter „Einst.“ wurde ein Manager für die DATEV-Buchhaltung hinzugefügt. Per Knopfdruck lassen sich hier die Standardkonten für den Kontenrahmen <strong>SKR03</strong> oder <strong>SKR04</strong> laden oder individuelle Aufwands-, Erlös- und Sammelkonten pflegen.</li>
    </ul>

    <h3>✨ Journale & Auswertungen</h3>
    <ul>
        <li><strong>Neue Export-Möglichkeiten:</strong> In den Reitern „Ausgang“ und „Eingang“ wurden Buttons für den direkten CSV-Export hinzugefügt. Journale lassen sich nun auf Knopfdruck wahlweise als PDF (für den Ausdruck) oder als CSV (für den Import in Fremdsysteme oder Excel) generieren.</li>
        <li><strong>Automatischer Start:</strong> Nach der Generierung wird das erzeugte Journal (egal ob PDF oder CSV) nun direkt in der jeweiligen Standardanwendung Ihres Computers geöffnet, sodass lange Lade-Rückmeldungen entfallen.</li>
        <li><strong>Klarere Ordnerstruktur:</strong> Zur besseren logischen Trennung wurden die systemseitigen Journal-Ordner von <code>ausw</code> auf <code>aausw</code> (Ausgangsauswertungen) und von <code>einj</code> auf <code>eausw</code> (Eingangsauswertungen) umbenannt. Die entsprechenden Pfade werden bei neuen Profilen automatisch korrekt gesetzt.</li>
        <li><strong>Bugfix PDF-Engine:</strong> Ein iterativer Fehler bei der Erzeugung des Ausgangsjournals (PDF) wurde behoben, der durch falsch übergebene String-Variablen auftreten konnte.</li>
    </ul>

    <h3>✨ Bugfixes & CLI-Verbesserungen</h3>
    <ul>
        <li><strong>Firmendaten (Falzmarken):</strong> Ein Fehler beim Speichern der Firmendaten wurde behoben. Das Feld 'Falzmarken' wurde korrekt in die Datenbankstruktur aufgenommen, sodass Änderungen nun fehlerfrei gesichert werden.</li>
        <li><strong>CLI/Edit-Modus (Temp-Dateien):</strong> Wird die GUI über ein Fremdprogramm mit einer temporären CSV-Datei aufgerufen, überschreibt diese nicht mehr fälschlicherweise den Pfad der echten Rechnungsdatenbank.</li>
        <li><strong>Briefbogen-Ladefehler:</strong> Der Briefbogen wird nun auch im Edit-Modus (bei externen Aufrufen) immer zuverlässig und direkt aus dem echten Firmen-Profil geladen, anstatt im Temp-Ordner gesucht zu werden.</li>
        <li><strong>CLI-Parameter --renr:</strong> Übergebene Rechnungsnummern aus Fremdprogrammen überschreiben in der GUI nun korrekt den alten Wert aus der CSV-Datei. Unnötige Duplikats-Warnungen bei der automatisierten Rechnungserstellung wurden beseitigt.</li>
        <li><strong>Einstellungen (Beispielaufruf):</strong> Der CLI-Beispielbefehl in den Einstellungen lässt sich nun markieren und herauskopieren (Read-Only Feld). Er aktualisiert sich zudem in Echtzeit, sobald die letzte Rechnungsnummer manuell korrigiert wird.</li>
        <li><strong>Code-Bereinigung:</strong> Unbenutzte Code-Fragmente wurden zur Fehlervermeidung aus den GUI-Modulen entfernt.</li>
    </ul>

    <h3>📚 Dokumentation & Handbuch-Erweiterung</h3>
    <ul>
        <li><strong>Funktionsübersicht & Anwendungsfälle:</strong> Das integrierte Handbuch wurde um das neue Kapitel 3.3 ("Programmfunktionen, Verwendungsszenarien & Anwendungsfälle") erweitert. Die Unterschiede zwischen der Rechnungsstellung an Behörden (XRechnung via Leitweg-ID / ZRE-Portal) und an Geschäftskunden gemäß der kommenden E-Rechnungspflicht 2025-2028 (ZUGFeRD via E-Mail) werden klar herausgestellt.</li>
        <li><strong>DATEV-Export Dokumentation:</strong> Das Handbuch (Kapitel 12) wurde um eine ausführliche technische Dokumentation der neuen DATEV-Exportfunktionen inkl. ausdrücklichem <strong>Beta-Warnhinweis</strong> (Testlauf mit Steuerberater erforderlich) erweitert.</li>
    </ul>

    <h2>10.11.2026</h2>
    <h3>✨ Neue Funktionen & XML-Korrekturen</h3>
    <ul>
        <li><strong>Automatische UTF-8-Konvertierung:</strong> Werden fehlerhaft codierte Rechnungs-CSVs über die Kommandozeile oder die GUI geladen, repariert und konvertiert das Programm diese nun vollautomatisch in das benötigte UTF-8-Format.</li>
        <li><strong>Referenzen normkonform getrennt:</strong> Das Feld "Ihr Zeichen" (KundeAktenzeichen) wird als echte Leitweg-Referenz (BuyerReference BT-13) übergeben. Das interne Feld "Unser Zeichen" (Aktenzeichen) wird standardkonform als Rechnungsnotiz (IncludedNote) in die XML geschrieben.</li>
        <li><strong>Kommandozeilen-Erweiterung:</strong> Das Kunden-Aktenzeichen kann nun per Parameter <code>--kunde-az</code> gesetzt werden.</li>
    </ul>

    <h2>09.11.2026</h2>
    <h3>📚 Dokumentation & Handbuch-Erweiterung</h3>
    <ul>
        <li><strong>Revisionssichere Archivierung (Kapitel 11.8):</strong> Das Handbuch wurde um ein dediziertes Kapitel zur revisionssicheren Archivierung nach GoBD in Kombination mit Nextcloud & WORM-Speichern ergänzt.</li>
    </ul>
    <h3>⚡ Performance & Fehlerbehebungen (Bugfixes)</h3>
    <ul>
        <li><strong>Statistik-Korrektur:</strong> Die Zählung der erstellten Ausgangsrechnungen im Reiter „Info“ wurde korrigiert.</li>
        <li><strong>Performance-Boost im Eingangsordner:</strong> Das Einlesen und Prüfen von Eingangsrechnungen wurde extrem beschleunigt (Caching der Journal-Datenbasis).</li>
    </ul>
    <h3>🛠 System & Architektur</h3>
    <ul>
        <li><strong>Neues Update-System:</strong> Die Update-Prüfung erfolgt nun über erech.6078.de. Updates werden automatisch in das Netzlaufwerk kopiert.</li>
        <li><strong>AppData-Nutzung:</strong> Lokale Konfigurationsdateien werden ab sofort sicher im Windows-Benutzerverzeichnis (<code>%LOCALAPPDATA%</code>) abgelegt, was UAC-Berechtigungskonflikte behebt.</li>
    </ul>

    <hr style="border: 0; border-top: 1px solid #ddd; margin: 40px 0 20px 0;">
</body>
</html>"""

def get_changelog_body_html(version_string):
    full_html = get_changelog_html(version_string)
    start_marker = "<body>"
    end_marker = '<hr style="border: 0; border-top: 1px solid #ddd; margin: 40px 0 20px 0;">'
    start_pos = full_html.find(start_marker)
    end_pos = full_html.find(end_marker)
    if start_pos != -1 and end_pos != -1:
        return full_html[start_pos + len(start_marker):end_pos].strip()
    return "<p>Changelog-Inhalt konnte nicht extrahiert werden.</p>"

def get_doku_md(version_string):
    return f"""# SokoIur eRechnung - Handbuch
**Version: {version_string}**

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
Die Anwendung (`.exe`) kann in einem beliebigen Ordner auf Ihrem PC abgelegt werden – auch in systemgeschützten Verzeichnissen wie `C:\\Programme`. Lokale Geräteeinstellungen speichert das Programm automatisch sicher in Ihrem Windows-Benutzerverzeichnis (`%LOCALAPPDATA%\\SokoIur_eRechnung`), sodass keine Administratorrechte für den täglichen Betrieb nötig sind.

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
*   `--edit`: Startet die grafische Oberfläche, füllt die Maske mit übergebenen Daten vor.
*   `--profil "Name"`: Wählt das Firmenprofil aus.
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
"""

def get_changelog_md(version_string):
    return f"""# Changelog – SokoIur eRechnung
**Aktuelle Version: {version_string}**

## Version 2.000146
### ✨ Neue Funktionen & Datenverwaltung
*   **Firma leeren:** Eine neue Funktion in den Einstellungen ermöglicht das vollständige Zurücksetzen aller Journale und Rechnungen einer Firma, bei Erhalt der Stammdaten.
*   **CSV-Import für Kunden:** Kundendaten können importiert werden. Anhand der Kundennummer erfolgt ein Update bestehender Kunden, ansonsten werden sie angehängt.
*   **CSV-Import für Produkte:** Produktdaten können aus CSV importiert und angehängt werden.
*   **Dokumentation:** Genaue Import-Strukturen ins Handbuch aufgenommen.

### 📚 Dokumentation
*   **Markdown-Support:** Handbuch und Changelog werden im AppData-Ordner nun zusätzlich im standardisierten Markdown-Format (`.md`) generiert.
*   **Ressourcenschonend:** Die Hilfedateien werden nur noch dann neu auf die Festplatte geschrieben, wenn das Programm einen tatsächlichen Versionssprung (erstmaliger Start nach einem Update) registriert.

## Version 2.000134
### ✨ DATEV-Export & Buchhaltung
*   **Automatischer DATEV-Export:** In den Reitern „Ausgang“ und „Eingang“ können nun vollautomatisch DATEV-konforme ASCII-CSV-Dateien (Stapelverarbeitung) für den Steuerberater erzeugt werden.
*   **Steuer-Splitting:** Rechnungen mit unterschiedlichen Steuersätzen werden beim DATEV-Export automatisch centgenau zerlegt.

### ✨ Journale & Auswertungen
*   **Neue Export-Möglichkeiten:** In den Reitern „Ausgang“ und „Eingang“ wurden Buttons für den direkten CSV-Export hinzugefügt.
*   **Klarere Ordnerstruktur:** Die systemseitigen Journal-Ordner wurden von `ausw` auf `aausw` und von `einj` auf `eausw` umbenannt.

### ✨ Bugfixes & CLI-Verbesserungen
*   **Firmendaten (Falzmarken):** Ein Fehler beim Speichern der Firmendaten wurde behoben.
*   **CLI-Parameter --renr:** Übergebene Rechnungsnummern aus Fremdprogrammen überschreiben in der GUI nun korrekt den alten Wert aus der CSV-Datei.

## 10.11.2026
### ✨ Neue Funktionen & XML-Korrekturen
*   **Automatische UTF-8-Konvertierung:** Fehlerhaft codierte Rechnungs-CSVs (z. B. ANSI/Excel) werden repariert und in UTF-8 konvertiert.
*   **Kommandozeilen-Erweiterung:** Das Kunden-Aktenzeichen kann nun per Parameter `--kunde-az` gesetzt werden.
"""