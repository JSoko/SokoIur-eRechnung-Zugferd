"""
hilfe_texte.py
--------------
HTML-Generierung für das Handbuch.
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
            <li><a class="toc-link" href="#kap4">4. Ordnerstruktur und Dateien</a></li>
            <li><a class="toc-link" href="#kap5">5. Jahreswechsel</a></li>
            <li><a class="toc-link" href="#kap6">6. Mandanten & Datenbanken</a></li>
            <li><a class="toc-link" href="#kap7">7. Rechnungspositionen, Leistungszeitraum & Duplikate</a></li>
            <li><a class="toc-link" href="#kap8">8. Rechnungsformate, Papierrechnung & elektronische Empfängeradresse</a></li>
            <li><a class="toc-link" href="#kap9">9. Datumseingaben</a></li>
            <li><a class="toc-link" href="#kap10">10. Standardtexte & Formatierungen</a></li>
            <li><a class="toc-link" href="#kap11">11. Eingangsrechnungen erfassen und auswerten</a></li>
            <li><a class="toc-link" href="#kap11_rev">11.8 Hinweise zur revisionssicheren Archivierung (Ausblick)</a></li>
            <li><a class="toc-link" href="#kap12">12. GitHub & Updates</a></li>
            <li><a class="toc-link" href="#kap13">13. Import-Format (Beispiel rechnung.csv)</a></li>
            <li><a class="toc-link" href="#kap14">14. Lizenzen & Drittparty-Module</a></li>
        </ul>
    </div>

    <h2 id="kap1">1. Installation & Ersteinrichtung</h2>
    <p>Die Anwendung (<code>.exe</code>) kann in einem beliebigen Ordner auf Ihrem PC abgelegt werden – auch in systemgeschützten Verzeichnissen wie <code>C:\Programme</code>. Lokale Geräteeinstellungen (wie z. B. die Fenstergröße) speichert das Programm automatisch sicher in Ihrem Windows-Benutzerverzeichnis (<code>%LOCALAPPDATA%\SokoIur_eRechnung</code>), sodass keine Administratorrechte für den täglichen Betrieb nötig sind.</p>
    <h3>Ersteinrichtung und Datenspeicherort:</h3>
    <p>Beim allerersten Start des Programms werden Sie aufgefordert, einen Grundpfad für die Datenspeicherung auszuwählen.</p>
    <div class="highlight">
        <strong>WICHTIG:</strong> Dieser Ordner darf sich aus Sicherheits- und Updategründen NICHT innerhalb oder unterhalb des Programmordners befinden!<br>
        Wenn Sie das Programm von mehreren Rechnern aus nutzen möchten, wählen Sie hier zwingend ein freigegebenes Netzwerklaufwerk aus.
    </div>
    <p>Anschließend legt das Programm dort alle benötigten Unterordner und leeren Konfigurations-Dateien (<code>.csv</code>) automatisch für Ihre erste Firma an.</p>
    <h3>Briefbogen hinterlegen:</h3>
    <p>Um Ihr eigenes Rechnungsdesign (Logo, Fußzeile etc.) als Hintergrund für die Rechnungen zu verwenden, wechseln Sie in den Reiter <strong>⚙️ Einst.</strong> und klicken Sie im Bereich der Firmendaten auf den Button <strong>„📄 Briefbogen hinterlegen“</strong>. Wählen Sie dort einfach Ihre PDF-Vorlage aus. Das Programm kopiert die Datei automatisch in den richtigen Firmenordner und benennt sie passend (<code>briefbogen.pdf</code>) um.</p>
    <p><em>Tipp:</em> Verfügt Ihr Briefbogen über zwei Seiten, nutzt das Programm für die erste Rechnungsseite die erste Seite des Briefbogens. Für alle Folgeseiten nutzt es die zweite Seite. Wenn Ihr Briefbogen nur aus einer Seite besteht, deckt das Programm auf Folgeseiten den oberen Kopfbereich automatisch unsichtbar ab, sodass nur die Fußzeile erhalten bleibt.</p>
    
    <h2 id="kap2">2. Haftungsausschluss, Support & Datenschutz</h2>
    
    <h3>Haftungsausschluss</h3>
    <p>Das Programm „SokoIur eRechnung“ wird Ihnen unentgeltlich (im Sinne einer Gefälligkeit / Schenkung) zur Verfügung gestellt.</p>
    <p>Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische Umsetzung der komplexen ZUGFeRD- und XRechnung-Spezifikationen, wird hiermit ausdrücklich ausgeschlossen. Es wird darauf hingewiesen, dass für das Anerkennen der erstellten Rechnungen durch die Adressaten oder die Finanzämter keinerlei Gewähr oder Haftung übernommen wird.</p>
    <p>Die Haftung ist gemäß § 521 BGB auf Vorsatz und grobe Fahrlässigkeit beschränkt. Die Nutzung im geschäftlichen Verkehr erfolgt vollständig auf Ihre eigene Gefahr. Bitte prüfen Sie die erzeugten Rechnungen und Auswertungen regelmäßig stichprobenartig.</p>

    <h3>Gewerbliche Nutzung & Support</h3>
    <p>Die Nutzung der Software ist kostenfrei. Wenn Sie das Programm jedoch gewerblich oder freiberuflich nutzen und die Weiterentwicklung wertschätzen, können Sie gerne eine freiwillige Zahlung (Donationware) leisten. Auf Wunsch stellen wir Ihnen hierüber selbstverständlich eine reguläre Rechnung aus, die Sie steuerlich geltend machen können.</p>
    <p>Bitte haben Sie Verständnis dafür, dass für diese unentgeltliche Software kein kostenloser, individueller Support geleistet werden kann. Sollten Sie Unterstützung bei der Einrichtung, Fragen zur Nutzung oder Wünsche für individuelle Anpassungen haben, kann dies nur im Rahmen einer kostenpflichtigen Dienstleistung erfolgen.</p>
    
    <div class="highlight">
        <strong>Kontakt für Support-Anfragen & Rechnungen:</strong><br>
        Webseite: <a href="https://erech.6078.de" target="_blank">https://erech.6078.de</a><br>
        E-Mail: <a href="mailto:SokoIur@6078.de">SokoIur@6078.de</a>
    </div>

    <h3>Datenschutz / Verbindungen</h3>
    <p>Das Programm arbeitet komplett lokal auf Ihrem Rechner. Ausschließlich zur Updateprüfung wird eine Datenverbindung zum Update-Server (erech.6078.de) aufgebaut. Diese Prüfung erfolgt niemals automatisch im Hintergrund, sondern wird immer nur durch den bewussten Klick des Benutzers auf den entsprechenden Button angestoßen. Es werden keine Rechnungs-, Firmen- oder Kundendaten an externe Server übermittelt.</p>

    <h2 id="kap2_1">2.1 Lizenzerklärung (Freeware / Donationware)</h2>
    <p><strong>1. Nutzungsrechte:</strong><br>Das Programm „SokoIur eRechnung“ (die ausführbare Datei) wird als Freeware bzw. Donationware bereitgestellt. Die Nutzung ist sowohl für private als auch für gewerbliche und freiberufliche Zwecke zeitlich unbegrenzt und kostenfrei gestattet.</p>
    <p><strong>2. Weitergabe und Vervielfältigung:</strong><br>Die Software darf in ihrer ursprünglichen, unveränderten Form kostenlos weitergegeben oder kopiert werden (z. B. auf USB-Sticks oder in internen Firmennetzwerken). Ein kommerzieller Vertrieb, das Anbieten der Software gegen Geld oder die Integration in kommerzielle Softwarepakete durch Dritte ist ohne ausdrückliche, schriftliche Genehmigung des Urhebers untersagt.</p>
    <p><strong>3. Quellcode und Modifikationen:</strong><br>Der Quellcode des Projekts ist auf GitHub öffentlich einsehbar. Wenn Sie den Code für eigene Zwecke nutzen, kompilieren oder modifizieren, richten sich die Bedingungen nach der dort hinterlegten Open-Source-Lizenz. Die vom Urheber bereitgestellte ausführbare Datei (<code>.exe</code>) darf jedoch nicht dekompiliert, manipuliert oder für schädliche Zwecke entfremdet werden.</p>
    <p><strong>4. Drittkomponenten:</strong><br>Dieses Programm nutzt Open-Source-Bibliotheken von Drittanbietern (u. a. Python, CustomTkinter, ReportLab, pypdf). Die Lizenzen dieser Drittkomponenten bleiben von dieser Lizenzerklärung unberührt. Eine genaue Auflistung und Verlinkung der jeweiligen Lizenzbedingungen finden Sie im Handbuch unter dem Punkt „Lizenzen & Drittparty-Module“.</p>
    
    <h2 id="kap3">3. Programmbeschreibung & Aufruf (CLI / GUI)</h2>
    <p>SokoIur eRechnung ist ein Rechnungstool zur Erstellung elektronischer Rechnungen. Es kann entweder komplett über die grafische Oberfläche (GUI) gesteuert werden, oder es fungiert als "Druck-Engine" für externe Programme.</p>
    <h3>Aufruf über Kommandozeile (CLI):</h3>
    <ul>
        <li><code>SokoIur_eRechnung.exe --auto [Parameter]</code> &rarr; Generiert direkt unsichtbar im Hintergrund</li>
        <li><code>SokoIur_eRechnung.exe --edit [Parameter]</code> &rarr; Öffnet die GUI (Manuelle Eingabe) mit den übergebenen Daten, ohne die Rechnungsnummer automatisch hochzuzählen.</li>
    </ul>

    <h3>Praxisbeispiel: Aufruf mit externen Daten (--edit)</h3>
    <p>Angenommen, Sie haben aus einem Drittprogramm (z. B. einer Branchensoftware) eine Rechnung als CSV-Datei exportiert. Sie möchten diese nun in "SokoIur eRechnung" laden, um sie vor der endgültigen PDF-Erstellung noch einmal manuell in der Oberfläche zu prüfen.</p>
    <div class="highlight">
        <code>SokoIur_eRechnung.exe --edit --profil "Hauptfirma" --rechnung "C:\Export\Neue_Rechnung.csv"</code>
    </div>
    
    <h3>Praxisbeispiel: Vollautomatisierte Generierung (--auto) & Kopien anlegen</h3>
    <p>Sie können die Erstellung vollständig unsichtbar im Hintergrund (<code>--auto</code>) oder mit Start der Bearbeitungsmaske (<code>--edit</code>) anstoßen. Übergeben Sie dazu das Profil, eine Rechnungsnummer (<code>--renr</code>), die CSV-Daten aus dem Temp-Ordner und mit dem Parameter <code>--kopie</code> ein externes Ziel-Verzeichnis (z.B. den Windows Dokumentenordner).</p>
    <p>Das Programm speichert die Rechnung dabei wie gewohnt vollautomatisch in den Standardordnern der Firma ab (wichtig für Ihr Journal und die Archivierung) und legt <strong>zusätzlich eine fertige Kopie</strong> der Rechnung in dem von Ihnen unter <code>--kopie</code> übergebenen Verzeichnis ab.</p>
    <div class="highlight">
        <code>SokoIur_eRechnung.exe --auto --profil "Ihre Firma" --renr "RE-2026-005" --rechnung "%TEMP%\rechnung.csv" --kopie "%USERPROFILE%\Documents"</code>
    </div>
    <p><strong>Hinweis zur Rechnungsnummer (renr.csv):</strong> Bei jedem erfolgreichen CLI-Aufruf aktualisiert das Programm die intern hinterlegte "letzte Rechnungsnummer" für die betroffene Firma. Zusätzlich wird im jeweiligen Firmenordner eine Datei namens <code>renr.csv</code> angelegt oder überschrieben, in der diese zuletzt vergebene Nummer steht. Dies ermöglicht Fremdprogrammen das einfache Auslesen der Nummer für den nächsten Lauf.</p>
    <h2 id="kap3_1">3.1 Die Benutzeroberfläche (Tabs) im Detail</h2>
    <p>Das Programm ist in sechs logische Bereiche (Reiter/Tabs) unterteilt, die Sie über die obere Navigationsleiste erreichen. Oben links wird Ihnen dabei stets die aktuell ausgewählte <strong>Firma (Mandant)</strong> angezeigt. Alle Aktionen in den Tabs beziehen sich immer auf die oben gewählte Firma.</p>

    <h3>📝 ERSTELLEN (Ausgangsrechnungen schreiben)</h3>
    <p><strong>Sinn & Nutzen:</strong> Hier erfassen und generieren Sie Ihre eigenen Ausgangsrechnungen an Kunden.<br>
    <strong>Verwendung:</strong> Sie geben die Kopfdaten ein (Kunde, Leitweg-ID, Rechnungsnummer) und fügen unten Ihre Artikel oder Dienstleistungen als Positionen hinzu. Die Felder für die Kundensuche unterstützen eine Live-Suche (Bestätigung per Enter-Taste). Über die Buttons am unteren Rand erzeugen Sie anschließend das gewünschte Format (ZUGFeRD-PDF, XRechnung oder eine einfache Papierrechnung). Das Programm berechnet Steuern und Summen dabei vollautomatisch.</p>

    <h3>📥 ERFASSEN (Eingangsrechnungen prüfen)</h3>
    <p><strong>Sinn & Nutzen:</strong> Haltautomatisierte Prüfung, Erfassung und Archivierung von Rechnungen, die Sie von Ihren Lieferanten erhalten haben.<br>
    <strong>Verwendung:</strong> Das Programm listet alle PDF- und XML-Dateien aus Ihrem Eingangsordner (<code>reneu</code>) auf. Mit einem Klick prüft das Programm elektronische Rechnungen (ZUGFeRD/XRechnung) auf gesetzliche Pflichtangaben (nach § 14 UStG / EN 16931), korrekte Summen und Duplikate. Gültige Belege werden von Ihnen direkt archiviert und ins Eingangsjournal gebucht. Bei Fehlern (z. B. falsche Summen) liefert das Programm einen Textvorschlag für die Reklamation beim Lieferanten.</p>

    <h3>📊 AUSGANG (Ausgangsjournal)</h3>
    <p><strong>Sinn & Nutzen:</strong> Auswertung und Export der von Ihnen geschriebenen Rechnungen.<br>
    <strong>Verwendung:</strong> Erzeugt auf Basis Ihrer geschriebenen Rechnungen ein übersichtliches PDF-Journal (wahlweise für einen bestimmten Monat oder das gesamte Jahr). Ideal zur Weitergabe an die Buchhaltung oder den Steuerberater. Das Journal summiert Netto-, Brutto- und Steuerbeträge nach den jeweiligen Steuersätzen getrennt auf.</p>

    <h3>📊 EINGANG (Eingangsjournal & Verwaltung)</h3>
    <p><strong>Sinn & Nutzen:</strong> Durchsuchen, Verwalten und Auswerten der erfassten Eingangsrechnungen.<br>
    <strong>Verwendung:</strong> Bietet eine intelligente Suchfunktion über alle archivierten Eingangsbelege (z. B. Suche nach Lieferant, Betrag oder ER-Nummer). Hier können Sie auch versehentlich oder doppelt erfasste Eingangsrechnungen wieder stornieren bzw. löschen. Über den PDF-Button erzeugen Sie das Eingangsjournal für Ihre Buchhaltung. Praktisch: Im PDF-Journal sind Klick-Links integriert, mit denen Sie das archivierte Originaldokument direkt öffnen können.</p>

    <h3>⚙️ Einst. (Einstellungen & Stammdaten)</h3>
    <p><strong>Sinn & Nutzen:</strong> Zentrale Konfiguration Ihrer Firmen, Nummernkreise und Stammdaten.<br>
    <strong>Verwendung:</strong> Hier legen Sie neue Firmen/Mandanten an und pflegen Ihre Firmendaten (Bankverbindung, USt-IdNr., Steuernummer), die für eine gültige elektronische Rechnung zwingend erforderlich sind. Zudem verwalten Sie hier Ihre Kunden- und Produktdatenbanken, definieren den Daten-Grundpfad (z. B. auf einem Netzwerklaufwerk) und können die Rechnungsnummern-Zähler bei Bedarf manuell korrigieren. Hier finden Sie auch den Muster-Befehl für den CLI-Aufruf.</p>

    <h3>ℹ️ Info (Hilfe & Statistik)</h3>
    <p><strong>Sinn & Nutzen:</strong> Dokumentation, Versionskontrolle und Nutzungsstatistiken.<br>
    <strong>Verwendung:</strong> Dieser Reiter öffnet auf Knopfdruck das vorliegende Handbuch oder den aktuellen Changelog im Browser. Außerdem sehen Sie hier übersichtliche Statistiken zur Anzahl der Programmstarts und der verarbeiteten Ein- und Ausgangsrechnungen im aktuellen Jahr. Über die Update-Funktion im Footer (unten rechts im Hauptfenster) können Sie zudem jederzeit prüfen, ob eine neue Programmversion auf GitHub verfügbar ist.</p>
    <br>
    <h2 id="kap3_2">3.2 Die Kommandozeilenparameter (CLI) im Detail</h2>
    <p>Das Programm bietet umfangreiche Parameter, um es aus anderen Anwendungen heraus (z. B. einer Branchensoftware) fernzusteuern. Wenn Sie Parameter übergeben, überschreiben diese temporär die Einstellungen des ausgewählten Profils für diesen einen Durchlauf.</p>
    
    <h3>Steuerungs-Parameter (Modus)</h3>
    <ul>
        <li><code>--auto</code>: Startet die Rechnungserstellung vollautomatisch unsichtbar im Hintergrund.</li>
        <li><code>--edit</code>: Startet die grafische Oberfläche, füllt die Maske mit den übergebenen Daten vor und wartet auf Ihre manuelle Bestätigung.</li>
        <li><code>--profil "Name"</code>: Wählt das Firmenprofil aus, dessen Basisdaten genutzt werden sollen.</li>
        <li><code>--no-open</code>: Verhindert, dass das fertige PDF nach der Erstellung automatisch im Standard-PDF-Viewer geöffnet wird.</li>
    </ul>

    <h3>Daten- und Dateiparameter</h3>
    <ul>
        <li><code>--renr "RE-Nummer"</code>: Überschreibt die in der CSV enthaltene Rechnungsnummer (schreibt diese auch in die <code>renr.csv</code> zurück).</li>
        <li><code>--kunde-az "Text"</code>: Überschreibt das Aktenzeichen des Kunden (Ihr Zeichen).</li>
        <li><code>--rechnung "Pfad"</code>: Pfad zur einzulesenden <code>rechnung.csv</code>.</li>
        <li><code>--kopie "Pfad"</code>: Zusätzliches Zielverzeichnis. Das PDF wird regulär im Firmenarchiv abgelegt und <strong>zusätzlich</strong> in dieses Verzeichnis kopiert.</li>
        <li><code>--ausgabe "Pfad"</code>: Überschreibt den Basisordner für die archivierten PDFs.</li>
        <li><code>--auswertungen "Pfad"</code>: Überschreibt den Basisordner für die Journal-CSVs.</li>
        <li><code>--jahr "YYYY"</code>: Setzt das Rechnungsjahr für die Unterordner-Ablage (z. B. 2026).</li>
    </ul>

    <h3>Layout- und Textparameter (optional)</h3>
    <ul>
        <li><code>--briefbogen "Pfad"</code>: Überschreibt das zu verwendende Hintergrund-PDF.</li>
        <li><code>--zahlungsbedingungen "Text"</code>: Setzt den Hinweistext zur Fälligkeit (BT-20).</li>
        <li><code>--rechnungsvermerk "Text"</code>: Setzt den allgemeinen Rechnungshinweis (BT-22).</li>
        <li><code>--kontoinhaber "Name"</code>: Überschreibt den im QR-Code und Text genutzten Kontoinhaber.</li>
        <li><code>--force-girocode</code> / <code>--no-girocode</code>: Erzwingt oder verhindert den Andruck des EPC-QR-Codes (Girocode) unabhängig von der Profileinstellung.</li>
        <li>Zusätzliche Text-Dateipfade: <code>--zusatz</code>, <code>--gruss</code>, <code>--header</code>, <code>--einleitung</code>.</li>
    </ul>
    <br>
    <h2 id="kap4">4. Ordnerstruktur und Dateien</h2>
    <p>Das Programm trennt strikt zwischen Programmdateien, lokalen Einstellungen und Ihren Firmendaten. Dadurch wird der sichere Betrieb im Netzwerk und in geschützten Windows-Ordnern gewährleistet:</p>
    <ul>
        <li><strong>Programmverzeichnis (z. B. <code>C:\Programme\erech</code>):</strong> Hier liegt ausschließlich die ausführbare Datei (<code>.exe</code>). Sie benötigt keine Schreibrechte.</li>
        <li><strong>Lokale Konfiguration (<code>%LOCALAPPDATA%\SokoIur_eRechnung</code>):</strong> In diesem versteckten Windows-Benutzerordner speichert das Programm die Datei <code>local_config.json</code> (Merkt sich Fenstergrößen, den akzeptierten Haftungsausschluss und den Pfad zu Ihren Daten) sowie die temporär generierten Hilfedateien.</li>
        <li><strong>Daten-Grundpfad:</strong> Diesen Pfad legen Sie beim ersten Start selbst fest (idealerweise auf einem Netzwerklaufwerk). Hier liegen alle sensiblen Firmenordner, Rechnungs-CSVs und archivierten PDFs.</li>
    </ul>
    <div class="highlight">
        <strong>Netzwerkbetrieb & Versionsschutz:</strong><br>
        Das Programm (.exe) selbst kann lokal auf verschiedenen Rechnern installiert sein, während der Datenspeicherpfad auf einem freigegebenen Netzwerklaufwerk liegt.<br>
        Versucht ein Rechner mit einer älteren Programmversion auf Daten zuzugreifen, die bereits mit einer neueren Version bearbeitet wurden, wird der Zugriff zum Schutz vor Datenkorruption blockiert und ein Update angeboten.
    </div>

    <h2 id="kap5">5. Jahreswechsel</h2>
    <p>Zum Jahreswechsel haben Sie zwei Möglichkeiten:</p>
    <ul>
        <li><strong>A) Neues Profil anlegen:</strong> Klicken Sie oben auf "+ Neu", um saubere, leere Ausgabe- und Auswertungs-Ordner für das neue Jahr zu erhalten.</li>
        <li><strong>B) Vorhandenes Profil anpassen:</strong> Ändern Sie in den "Einstellungen" das "Aktuelle Rechnungsjahr" im Dropdown.</li>
    </ul>

    <h2 id="kap6">6. Mandanten, Datenbanken & Firmendaten</h2>
    <p>Sie können im Reiter "Einst." verschiedene Firmenprofile verwalten. Ihre Kunden- und Produktdatenbanken werden zentral im Firmenverzeichnis gespeichert und per Live-Suche (auch per Tastendruck im Feld) unterstützt.</p>
    <div class="highlight">
        <strong>Automatische Netzwerk-Synchronisation:</strong><br>
        Das Programm ist voll netzwerkfähig. Wenn Sie das Programm an einem neuen Rechner installieren und als Daten-Grundpfad das bestehende Netzwerklaufwerk auswählen, werden sofort alle existierenden Firmen automatisch erkannt und lokal eingebunden.<br>
        Zudem prüft das Programm <strong>bei jedem Neustart</strong> automatisch, ob ein anderer Nutzer im Netzwerk in der Zwischenzeit eine neue Firma angelegt hat, und fügt diese nahtlos und von selbst in Ihre Firmen-Auswahl hinzu.
    </div>

    <h2 id="kap7">7. Rechnungspositionen, Leistungszeitraum & Duplikate</h2>
    <div class="highlight">
        <strong>Wichtiger Hinweis zum Leistungszeitraum:</strong><br>
        Ist im Kopf UND in der Position ein Zeitraum angegeben, muss der Positionszeitraum ZWINGEND kalendarisch INNERHALB des Kopf-Zeitraums liegen.
    </div>
    <h3>Wiederverwendung von Rechnungen (Storno & Folgerechnungen):</h3>
    <p>Über die Funktion <strong>„Rechnungs-CSV wählen“</strong> im Reiter <em>ERSTELLEN</em> können Sie jederzeit eine bereits erstellte Rechnungs-CSV-Datei laden.</p>
    <div class="highlight">
        <strong>Praxis-Tipp:</strong> Ideal zur Erstellung von <strong>Stornorechnungen</strong> oder <strong>wiederkehrenden Folgerechnungen</strong> auf Basis von Altdaten, ohne alles neu eintippen zu müssen.
    </div>

    <h2 id="kap8">8. Rechnungsformate, Papierrechnung & elektronische Empfängeradresse</h2>
    <p>Das Programm unterstützt die folgenden Rechnungsarten:</p>
    <ul>
        <li><strong>ZUGFeRD (Hybrid-Format - Empfohlen):</strong> Verbindet eine optisch ansprechende PDF-Rechnung für den Menschen mit einer unsichtbar eingebetteten XML-Datei für die Buchhaltung. Sie versenden <strong>genau eine Datei</strong> (<code>.pdf</code>), die universell lesbar und voll normkonform ist.</li>
        <li><strong>XRechnung (Reines Datenformat):</strong> Besteht aus einer reinen XML-Datei (nach EN 16931). Da sie von Menschen ohne Spezialsoftware nicht lesbar ist, generiert das Programm hierfür auf Wunsch ein separates <strong>Begleit-PDF</strong> (mit dem rechtlichen Hinweis, dass die XML-Datei maßgeblich ist).</li>
        <li><strong>Papierrechnung (PDF ohne XML):</strong> Die Schaltfläche <strong>„Papierrechnung erstellen“</strong> erzeugt ausschließlich eine visuell lesbare PDF-Rechnung. Sie verwendet denselben Briefbogen und dasselbe Layout wie die ZUGFeRD-Rechnung, enthält jedoch weder eine eingebettete XML-Datei noch eine separate XML-Datei. Die Datei wird als <code>Rechnung_&lt;Rechnungsnummer&gt;_Papier.pdf</code> gespeichert.</li>
    </ul>
    <div class="highlight">
        <strong>Übergangsfunktion:</strong> Die Papierrechnung wird ausschließlich für eine Übergangszeit bereitgestellt. Sie ist nicht für den elektronischen Rechnungsversand nach XRechnung oder ZUGFeRD geeignet und kann in einer späteren Programmversion wieder entfernt werden. Verwenden Sie sie daher nur, wenn eine reine Sicht-PDF tatsächlich ausreicht.
    </div>
    <h3>E-Mail / Leitweg-ID und Endpoint-Schema des Kunden</h3>
    <p>Die beiden Eingabefelder dienen der eindeutigen elektronischen Adressierung des Rechnungsempfängers. Sie werden bei Aktivierung von <strong>„Kunde speichern/updaten“</strong> in den Kundendaten hinterlegt und bei einer späteren Kundenauswahl wieder übernommen.</p>
    <ul>
        <li><strong>E-Mail / Leitweg-ID:</strong> Hier steht entweder die Rechnungs-E-Mail-Adresse des Kunden oder bei öffentlichen Auftraggebern dessen Leitweg-ID. Diese Angabe wird für die elektronische Zustellung und für die technische Validierung elektronischer Rechnungen benötigt.</li>
        <li><strong>Endpoint-Schema:</strong> Es bezeichnet die Art der elektronischen Adresse. Bei einer E-Mail-Adresse setzt das Programm automatisch <code>EM</code>. Bei einer Leitweg-ID ist in der Regel <code>0204</code> einzutragen.</li>
    </ul>
    <p>Für XRechnung und ZUGFeRD ist eine elektronische Käuferadresse erforderlich. Die Papierrechnung kann dagegen auch erstellt werden, wenn diese Felder leer sind.</p>
    <div class="highlight">
        <strong>Warum ZUGFeRD in der Praxis vorzuziehen ist:</strong><br>
        ZUGFeRD vermeidet das sogenannte "Zwei-Dateien-Chaos". Es verhindert, dass XML- und PDF-Dateien im E-Mail-Verkehr getrennt werden, und bietet maximale Benutzerfreundlichkeit. Eine reine XRechnung sollte im geschäftlichen Alltag (B2B) nur dann gewählt werden, wenn der Empfänger (z. B. eine Behörde) dies explizit verlangt. 
        <br><br>
        <em>Hinweis beim Versand einer XRechnung:</em> Nach der Generierung öffnet sich der Zielordner automatisch im Explorer. Da es sich um zwei getrennte Dateien handelt, müssen Sie sowohl die XML-Datei als auch das Begleit-PDF manuell (z. B. gemeinsam in einer E-Mail) an Ihren Kunden übermitteln.
    </div>

    <h2 id="kap9">9. Datumseingaben</h2>
    <p>Zulässige Formate: <code>TTMMJJ, TT,MM,JJ, TT.MM.JJJJ, TT,MM,JJJJ</code> oder <code>JJJJ-MM-TT</code>.</p>

    <h2 id="kap10">10. Standardtexte & Formatierungen</h2>
    <p>Über "Texte bearbeiten" (<code>Alt+T</code>) legen Sie Zahlungsbedingungen (BT-20) und Rechnungsvermerke (BT-22) fest. Formatierungs-Kürzel: Zeilenumbruch <code>~cr</code>, Fett <code>~f Text f~</code>, Kursiv <code>~k Text k~</code>.</p>

    <h2 id="kap11">11. Eingangsrechnungen erfassen und auswerten</h2>
    <p>Die Eingangsrechnungsverarbeitung ist vollständig in die jeweilige Firmenverwaltung eingebunden. Für jede Firma legt das Programm die Ordner <code>reneu</code> (neue Belege), <code>rebearb/&lt;Jahr&gt;</code> (bearbeitete Originaldateien), <code>rchn/&lt;Jahr&gt;</code> (nummerierte Archivkopien) und <code>einj/&lt;Jahr&gt;</code> (Eingangsjournal) an.</p>
    <h3>11.1 Erfassung im Reiter „ERFASSEN“</h3>
    <ol>
      <li>Legen Sie neue Eingangsrechnungen in den Firmenordner <code>reneu</code>.</li>
      <li>Klicken Sie auf <strong>„Erste Eingangsrechnung im Ordner prüfen“</strong>. Ist der Ordner leer, nennt das Programm den genauen geprüften Pfad.</li>
      <li>Das Programm erkennt ZUGFeRD-Hybrid-PDFs, XRechnungs-XML-Dateien (CII oder UBL) und sonstige Dateien.</li>
      <li>Bei ZUGFeRD und XRechnung prüft es automatisiert die technische Lesbarkeit, die XML-Struktur, zentrale EN-16931-Angaben, Pflichtangaben nach § 14 Abs. 4 UStG, Summenkonsistenz und die vorhandenen Steuerangaben, soweit diese maschinell auslesbar sind.</li>
      <li>Bei erfolgreicher Prüfung erhalten Sie eine übersichtliche Zusammenfassung und entscheiden ausdrücklich, ob der Beleg als Eingangsrechnung erfasst wird.</li>
    </ol>
    <div class="highlight"><strong>Wichtige Grenze:</strong> Die Prüfung ist eine automatisierte formelle und rechnerische Plausibilitätsprüfung. Sie ersetzt weder die sachliche Rechnungsprüfung noch eine steuerliche oder rechtliche Freigabe, etwa zur Leistungsbeziehung, zum Vorsteuerabzug, zu Sonderregelungen oder zur Unternehmereigenschaft.</div>
    <h3>11.2 Fehlerhafte strukturierte Rechnungen</h3>
    <p>Fehlen auslesbare Pflichtangaben oder sind Summen nicht schlüssig, wird kein Beleg gebucht. Das Programm zeigt E-Mail-Adresse des Ausstellers, Rechnungsnummer und Rechnungsdatum an, soweit auslesbar. Zudem stellt es einen kopierbaren Betreff und einen kopierbaren Text zur Bitte um eine berichtigte Rechnung bereit.</p>
    <h3>11.3 XRechnung und Leseabschrift</h3>
    <p>Bei einer XRechnung kann eine lesbare PDF-Leseabschrift erzeugt werden. Die Checkbox merkt sich die letzte Einstellung. Maßgeblich bleibt stets die XML-Datei. Beispiel der Archivierung: <code>ER260001.xml</code> und <code>ER260001_Leseabschrift.pdf</code>.</p>
    <h3>11.4 Sonstige Formate und manuelle Ergänzung</h3>
    <p>Für reine PDF-Rechnungen, gescannte Papierrechnungen und sonstige Dateien wählen Sie die Kategorie und bestätigen gegebenenfalls den Vorsteuerabzug. Für das Journal müssen mindestens Netto- oder Bruttobetrag eingegeben werden. Wird nur ein Nettobetrag eingegeben, ergänzt das Programm 19 % Umsatzsteuer. Wird nur der Bruttobetrag eingegeben, rechnet es bei fehlender Steuerangabe mit 19 % zurück. Lieferant, externe Rechnungsnummer und Datum können nachgetragen werden.</p>
    <h3>11.5 Nummern, Archivierung und Lösch-Warteliste</h3>
    <p>Die interne Nummer lautet <code>ER</code> + zweistelliges Jahr + vierstellige laufende Nummer, zum Beispiel <code>ER260001</code>. Die letzte Nummer kann unter „Einst.“ eingesehen und berichtigt werden. Das Original wird mit seinem ursprünglichen Namen nach <code>rebearb/&lt;Jahr&gt;</code> verschoben; eine Kopie wird im Archiv <code>rchn/&lt;Jahr&gt;</code> mit der internen Nummer abgelegt. Kann die Quelldatei nicht verschoben werden, kopiert das Programm sie und versucht bei späteren Einlesevorgängen zuerst erneut, die ursprüngliche Datei zu löschen. Andere Dateien im Eingangsordner werden dennoch weiter verarbeitet.</p>
    <h3>11.6 Eingangsjournal</h3>
    <p>Pro Monat entsteht eine CSV im Ordner <code>einj/&lt;Jahr&gt;</code>. Der Reiter „EINGANG“ erzeugt daraus ein PDF-Journal mit interner ER-Nummer, Rechnungsdaten, Lieferant, Beträgen, Steueraufteilung, Format und Vorsteuer-Prüfvermerk. Die Zeile „Datei öffnen“ enthält einen Verweis auf die archivierte Originalrechnung. Ob ein PDF-Viewer lokale Dateilinks öffnet, hängt von dessen Sicherheitseinstellungen ab.</p>
    <p><strong>Beispiel:</strong> Eine am 15.03.2026 eingelesene XRechnung erhält die Nummer <code>ER260001</code>; das Journal wird als <code>einj/2026/er202603.csv</code> geführt. Das Jahresjournal kann im Reiter „EINGANG“ als PDF erzeugt werden.</p>
    <h3>11.7 Ausgangsjournal</h3>
    <p>Das Programm erstellt auch für Ausgangsrechnungen Monats-CSVs. Im Reiter „Ausgang“ können Sie daraus ein PDF-Journal erzeugen.</p>

    <h2 id="kap11_rev">11.8 Hinweise zur revisionssicheren Archivierung (Ausblick)</h2>
    <p><strong>Aktueller Entwicklungsstand:</strong> Das Programm „SokoIur eRechnung“ bietet zum aktuellen Zeitpunkt noch keine integrierte, vollautomatisierte und zertifizierte revisionssichere Archivierung im Sinne der GoBD (Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern, Aufzeichnungen und Unterlagen in elektronischer Form sowie zum Datenzugriff). Die lokalen Ordnerstrukturen (wie z. B. <code>rchn</code> und <code>are</code>) dienen der übersichtlichen geordneten Ablage und Buchhaltungsvorbereitung, erfüllen jedoch rein technisch ohne zusätzliche Maßnahmen noch nicht die strengen rechtlichen Vorgaben an Unveränderbarkeit, Vollständigkeit und Nachvollziehbarkeit über die gesetzlichen Aufbewahrungsfristen von bis zu 10 Jahren.</p>
    <p><strong>Geplante Erweiterung:</strong> Es ist beabsichtigt, in einer kommenden Version eine detaillierte Anleitung bzw. Workflows aufzunehmen, wie die erzeugten Rechnungen, XML-Dateien und Journals in Kombination mit modernen Cloud-Speichern (wie Nextcloud) und zertifiziertem <strong>WORM-Onlinespeicher</strong> (Write Once, Read Many – einmal schreiben, oft lesen; d.h. physisch oder logisch unveränderbarer und löschgeschützter Speicher) revisionssicher betrieben werden können.</p>
    <h3>Konzeptioneller Ausblick (WORM & Nextcloud):</h3>
    <ul>
      <li><strong>Lokale Erstellung & Export:</strong> SokoIur eRechnung generiert wie gewohnt die Rechnungs-, XML-Datensätze und Journale in den lokalen oder im Netzwerk freigegebenen Firmenordnern.</li>
      <li><strong>Synchronisation via Nextcloud:</strong> Über den Nextcloud-Client können diese Verzeichnisse (insbesondere das Rechnungsarchiv <code>are</code> und <code>rchn</code>) vollautomatisch im Hintergrund in eine Nextcloud-Instanz synchronisiert werden.</li>
      <li><strong>Unveränderbarkeit durch WORM-Storage:</strong> Um die rechtlich geforderte Revisionssicherheit (GoBD-Konformität) zu erreichen, wird das entsprechende Nextcloud-Zielverzeichnis auf einem Storage-Backend eingerichtet, das WORM-Eigenschaften unterstützt (z. B. S3-kompatibler Object Storage mit aktivierten <em>Object Locks</em> im Compliance-Modus oder spezielle WORM-Share-Freigaben).</li>
      <li><strong>Vorteil dieses Ansatzes:</strong> Einmal auf den WORM-Speicher hochgeladene Rechnungen und XML-Dateien können dort weder durch Anwender noch durch Administratorrechte vor Ablauf der festgelegten Aufbewahrungsfrist gelöscht oder überschrieben werden. Damit sind die gesetzlichen Anforderungen an die Unveränderbarkeit erfüllt, ohne dass eine geschlossene, teure Spezialsoftware angeschafft werden muss.</li>
    </ul>

    <h2 id="kap12">12. GitHub & Updates</h2>
    <p>Quellcode und Releases sind auf <a href="https://github.com/JSoko/SokoIur-eRechnung-Zugferd" target="_blank">GitHub</a> einsehbar.</p>
    <p>Das Programm prüft auf Wunsch, ob auf dem Server <a href="https://erech.6078.de" target="_blank">https://erech.6078.de</a> eine neue Version vorliegt. Wenn Sie ein Update durchführen, wird die neue Version heruntergeladen, bei Ihnen lokal installiert und <strong>zusätzlich automatisch in das Basisverzeichnis Ihres Netzwerklaufwerks (Daten-Grundpfad) kopiert</strong>. So können auch alle anderen Arbeitsplätze schnell und einfach auf die aktuellste Programmversion zugreifen, indem sie die neue <code>.exe</code>-Datei von dort kopieren und auf ihrem lokalen Rechner austauschen.</p>

    <h2 id="kap13">13. Import-Format (Beispiel rechnung.csv)</h2>
    <p>Wenn Sie Rechnungen aus einem Drittprogramm exportieren und automatisiert verarbeiten möchten, muss die übergebene <code>rechnung.csv</code> ein fest definiertes Format (durch Semikolon getrennt) aufweisen. Die Kopfdaten der Rechnung werden in jeder Zeile wiederholt, lediglich die Positionsdaten ändern sich.</p>
    <p>Hier ist ein Muster für die "Hauptfirma" mit einer Rechnung und drei Positionen:</p>
    <div class="highlight" style="overflow-x: auto; white-space: pre;"><code>Rechnungsnummer;Rechnungsdatum;Faelligkeitsdatum;KundeName;KundeStrasse;KundePLZ;KundeOrt;KundeLand;KundeEmail;KundeEndpoint;KundeEndpointScheme;KundeNr;Aktenzeichen;KundeAktenzeichen;LeistungszeitraumKopf;Ratenzahlung;PosNr;Menge;Einheit;Bezeichnung;EinzelpreisNetto;Steuersatz;Zusatztext;LeistungszeitraumPos
RE-2026-005;15.03.2026;14.04.2026;Musterkunde GmbH;Beispielweg 42;12345;Musterstadt;DE;rechnung@muster.de;rechnung@muster.de;EM;KD-1000;AZ-99;IHR-REF-123;01.03.2026|15.03.2026;False;1;1;Pauschale (LS);Einrichtungspauschale;250,00;19;Dies ist ein optionaler Zusatztext zur Gesamtrechnung.;
RE-2026-005;15.03.2026;14.04.2026;Musterkunde GmbH;Beispielweg 42;12345;Musterstadt;DE;rechnung@muster.de;rechnung@muster.de;EM;KD-1000;AZ-99;IHR-REF-123;01.03.2026|15.03.2026;False;2;5,5;Stunde(n) (HUR);Beratungsleistung;120,00;19;;
RE-2026-005;15.03.2026;14.04.2026;Musterkunde GmbH;Beispielweg 42;12345;Musterstadt;DE;rechnung@muster.de;rechnung@muster.de;EM;KD-1000;AZ-99;IHR-REF-123;01.03.2026|15.03.2026;False;3;10;Stück (C62);Softwarelizenzen;49,90;19;;</code></div>
    
    <p><strong>Hinweis zu den Einheiten:</strong> Das Programm erwartet idealerweise den UN/ECE-Code in Klammern (z.B. <code>(C62)</code> für Stück oder <code>(HUR)</code> für Stunden). Alternativ reicht in der Regel auch das bloße Kürzel wie <code>C62</code>.</p>

    <h3>13.1 Pflichtfelder für gültige ZUGFeRD- & XRechnungen</h3>
    <p>Damit das Programm automatisiert eine normkonforme elektronische Rechnung nach EN 16931 erstellen kann, müssen in der <code>rechnung.csv</code> zwingend folgende Felder befüllt sein (alle anderen dürfen leer bleiben, aber die Semikolons müssen als Platzhalter erhalten bleiben):</p>
    <ul>
        <li><strong>Kopfdaten (in jeder Zeile identisch):</strong>
            <ul>
                <li><code>Rechnungsnummer</code>: Die eindeutige Rechnungsnummer.</li>
                <li><code>Rechnungsdatum</code>: Das Datum der Rechnungsstellung (z. B. 15.03.2026).</li>
                <li><code>KundeName</code>, <code>KundeStrasse</code>, <code>KundePLZ</code>, <code>KundeOrt</code>, <code>KundeLand</code>: Die vollständige postalische Anschrift des Rechnungsempfängers.</li>
                <li><code>KundeEndpoint</code> & <code>KundeEndpointScheme</code>: Die elektronische Adresse des Empfängers. Tragen Sie unter Endpoint die E-Mail-Adresse (Scheme: <code>EM</code>) oder die Leitweg-ID (Scheme: <code>0204</code>) ein.</li>
                <li><code>Aktenzeichen</code> (Optional): Ihr internes Zeichen ("Unser Zeichen"). Wird zur EN-16931-Konformität als Rechnungsnotiz übergeben.</li>
                <li><code>KundeAktenzeichen</code> (Optional): Das Zeichen des Kunden ("Ihr Zeichen" / BuyerReference BT-13).</li>
            </ul>
        </li>
        <li><strong>Positionsdaten (pro Zeile individuell):</strong>
            <ul>
                <li><code>PosNr</code>: Die fortlaufende Positionsnummer (z. B. 1, 2, 3).</li>
                <li><code>Bezeichnung</code>: Der Name / die Beschreibung des Artikels oder der Leistung.</li>
                <li><code>Menge</code>: Die Anzahl (Zahlen mit Komma oder Punkt).</li>
                <li><code>Einheit</code>: Die Maßeinheit (z. B. C62, HUR, LS).</li>
                <li><code>EinzelpreisNetto</code>: Der Netto-Stückpreis.</li>
                <li><code>Steuersatz</code>: Der anzuwendende Umsatzsteuersatz (z. B. 19, 7 oder 0).</li>
            </ul>
        </li>
    </ul>
    <div class="highlight">
        <strong>Wichtig für die Firmendaten (firma.csv):</strong> Auch der Rechnungsaussteller muss vollständig konfiguriert sein. Dazu gehören zwingend Firmenname, vollständige Adresse, Bankverbindung (IBAN) sowie die USt-IdNr. oder Steuernummer.
    </div>

    <h2 id="kap14">14. Lizenzen & Drittparty-Module</h2>
    <p>Dieses Programm wurde in Python geschrieben und nutzt für bestimmte Funktionen Open-Source-Bibliotheken von Drittanbietern. Nachfolgend finden Sie eine Auflistung der verwendeten Hauptkomponenten sowie Links zu deren jeweiligen Lizenzbedingungen:</p>
    <ul>
        <li><strong>Python</strong> (Programmiersprache)<br>Lizenz: Python Software Foundation License (PSF) <br><a href="https://docs.python.org/3/license.html" target="_blank">Zur Lizenz</a></li>
        <li><strong>CustomTkinter</strong> (Für das Design der Benutzeroberfläche)<br>Lizenz: MIT License <br><a href="https://github.com/TomSchimansky/CustomTkinter/blob/master/LICENSE" target="_blank">Zur Lizenz</a></li>
        <li><strong>ReportLab</strong> (Für die PDF-Generierung des Rechnungslayouts)<br>Lizenz: BSD License <br><a href="https://bitbucket.org/rptlab/reportlab/src/master/LICENSE.txt" target="_blank">Zur Lizenz</a></li>
        <li><strong>pypdf</strong> (Für das Einbetten der ZUGFeRD XML-Datei in das PDF)<br>Lizenz: BSD 3-Clause License <br><a href="https://github.com/py-pdf/pypdf/blob/main/LICENSE" target="_blank">Zur Lizenz</a></li>
        <li><strong>qrcode</strong> (Für die Generierung des Girocodes/QR-Codes)<br>Lizenz: BSD 3-Clause License <br><a href="https://github.com/lincolnloop/python-qrcode/blob/master/LICENSE" target="_blank">Zur Lizenz</a></li>
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
    
    <h2>10.11.2026</h2>
    <h3>✨ Neue Funktionen & XML-Korrekturen</h3>
    <ul>
        <li><strong>Referenzen normkonform getrennt:</strong> Das Feld "Ihr Zeichen" (KundeAktenzeichen) wird als echte Leitweg-Referenz (BuyerReference BT-13) übergeben. Das interne Feld "Unser Zeichen" (Aktenzeichen) wird zur Vermeidung von EN 16931-Validierungsfehlern ab sofort standardkonform als Rechnungsnotiz (IncludedNote) in die XML geschrieben.</li>
        <li><strong>Kommandozeilen-Erweiterung:</strong> Das Kunden-Aktenzeichen kann nun per Parameter <code>--kunde-az</code> für automatisierte CLI-Abläufe gesetzt werden.</li>
    </ul>
    <h2>09.11.2026</h2>
    <h3>📚 Dokumentation & Handbuch-Erweiterung</h3>
    <ul>
        <li><strong>Revisionssichere Archivierung (Kapitel 11.8):</strong> Das Handbuch wurde um ein dediziertes Kapitel zur revisionssicheren Archivierung nach GoBD ergänzt. Es wird klargestellt, dass das Programm diese Funktion zum aktuellen Zeitpunkt noch nicht direkt integriert bietet, aber ein konzeptioneller Ausblick und Leitfaden aufgenommen wurde, wie die Archivierung über eine Kombination aus Nextcloud und einem unveränderbaren WORM-Onlinespeicher realisiert werden kann.</li>
    </ul>
    <h3>⚡ Performance & Fehlerbehebungen (Bugfixes)</h3>
    <ul>
        <li><strong>Statistik-Korrektur (Rechnungsausgang):</strong> Die Zählung der erstellten Ausgangsrechnungen im Reiter „Info“ wurde korrigiert. Die Zahlen werden nun zuverlässig aus den Journal-Dateien (Auswertungen/reYYYYMM.csv) ermittelt, statt fälschlicherweise aus der temporären Bearbeitungsdatei (rechnung.csv).</li>
        <li><strong>Massiver Performance-Boost im Eingangsordner:</strong> Das Einlesen und Prüfen von neuen Eingangsrechnungen im Reiter „ERFASSEN“ wurde extrem beschleunigt. Die Journal-Datenbasis wird für die Duplikatsprüfung nun nur noch einmalig pro Aktualisierungszyklus geladen und im Arbeitsspeicher gehalten (Caching), anstatt das Laufwerk für jede einzelne Datei im Ordner reneu komplett neu zu durchsuchen.</li>
    </ul>
    <h3>🛠 System & Architektur</h3>
    <ul>
        <li><strong>Neues Update-System (erech.6078.de):</strong> Die Update-Prüfung erfolgt nicht mehr über GitHub, sondern direkt über den eigenen Server erech.6078.de. Wird ein Update durchgeführt, legt das Programm ab sofort vollautomatisch eine Kopie der neuen .exe-Datei im Hauptverzeichnis des Netzwerklaufwerks ab, um die Verteilung an andere Arbeitsplätze im Büro drastisch zu erleichtern.</li>
        <li><strong>Installationsfreundlichkeit & AppData-Nutzung:</strong> Das Programm trennt nun strikt zwischen der Programmdatei und lokalen Konfigurationsdateien. Die Datei <code>local_config.json</code> (welche lokale UI-Einstellungen speichert) sowie generierte Hilfedateien werden ab sofort sicher im Windows-Benutzerverzeichnis (<code>%LOCALAPPDATA%\SokoIur_eRechnung</code>) abgelegt. Dies behebt Schreib- und Berechtigungsprobleme (UAC-Konflikte), wenn die Anwendung in systemgeschützten Ordnern wie <code>C:\Programme</code> installiert und ohne Administratorrechte ausgeführt wird.</li>
    </ul>
    <h3>✨ Neue Funktionen (Features)</h3>
    <ul>
        <li><strong>Automatische Netzwerk-Synchronisation:</strong> Das Programm erkennt nun beim allerersten Start (nach Auswahl des Daten-Grundpfad) sofort alle bereits im Netzwerk existierenden Firmen und bindet diese automatisch in die lokale Konfiguration ein. Zudem wurde sichergestellt und dokumentiert, dass bei jedem Neustart der Anwendung auch nachträglich von anderen Nutzern neu angelegte Firmen erkannt und synchronisiert werden.</li>
        <li><strong>Kommandozeilen-Parameter --renr (Rechnungsnummer-Überschreibung):</strong> Bei CLI-Aufrufen kann die Rechnungsnummer nun explizit von außen vorgegeben werden.</li>
        <li><strong>Schnittstellen-Datei renr.csv:</strong> Bei jeder erfolgreichen Rechnungserstellung per CLI wird die zuletzt vergebene Rechnungsnummer in die Datei renr.csv im jeweiligen Firmenordner geschrieben. Dies ermöglicht Fremdprogrammen das einfache Auslesen der Nummer für den nächsten Lauf.</li>
        <li><strong>Kommandozeilen-Parameter --kopie (Zusätzlicher Export):</strong> Rechnungen können per CLI-Aufruf nun automatisch in ein externes Wunsch-Verzeichnis kopiert werden. Die Dateien werden wie gewohnt sicher im internen Firmenarchiv (rchn/are) abgelegt und zusätzlich in den übergebenen Pfad kopiert. Dies unterstützt ZUGFeRD-PDFs, XRechnung (XML + Begleit-PDF) und Papierrechnungen und funktioniert sowohl im vollautomatischen Modus (--auto) als auch beim Starten der Bearbeitungsmaske (--edit).</li>
        <li><strong>Dynamischer CLI-Beispielaufruf:</strong> Im Reiter „Einstellungen“ wird ab sofort ein dynamischer Beispielbefehl für die Kommandozeile angezeigt. Dieser ist mit den echten Daten der aktuell ausgewählten Firma vorausgefüllt und demonstriert die Nutzung der Parameter --auto, --profil, --renr, --rechnung und --kopie.</li>
    </ul>

    <h2>08.11.2026</h2>
    <h3>Neue Funktionen & Verbesserungen</h3>
    <ul>
        <li><strong>Tastatur-gesteuerte Kundensuche (Enter-Shortcut):</strong> In der manuellen Rechnungserfassung (📝 ERSTELLEN-Tab) öffnen die Eingabefelder für Kundennummer und Kunde Name nun direkt die entsprechende Suchbox, wenn die Enter-Taste betätigt wird.<br>
        <em>Bedienkomfort:</em> Die Suchfenster erlauben eine blitzschnelle Navigation mit den Pfeiltasten (Hoch/Runter) durch die Trefferliste sowie ein sofortiges Übernehmen des ausgewählten Kunden per Enter. Exakt 1 eindeutiger Treffer wird bei Enter direkt übernommen; über ESC lässt sich das Suchfenster jederzeit ohne Übernahme schließen.</li>
        <li><strong>Intelligente Sicherheitsabfrage beim Beenden:</strong> Das Programm warnt nun zuverlässig vor dem ungespeicherten Schließen, sobald Positionen in der Bearbeitungsmaske erfasst wurden (sowohl beim Klick auf das rote Fenster-X als auch beim Beenden-Button im Footer). Nach erfolgreichem Speichern und PDF-Generierung wird das Programm hingegen ohne Rückfrage sauber beendet (skip_warning).</li>
        <li><strong>Automatisierte CSV-Archivierung (arecsv):</strong> Zeitgleich zur PDF-Erstellung im Jahresunterordner von are wird nun im neuen Ordner arecsv (ebenfalls nach Jahren strukturiert) zu jeder Rechnung eine namensgleiche CSV-Datei für externe Analysen und Buchhaltungsimporte gesichert.</li>
        <li><strong>Kompakteres PDF-Layout & Falzmarken:</strong> Optimierter, kompakter Zeilenabstand (1,1-fach) sowie kleinere, übersichtlichere Schriften für Kunden- und Kopfdaten. Optionale Ein-/Ausschaltbarkeit von dezenten Falz- und Lochmarken für DIN-Lang-Umschläge in den Firmeneinstellungen.</li>
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
