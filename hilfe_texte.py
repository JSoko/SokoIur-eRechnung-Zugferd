"""
hilfe_texte.py
--------------
HTML- und Markdown-Generierung für das Handbuch und Changelog.
"""
import re

def get_doku_html(version_string):
    return rf"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SokoIur eRechnung - Handbuch</title>
    <style>
        html {{ background-color: #e9ecef; scroll-behavior: smooth; }}
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.7; color: #333; max-width: 1300px; margin: 40px auto; padding: 0 20px; display: flex; gap: 30px; }}
        .sidebar {{ flex: 0 0 300px; position: sticky; top: 40px; height: calc(100vh - 80px); overflow-y: auto; background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); }}
        .main-content {{ flex: 1; background-color: #ffffff; padding: 50px 60px; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); min-width: 0; }}
        h1 {{ color: #1f538d; text-align: center; margin-bottom: 5px; font-size: 2.2em; }}
        p.version {{ text-align: center; color: #6c757d; margin-top: 0; margin-bottom: 40px; }}
        h2 {{ color: #1f538d; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-top: 50px; font-size: 1.6em; }}
        h3 {{ color: #2c3e50; margin-top: 30px; font-size: 1.2em; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; color: #004999; }}
        p, li {{ font-size: 15px; }}
        .toc ul {{ list-style-type: none; padding: 0; margin: 0; }}
        .toc li {{ margin-bottom: 12px; font-size: 14px; }}
        .toc-link {{ color: #495057; text-decoration: none; display: block; transition: all 0.2s; border-left: 2px solid transparent; padding-left: 10px; margin-left: -12px; }}
        .toc-link:hover {{ color: #1f538d; font-weight: bold; border-left: 2px solid #1f538d; background: #f8f9fa; }}
        code {{ background: #f1f3f5; padding: 3px 6px; border-radius: 4px; font-family: 'Consolas', monospace; color: #d63384; font-size: 0.95em; }}
        .highlight {{ background-color: #f8fbff; border-left: 5px solid #6fa8dc; padding: 15px 20px; margin: 25px 0; border-radius: 0 8px 8px 0; }}
        .warning-box {{ background-color: #fff5f5; border-left: 5px solid #e06666; padding: 15px 20px; margin: 25px 0; border-radius: 0 8px 8px 0; color: #990000; }}
        .badge-beginner {{ background-color: #e2f0d9; color: #385723; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
        .badge-pro {{ background-color: #ddefff; color: #1f538d; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
        
        table.cheat-sheet {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; }}
        table.cheat-sheet th, table.cheat-sheet td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; font-size: 14px; }}
        table.cheat-sheet th {{ background-color: #f8f9fa; color: #1f538d; }}
        
        details {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; margin-bottom: 15px; padding: 15px; transition: all 0.2s ease; }}
        details[open] {{ background: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        summary {{ font-size: 15px; cursor: pointer; color: #1f538d; outline: none; list-style: none; display: flex; align-items: center; justify-content: space-between; }}
        summary::-webkit-details-marker {{ display: none; }}
        summary:after {{ content: '+'; font-size: 20px; font-weight: bold; color: #1f538d; }}
        details[open] summary:after {{ content: '-'; }}
        details p {{ margin-top: 15px; margin-bottom: 0; padding-top: 15px; border-top: 1px solid #e9ecef; }}
        
        @media (max-width: 950px) {{ body {{ flex-direction: column; padding: 10px; }} .sidebar {{ position: static; height: auto; padding: 20px; }} .main-content {{ padding: 30px 20px; }} }}
    </style>
</head>

<body>
    <div class="sidebar">
        <h2 style="margin-top: 0; border: none; font-size: 1.4em;">Inhaltsverzeichnis</h2>
        <div class="toc">
            <ul>
                <li><a class="toc-link" href="#kap1">1. Zielgruppe, Zweck & Schnellstart</a></li>
                <li><a class="toc-link" href="#kap2">2. Haftungsausschluss & Support</a></li>
                <li><a class="toc-link" href="#kap2_1">2.1 Lizenzerklärung</a></li>
                <li><a class="toc-link" href="#kap3">3. Programmaufruf & CLI (Cheat-Sheet)</a></li>
                <li><a class="toc-link" href="#kap3_1">3.1 Benutzeroberfläche & Tabs</a></li>
                <li><a class="toc-link" href="#kap3_2">3.2 Kommandozeilenparameter</a></li>
                <li><a class="toc-link" href="#kap3_3">3.3 Verwendungsszenarien & Use Cases</a></li>
                <li><a class="toc-link" href="#kap4">4. Ordnerstruktur & Admin-Guide</a></li>
                <li><a class="toc-link" href="#kap5">5. Jahreswechsel</a></li>
                <li><a class="toc-link" href="#kap6">6. Mandanten & Datenbanken</a></li>
                <li><a class="toc-link" href="#kap7">7. Positionen & Leistungszeitraum</a></li>
                <li><a class="toc-link" href="#kap8">8. Rechnungsformate (ZUGFeRD/XRechnung)</a></li>
                <li><a class="toc-link" href="#kap9">9. Datumseingaben</a></li>
                <li><a class="toc-link" href="#kap10">10. Standardtexte & Formatierung</a></li>
                <li><a class="toc-link" href="#kap11">11. Eingangsrechnungen & Archiv</a></li>
                <li><a class="toc-link" href="#kap12">12. DATEV-Export & Buchhaltung</a></li>
                <li><a class="toc-link" href="#kap13">13. GitHub & Updates</a></li>
                <li><a class="toc-link" href="#kap14">14. Import-Format (CSV)</a></li>
                <li><a class="toc-link" href="#kap15">15. Mini-Glossar</a></li>
                <li><a class="toc-link" href="#kap16">16. FAQ – Häufige Fragen</a></li>
                <li><a class="toc-link" href="#kap17">17. Schlagwortverzeichnis</a></li>
            </ul>
        </div>
    </div>
    
    <div class="main-content">
        <h1>SokoIur eRechnung - Handbuch</h1>
        <p class="version"><strong>Version: {version_string}</strong></p>

    <h2 id="kap1">1. Zielgruppe, Zweck & Schnellstart <span class="badge-beginner">🟢</span></h2>
    
    <h3>Für wen und what ist das Programm gedacht?</h3>
    <p>Das Programm <strong>SokoIur eRechnung</strong> richtet sich an Freiberufler, Selbstständige, Handwerker sowie kleine bis mittlere Unternehmen, die rechtssichere elektronische Rechnungen im modernen <strong>ZUGFeRD-</strong> und <strong>XRechnung-Standard</strong> erstellen, empfangen und verwalten möchten. Es fungiert entweder als eigenständige Standalone-Lösung für den Arbeitsplatz oder als unsichtbare „Druck-Engine“ im Hintergrund, die von externen Branchenprogrammen via Kommandozeile ferngesteuert werden kann.</p>

    <h3>Welche Aufgaben kann das Programm erfüllen?</h3>
    <ul>
        <li><strong>Ausgangsrechnungen:</strong> Schreiben und Generieren von GoBD-konformen Rechnungen inkl. automatischer Steuerberechnung, optionalem Girocode (QR-Code) und integriertem PDF-Briefpapier.</li>
        <li><strong>Eingangsrechnungen:</strong> Automatisierte formelle Prüfung nach EN 16931 / § 14 UStG, Duplikatskontrolle (Hash & Inhalt) und revisionsvorbereitende Archivierung.</li>
        <li><strong>Buchhaltung & Export:</strong> Erstellung von Ein- und Ausgangsjournalen als PDF oder CSV sowie direkter DATEV-Export (EXTF) mit automatischem Steuer-Splitting.</li>
        <li><strong>Netzwerk- & Mehrplatzbetrieb:</strong> Parallele Nutzung über ein zentrales Netzlaufwerk mit integriertem File-Locking (Sperrdateien) zur Vermeidung von Konflikten.</li>
    </ul>

    <h3>Installation & Ersteinrichtung</h3>
    <p>Die Anwendung (<code>.exe</code>) kann in einem beliebigen Ordner auf Ihrem PC abgelegt werden – auch in systemgeschützten Verzeichnissen wie <code>C:\Programme</code>. Lokale Geräteeinstellungen speichert das Programm automatisch sicher in Ihrem Windows-Benutzerverzeichnis (<code>%LOCALAPPDATA%\SokoIur_eRechnung</code>), sodass keine Administratorrechte für den täglichen Betrieb nötig sind.</p>
    
    <div class="highlight">
        <strong>⚡ In 3 Schritten zur ersten Rechnung (Quickstart für Eilige):</strong><br>
        1. <strong>Grundpfad wählen:</strong> Beim ersten Start einen zentralen Datenspeicherort (bei Mehrplatznutzung ein Netzlaufwerk) festlegen.<br>
        2. <strong>Briefbogen hinterlegen:</strong> Im Reiter <strong>⚙️ Konfig.</strong> über den Button <em>„Briefbogen hinterlegen“</em> Ihre PDF-Vorlage hochladen.<br>
        3. <strong>Rechnung schreiben:</strong> In den Reiter <strong>📝 ERSTELLEN</strong> wechseln, Kundendaten eintragen, Positionen hinzufügen und unten auf <em>„Zugpferdrechnung erstellen & öffnen (Alt+P)“</em> klicken.
    </div>

    <p><strong>WICHTIGER HINWEIS ZUM DATENSPEICHERORT:</strong> Dieser Ordner darf sich aus Sicherheits- und Updategründen NICHT innerhalb oder unterhalb des Programmordners befinden! Wenn Sie das Programm von mehreren Rechnern aus nutzen möchten, wählen Sie hier zwingend ein freigegebenes Netzwerklaufwerk aus.</p>
    <p>Anschließend legt das Programm dort alle benötigten Unterordner und leeren Konfigurations-Dateien (<code>.csv</code>) automatisch für Ihre erste Firma an.</p>
    
    <h3>Briefbogen hinterlegen:</h3>
    <p>Um Ihr eigenes Rechnungsdesign (Logo, Fußzeile etc.) als Hintergrund für die Rechnungen zu verwenden, wechseln Sie in den Reiter <strong>⚙️ Konfig.</strong> und klicken Sie im Bereich der Firmendaten auf den Button <strong>„📄 Briefbogen hinterlegen“</strong>. Wählen Sie dort einfach Ihre PDF-Vorlage aus.</p>
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
    
    <h2 id="kap3">3. Programmaufruf & CLI (Power-User Cheat-Sheet) <span class="badge-pro">🔵</span></h2>
    <p>SokoIur eRechnung is ein Rechnungstool zur Erstellung elektronischer Rechnungen. Es kann komplett über die grafische Oberfläche (GUI) gesteuert werden oder als "Druck-Engine" für externe Branchensoftware fungieren.</p>
    
    <h3>Tastenkürzel-Übersicht (GUI):</h3>
    <ul>
        <li><code>Alt + E</code> &rarr; Zum Reiter ERSTELLEN wechseln</li>
        <li><code>Alt + F</code> &rarr; Zum Reiter ERFASSEN wechseln</li>
        <li><code>Alt + A</code> &rarr; Zum Reiter AUSGANG wechseln</li>
        <li><code>Alt + I</code> &rarr; Zum Reiter EINGANG wechseln</li>
        <li><code>Alt + K</code> &rarr; Zum Reiter Konfig. wechseln</li>
        <li><code>F1</code> &rarr; Hilfe & Info aufrufen</li>
        <li><code>Alt + L</code> &rarr; Letzte Rechnungs-CSV laden</li>
        <li><code>Alt + T</code> &rarr; Texte bearbeiten (Header, Einleitung, Gruß)</li>
        <li><code>Alt + P</code> &rarr; ZUGFeRD-Rechnung generieren, öffnen & beenden</li>
        <li><code>+</code> (Plus-Taste) &rarr; Neue Position im Formular hinzufügen</li>
    </ul>

    <h2 id="kap3_1">3.1 Die Benutzeroberfläche (Tabs) im Detail</h2>
    <p><em>Tipp: Sie können zwischen allen Reitern schnell über die Tastatur wechseln. Halten Sie dazu die <strong>Alt-Taste</strong> gedrückt und tippen Sie den unterstrichenen Buchstaben der Tab-Überschrift.</em></p>
    <h3>📝 E̲RSTELLEN (Ausgangsrechnungen schreiben)</h3>
    <p>Hier erfassen und generieren Sie Ihre eigenen Ausgangsrechnungen an Kunden inkl. automatischer Steuerberechnung.</p>
    <h3>📥 ERF̲ASSEN (Eingangsrechnungen prüfen)</h3>
    <p>Haltautomatisierte Prüfung, Erfassung und Archivierung von Rechnungen Ihrer Lieferanten (Prüfung nach EN 16931 / § 14 UStG).</p>
    <h3>📊 A̲USGANG (Ausgangsjournal)</h3>
    <p>Auswertung der geschriebenen Rechnungen als PDF, CSV oder DATEV-Export.</p>
    <h3>📊 EI̲NGANG (Eingangsjournal & Verwaltung)</h3>
    <p>Durchsuchen, Verwalten und Auswerten der erfassten Eingangsrechnungen (Storno-Funktion inklusive).</p>
    <h3>⚙️ K̲onfig. (Einstellungen & Stammdaten)</h3>
    <p>Zentrale Konfiguration Ihrer Firmen, Nummernkreise, DATEV-Konten und Stammdaten mit hilfreichen Tooltips.</p>
    <h3>ℹ️ Info (Hilfe & Statistik)</h3>
    <p>Dokumentation, Version, Statistiken und Update-Suche.</p>
    
    <h2 id="kap3_2">3.2 Die Kommandozeilenparameter (CLI Cheat-Sheet) <span class="badge-pro">🔵</span></h2>
    <table class="cheat-sheet">
        <tr>
            <th>Parameter</th>
            <th>Beschreibung / Verwendung</th>
        </tr>
        <tr>
            <td><code>--auto</code></td>
            <td>Startet die Rechnungserstellung vollautomatisch unsichtbar im Hintergrund.</td>
        </tr>
        <tr>
            <td><code>--edit</code></td>
            <td>Startet die GUI zur manuellen Nachbearbeitung (enthält Schutz vor versehentlichem Schließen).</td>
        </tr>
        <tr>
            <td><code>--profil "Name"</code></td>
            <td>Wählt das Firmenprofil aus (bricht bei nicht existierendem Profil sicherheitshalber ab).</td>
        </tr>
        <tr>
            <td><code>--renr "Nummer"</code></td>
            <td>Überschreibt die in der CSV enthaltene Rechnungsnummer.</td>
        </tr>
        <tr>
            <td><code>--rechnung "Pfad"</code></td>
            <td>Pfad zur einzulesenden <code>rechnung.csv</code> (z. B. Export-Datei aus Fremdsoftware).</td>
        </tr>
        <tr>
            <td><code>--kopie "Pfad"</code></td>
            <td>Zusätzliches Zielverzeichnis für eine Kopie der generierten Rechnung.</td>
        </tr>
    </table>

    <h2 id="kap3_3">3.3 Programmfunktionen, Verwendungsszenarien & Anwendungsfälle</h2>
    <h3>Kernfunktionen & Typische Szenarien</h3>
    <p><strong>Szenario A (Standalone):</strong> Freiberufler nutzen das Tool als Abrechnungswerkzeug für Kunden, Artikel und DATEV-Export.<br>
    <strong>Szenario B (Druck-Engine):</strong> Mittelständische Branchensoftware übergibt CSV-Daten per CLI (<code>--auto</code>), das Tool bettet sie in den Briefbogen ein und versendet ZUGFeRD-PDFs ohne GUI.</p>

    <h3>Spezifische Anwendungsfälle (Use Cases)</h3>
    <ul>
        <li><strong>Behörden (B2G - XRechnung):</strong> Leitweg-ID im Feld "E-Mail / Leitweg-ID" eintragen, Endpoint-Schema auf <code>0204</code> setzen. Generiert reine XML-Dateien für Upload-Portale (ZRE/OZG-RE) und Begleit-PDFs.</li>
        <li><strong>Geschäftskunden (B2B - E-Rechnungspflicht):</strong> ZUGFeRD-Button nutzen. Enthält Menschen-lesbare PDF-Ansicht und unsichtbare EN 16931 XML-Daten.</li>
        <li><strong>Stornorechnung:</strong> Alte Rechnung via CSV laden, Beträge ins Minus setzen, Hinweistexte anpassen.</li>
        <li><strong>Girocode:</strong> EPC-QR-Code aufdrucken für schnelles Scannen und Bezahlen per Banking-App.</li>
    </ul>

    <h2 id="kap4">4. Ordnerstruktur und Admin-Guide <span class="badge-pro">🔵</span></h2>
    <p>Das Programm trennt strikt zwischen Programmdateien (Installation), lokalen Einstellungen (AppData) und Firmendaten (Daten-Grundpfad auf dem Netzlaufwerk).</p>
    
    <div class="highlight">
        <strong>🛡️ Admin-Hinweise zum Netzwerkbetrieb & File-Locking:</strong><br>
        - Das Programm nutzt Sperrdateien (<code>erechnung.lock</code> und <code>erfassung.lock</code>) im Firmenverzeichnis, um gleichzeitige Schreibkonflikte im Netzwerk zu verhindern.<br>
        - Sollte ein Arbeitsplatz abstürzen, erkennt das System verwaiste Locks und erlaubt nach einer Sicherheitswarnung das manuelle Entfernen der Sperre ("Lock entfernen").<br>
        - Lokale Konfigurationen landen sicher in <code>%LOCALAPPDATA%\SokoIur_eRechnung</code>, was UAC-Berechtigungskonflikte ausschließt.
    </div>

    <h2 id="kap5">5. Jahreswechsel</h2>
    <p>Ändern Sie in den "Einstellungen" einfach das "Aktuelle Rechnungsjahr" im Dropdown oder legen Sie ein neues Firmenprofil an.</p>

    <h2 id="kap6">6. Mandanten, Datenbanken & Firmendaten</h2>
    <p>Sie können im Reiter "Konfig." verschiedene Firmenprofile verwalten. Das Programm synchronisiert neue Firmen automatisch über den geteilten Daten-Grundpfad.</p>

    <h2 id="kap7">7. Rechnungspositionen, Leistungszeitraum & Duplikate</h2>
    <p>Ist im Kopf UND in der Position ein Zeitraum angegeben, muss der Positionszeitraum zwingend innerhalb des Kopf-Zeitraums liegen.</p>

    <h2 id="kap8">8. Rechnungsformate, Papierrechnung & elektronische Empfängeradresse</h2>
    <p>Das Programm unterstützt ZUGFeRD (Hybrid-PDF mit XML), reine XRechnung (XML + Begleit-PDF) und Papierrechnungen (Übergangslösung).</p>

    <h2 id="kap9">9. Datumseingaben</h2>
    <p>Zulässige Formate: <code>TTMMJJ, TT,MM,JJ, TT.MM.JJJJ, TT,MM,JJJJ</code> oder <code>JJJJ-MM-TT</code>.</p>

    <h2 id="kap10">10. Standardtexte & Formatierungen</h2>
    <p>Über "Texte bearbeiten" (<code>Alt+T</code>) legen Sie Zahlungsbedingungen (BT-20) und Rechnungsvermerke (BT-22) fest. Formatierungs-Kürzel: Zeilenumbruch <code>~cr</code>, Fett <code>~f Text f~</code>, Kursiv <code>~k Text k~</code>.</p>

    <h2 id="kap11">11. Eingangsrechnungen erfassen und auswerten</h2>
    <p>Legen Sie neue Eingangsrechnungen in den Ordner <code>reneu</code>. Das Programm prüft diese automatisiert. Fehlerhafte Belege werden abgewiesen. Nach erfolgreicher Erfassung wird der Beleg im Archiv (<code>rchn</code>) gespeichert und im Journal (<code>eausw</code>) vermerkt.</p>

    <h2 id="kap11_rev">11.8 Hinweise zur revisionssicheren Archivierung (Ausblick)</h2>
    <p>Zur Erfüllung der GoBD wird empfohlen, die generierten Verzeichnisse (<code>rchn</code> und <code>are</code>) automatisch in einen <strong>WORM-Onlinespeicher</strong> (z.B. via Nextcloud) zu synchronisieren, der eine nachträgliche Veränderung technisch ausschließt.</p>

    <h2 id="kap12">12. DATEV-Export & Buchhaltung <span class="badge-pro">🔵</span></h2>
    <p>SokoIur eRechnung bietet eine integrierte Exportfunktion für die Finanzbuchhaltung (Stapelverarbeitung im ASCII-CSV / EXTF-Format).</p>
    
    <div class="warning-box">
        <strong style="color: #d9534f;">WICHTIGER HINWEIS (BETA-FUNKTION):</strong><br>
        Die DATEV-Exportfunktionen wurden bisher nicht abschließend in einer produktiven DATEV-Umgebung getestet. Bitte übergeben Sie Daten zunächst probeweise mit Testdaten an Ihren Steuerberater, um den fehlerfreien Import (Feldzuordnungen, 7 Pflichtspalten, Längenbeschränkungen) sicherzustellen.
    </div>

    <h3>12.1 Konfiguration (SKR03 / SKR04) & Automatisches Steuer-Splitting</h3>
    <p>Im Reiter <strong>⚙️ Konfig.</strong> können Sie über <strong>„📈 DATEV-Konten“</strong> Standardkonten für SKR03/SKR04 laden. Rechnungen mit unterschiedlichen Steuersätzen werden beim DATEV-Export automatisch centgenau zerlegt, anteilig zurückgerechnet und mit intelligent vergebenen Soll/Haben-Kennzeichen (S/H) versehen.</p>

    <h2 id="kap13">13. GitHub & Updates</h2>
    <p>Quellcode und Releases sind auf GitHub einsehbar. Über die Update-Funktion wird die neue Version direkt in Ihr Netzlaufwerk geladen.</p>

    <h2 id="kap14">14. Import-Formate (CSV)</h2>
    <p>Alle CSV-Dateien müssen semikolongetrennt (<code>;</code>) und im Format UTF-8 vorliegen (bei ANSI-Dateien aus Excel erfolgt eine automatische Reparatur).</p>

    <h2 id="kap15">15. Mini-Glossar für Einsteiger</h2>
    <ul>
        <li><strong>ZUGFeRD:</strong> Ein Hybrid-Format, das eine normale PDF-Ansicht für Menschen mit einer unsichtbaren XML-Datei für Computer/Buchhaltung kombiniert.</li>
        <li><strong>XRechnung:</strong> Ein reines XML-Datenformat, das vor allem von öffentlichen Auftraggebern (Behörden) vorgeschrieben wird.</li>
        <li><strong>Leitweg-ID:</strong> Die digitale Postanschrift für Rechnungen an Behörden (erscheint anstelle einer normalen E-Mail-Adresse).</li>
        <li><strong>WORM-Speicher:</strong> (Write Once, Read Many) Ein Speichersystem, bei dem Dateien nach dem Schreiben nicht mehr verändert oder gelöscht werden können (wichtig für GoBD-Konformität).</li>
        <li><strong>DATEV EXTF:</strong> Ein standardisiertes ASCII-CSV-Format zum verlustfreien Import von Buchungsstapeln in die Kanzlei-Software des Steuerberaters.</li>
    </ul>

    <h2 id="kap16">16. FAQ – Häufig gestellte Fragen</h2>
    
    <details>
        <summary><strong>Wie kann ich mein eigenes Logo auf die Rechnung drucken?</strong></summary>
        <p>Das Programm nutzt eine PDF-Vorlage als Hintergrund. Erstellen Sie z. B. in Word Ihr Briefpapier mit Logo, speichern Sie es als PDF und hinterlegen Sie es im Reiter <em>Konfig.</em> unter „Briefbogen hinterlegen“.</p>
    </details>
    
    <details>
        <summary><strong>Wie setze ich die Rechnungsnummern für das neue Jahr zurück?</strong></summary>
        <p>Wechseln Sie im Reiter <em>Konfig.</em> einfach das „Aktuelle Rechnungsjahr“ und korrigieren Sie darunter die „Letzte Rechnungs-Nr.“ einmalig händisch auf den Startwert.</p>
    </details>
    
    <details>
        <summary><strong>Wie erstelle ich eine XRechnung für Behörden?</strong></summary>
        <p>Tragen Sie bei der Rechnungserstellung in das Feld „E-Mail / Leitweg-ID“ die Leitweg-ID ein und setzen Sie das „Endpoint-Schema“ auf <code>0204</code>.</p>
    </details>
    
    <details>
        <summary><strong>Das Programm startet nicht mehr oder ist gesperrt. Was tun?</strong></summary>
        <p>Wenn eine Firma gesperrt ist (Lock), wurde das Programm evtl. unsanft beendet. Beim Versuch, den Reiter zu wechseln, erscheint ein Hinweisfenster, in dem Sie den „Lock entfernen“ können.</p>
    </details>

    <h2 id="kap17">17. Schlagwortverzeichnis (Index)</h2>
    <div style="column-count: 2; column-gap: 40px; margin-top: 10px;">
        <p><strong>B</strong><br>
        <a href="#kap1">Briefbogen hinterlegen</a><br>
        <a href="#kap12">Buchhaltung</a></p>
        <p><strong>D</strong><br>
        <a href="#kap1">Daten-Speicherort</a><br>
        <a href="#kap2">Datenschutz</a><br>
        <a href="#kap12">DATEV-Export</a></p>
        <p><strong>E</strong><br>
        <a href="#kap11">Eingangsrechnungen prüfen</a><br>
        <a href="#kap3_3">E-Rechnungspflicht</a></p>
        <p><strong>G</strong><br>
        <a href="#kap3_3">Girocode (QR-Code)</a></p>
        <p><strong>I</strong><br>
        <a href="#kap14">Import (Kunden & Produkte)</a></p>
        <p><strong>J</strong><br>
        <a href="#kap5">Jahreswechsel</a><br>
        <a href="#kap3_1">Journale (Ausgang / Eingang)</a></p>
        <p><strong>L</strong><br>
        <a href="#kap3_3">Leitweg-ID</a></p>
        <p><strong>M</strong><br>
        <a href="#kap6">Mandanten & Firmenprofile</a></p>
        <p><strong>N</strong><br>
        <a href="#kap1">Netzwerkbetrieb</a></p>
        <p><strong>S</strong><br>
        <a href="#kap10">Standardtexte</a><br>
        <a href="#kap3_3">Stornorechnung</a></p>
        <p><strong>X</strong><br>
        <a href="#kap8">XRechnung</a></p>
        <p><strong>Z</strong><br>
        <a href="#kap8">ZUGFeRD</a></p>
    </div>
    <hr style="border: 0; border-top: 1px solid #ddd; margin: 40px 0 20px 0;">
    <p style="text-align: center; color: #666; font-size: 0.9em;">
        &copy; Joachim Sokolowski, Offenbacher Str. 99, 63263 Neu-Isenburg
    </p>
    <br><br><br>
    </div> <!-- Ende der main-content -->
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
        html {{ background-color: #e9ecef; }}
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.7; color: #333; max-width: 900px; margin: 40px auto; padding: 50px 60px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); }}
        h1 {{ color: #1f538d; text-align: center; margin-bottom: 5px; font-size: 2.2em; }}
        p.version {{ text-align: center; color: #6c757d; margin-top: 0; margin-bottom: 40px; }}
        h2 {{ color: #1f538d; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-top: 50px; font-size: 1.6em; }}
        h3 {{ margin-top: 25px; margin-bottom: 10px; color: #0066cc; font-size: 1.1em; text-transform: uppercase; letter-spacing: 0.5px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 12px; font-size: 15px; }}
        code {{ background: #f1f3f5; padding: 3px 6px; border-radius: 4px; font-family: 'Consolas', monospace; color: #d63384; font-size: 0.95em; }}
        @media (max-width: 768px) {{ body {{ margin: 10px; padding: 20px; }} }}
    </style>
</head>
<body>
    <h1>Changelog – SokoIur eRechnung</h1>
    <p><strong>Aktuelle Version: {version_string}</strong></p>
    <h2>Version 2.000151</h2>
    <h3>✨ UI/UX-Verbesserungen & Einstellungen</h3>
    <ul>
        <li><strong>Schnellnavigation (Shortcuts):</strong> Die Tastenkürzel für den direkten Wechsel der Reiter (z. B. Alt+E für Erstellen) werden nun platzsparend und visuell elegant durch einen Unterstrich im jeweiligen Buchstaben der Tab-Überschrift (z. B. E̲RSTELLEN) signalisiert.</li>
        <li><strong>Umbenennung:</strong> Der Reiter „Einstellungen“ wurde in „Konfig.“ (Tastenkürzel Alt+K) umbenannt, um die Tab-Leiste kompakt zu halten.</li>
        <li><strong>Modernes Karten-Design:</strong> Der Reiter „Einstellungen“ wurde komplett überarbeitet und in übersichtliche Themen-Karten (Cards) unterteilt.</li>
        <li><strong>Hover-Erklärungen (Tooltips):</strong> Wichtige Buttons und Checkboxen in den Einstellungen sind nun mit hilfreichen Tooltips versehen, die beim Darüberfahren mit der Maus Erklärungen einblenden.</li>
        <li><strong>DATEV-Konten Manager:</strong> Der Konfigurations-Button für die DATEV-Kontenrahmen (SKR03/SKR04) ist nun prominent im Bereich der Stammdaten integriert.</li>
    </ul>
    <h2>Version 2.000150</h2>
    <h3>✨ Kommandozeile (CLI) & Fremdprogramm-Integration</h3>
    <ul>
        <li><strong>Strikte Profil-Validierung:</strong> Wird das Programm über <code>--auto</code> oder <code>--edit</code> mit einem nicht existierenden Firmennamen aufgerufen, bricht es nun mit einer klaren Fehlermeldung ab. Zuvor wurde fälschlicherweise das Standardprofil herangezogen.</li>
        <li><strong>Sicherheitswarnung bei Abbruch:</strong> Wird die GUI über den Parameter <code>--edit</code> von einem Drittsystem aufgerufen, erscheint nun ein spezifischer Warnhinweis, wenn der Nutzer das Fenster ohne Rechnungserstellung (Beenden / X) schließen möchte. Dies beugt verwaisten Rechnungsnummern im Drittsystem vor.</li>
        <li><strong>Saubere Textfelder:</strong> Beim CLI-gesteuerten Einlesen einer temporären Rechnungs-CSV werden alte Anmerkungen (Zusatztexte) aus dem regulären Firmenbetrieb nun korrekt ignoriert, sodass eine saubere Maske zur Verfügung steht.</li>
    </ul>
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
        <li><strong>Automatisierter DATEV-Export:</strong> In den Reitern „Ausgang“ und „Eingang“ können nun vollautomatisch DATEV-konforme ASCII-CSV-Dateien (Stapelverarbeitung) für den Steuerberater erzeugt werden.</li>
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

def html_to_md(html_text):
    body_match = re.search(r'<body>(.*?)</body>', html_text, re.DOTALL | re.IGNORECASE)
    text = body_match.group(1) if body_match else html_text
    text = re.sub(r'<div class="toc">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.IGNORECASE)
    text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.IGNORECASE)
    text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.IGNORECASE)
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.IGNORECASE)
    text = re.sub(r'<a[^>]*href="(.*?)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'* \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<hr[^>]*>', '---\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&copy;', '©').replace('&rarr;', '->')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def get_doku_md(version_string):
    return html_to_md(get_doku_html(version_string))

def get_changelog_md(version_string):
    return html_to_md(get_changelog_html(version_string))