"""
hilfe_texte.py
--------------
HTML-Generierung für das Handbuch.
"""

def get_doku_html(version_string):
    return f"""<!DOCTYPE html>
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
            <li><a class="toc-link" href="#kap2">2. Haftungsausschluss & Datenschutz</a></li>
            <li><a class="toc-link" href="#kap3">3. Programmbeschreibung & Aufruf (CLI / GUI)</a></li>
            <li><a class="toc-link" href="#kap4">4. Ordnerstruktur und Dateien</a></li>
            <li><a class="toc-link" href="#kap5">5. Jahreswechsel</a></li>
            <li><a class="toc-link" href="#kap6">6. Mandanten & Datenbanken</a></li>
            <li><a class="toc-link" href="#kap7">7. Rechnungspositionen & Leistungszeitraum</a></li>
            <li><a class="toc-link" href="#kap8">8. Datumseingaben</a></li>
            <li><a class="toc-link" href="#kap9">9. Textformatierungen</a></li>
            <li><a class="toc-link" href="#kap10">10. Journal & Auswertungen</a></li>
            <li><a class="toc-link" href="#kap11">11. GitHub & Updates</a></li>
            <li><a class="toc-link" href="#kap12">12. Lizenzen & Drittparty-Module</a></li>
        </ul>
    </div>

    <h2 id="kap1">1. Installation & Ersteinrichtung</h2>
    <p>Die Anwendung (<code>.exe</code>) ist vollständig portabel und kann in einem beliebigen Ordner auf Ihrem PC abgelegt werden.</p>
    <h3>Ersteinrichtung und Datenspeicherort:</h3>
    <p>Beim allerersten Start des Programms werden Sie aufgefordert, einen Grundpfad für die Datenspeicherung auszuwählen.</p>
    <div class="highlight">
        <strong>WICHTIG:</strong> Dieser Ordner darf sich aus Sicherheits- und Updategründen NICHT innerhalb oder unterhalb des Programmordners befinden!<br>
        Wenn Sie das Programm von mehreren Rechnern aus nutzen möchten, wählen Sie hier zwingend ein freigegebenes Netzwerklaufwerk aus.
    </div>
    <p>Anschließend legt das Programm dort alle benötigten Unterordner und leeren Konfigurations-Dateien (<code>.csv</code>) automatisch für Ihre erste Firma an.</p>
    <h3>Briefbogen:</h3>
    <p>Legen Sie in den soeben erstellten Firmenordner eine Datei namens <code>briefbogen.pdf</code>. Diese wird als Hintergrund für die Rechnung verwendet.</p>
    <p><em>Tipp:</em> Verfügt Ihr Briefbogen über zwei Seiten, nutzt das Programm für die erste Rechnungsseite die erste Seite des Briefbogens. Für alle Folgeseiten nutzt es die zweite Seite. Wenn Ihr Briefbogen nur aus einer Seite besteht, deckt das Programm auf Folgeseiten den oberen Kopfbereich automatisch unsichtbar ab, sodass nur die Fußzeile erhalten bleibt.</p>

    <h2 id="kap2">2. Haftungsausschluss & Datenschutz</h2>
    <p>Das Programm "SokoIur eRechnung" wird Ihnen unentgeltlich (als Gefälligkeit / Schenkung) zur Verfügung gestellt.</p>
    <p>Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische Umsetzung der komplexen ZUGFeRD/XRechnung-Spezifikationen, wird hiermit ausdrücklich ausgeschlossen. Es wird ausdrücklich darauf hingewiesen, dass auch für das Anerkennen der erstellten Rechnungen durch die Adressaten oder die Finanzämter keinerlei Gewähr oder Haftung übernommen wird.</p>
    <p>Die Haftung ist gemäß § 521 BGB auf Vorsatz und grobe Fahrlässigkeit beschränkt. Die Nutzung im geschäftlichen Verkehr erfolgt auf Ihre eigene Gefahr. Bitte prüfen Sie erzeugte Rechnungen stichprobenartig.</p>
    <h3>Datenschutz / Verbindungen:</h3>
    <p>Das Programm arbeitet komplett lokal. Ausschließlich zur Updateprüfung, die NICHT automatisch durchgeführt sondern durch den entsprechenden Button vom Benutzer angestoßen wird, wird eine Datenverbindung zu GitHub benötigt und aufgebaut.</p>

    <h2 id="kap3">3. Programmbeschreibung & Aufruf (CLI / GUI)</h2>
    <p>SokoIur eRechnung ist ein Rechnungstool zur Erstellung ZUGFeRD-konformer PDFs. Es kann entweder komplett über die grafische Oberfläche (GUI) gesteuert werden, oder es fungiert als "Druck-Engine" für externe Programme.</p>
    <h3>Aufruf über Kommandozeile (CLI):</h3>
    <ul>
        <li><code>erechnung_generator.exe --auto [Parameter]</code> &rarr; Generiert direkt unsichtbar im Hintergrund</li>
        <li><code>erechnung_generator.exe --edit [Parameter]</code> &rarr; Öffnet die GUI (Manuelle Eingabe) mit den übergebenen Daten, ohne die Rechnungsnummer automatisch hochzuzählen.</li>
    </ul>
    <h3>Verfügbare CLI-Parameter (überschreiben temporär das aktive Profil):</h3>
    <ul>
        <li><code>--profil</code> Name des Firmenprofils (z.B. "Firma 1").</li>
        <li><code>--firma</code> Pfad zur firma.csv.</li>
        <li><code>--rechnung</code> Pfad zur rechnung.csv.</li>
        <li><code>--briefbogen</code> Pfad zur briefbogen.pdf.</li>
        <li><code>--zusatz</code> Pfad zur zusatz.csv.</li>
        <li><code>--gruss</code> Pfad zur gruss.csv.</li>
        <li><code>--header</code> Pfad zur header.csv.</li>
        <li><code>--einleitung</code> Pfad zur einleitung.csv.</li>
        <li><code>--ausgabe</code> Ordner für fertiggestellte PDFs.</li>
        <li><code>--auswertungen</code> Ordner für das Rechnungs-Journal.</li>
        <li><code>--jahr</code> Zwingt das Programm in ein spezielles Rechnungsjahr.</li>
        <li><code>--no-open</code> Verhindert das automatische Öffnen der PDF nach der Erstellung.</li>
    </ul>

    <h2 id="kap4">4. Ordnerstruktur und Dateien</h2>
    <p>Das Programm verwendet eine feste Ordnerstruktur, die sich an einem von Ihnen in den Einstellungen gewählten "Daten-Grundpfad" orientiert.</p>
    <div class="highlight">
        <strong>Netzwerkbetrieb & Versionsschutz:</strong><br>
        Das Programm (.exe) selbst kann lokal auf verschiedenen Rechnern installiert sein, während der Datenspeicherpfad auf einem freigegebenen Netzwerklaufwerk liegt. So greifen alle Nutzer auf denselben Datenbestand zu.<br><br>
        <strong>WICHTIG:</strong> Sobald ein Rechner mit einer neueren Programmversion auf die Netzwerkdaten zugreift, wird diese Version in einer unsichtbaren Datei namens <code>erech.txt</code> im Daten-Grundpfad hinterlegt. Versucht danach ein Rechner mit einer älteren Programmversion auf diese Daten zuzugreifen, wird der Zugriff zum Schutz vor Datenkorruption blockiert. Das Programm bietet Ihnen dann automatisch an, sich über GitHub auf die aktuelle Version zu aktualisieren, bevor Sie weiterarbeiten können.
    </div>
    <p>Der Ordner für die jeweilige Firma wird automatisch anhand des Firmennamens (ohne Leerzeichen) im Grundpfad generiert. Innerhalb dieses Firmenordners wird folgende Struktur angelegt:</p>
    <ul>
        <li><strong>/ (Firmen-Hauptordner) :</strong> Hier liegen alle zentralen Stammdaten.<br>
        (<code>firma.csv, rechnung.csv, kunden.csv, produkte.csv, zusatz.csv, gruss.csv, header.csv, einleitung.csv</code> sowie der <code>briefbogen.pdf</code>).</li>
        <li><strong>/ausw/ :</strong> Dieser Ordner sammelt alle Dateien und Journale für die Auswertungen.</li>
        <li><strong>/are/ :</strong> Hier werden alle Ausgangsrechnungen als fertige PDFs archiviert, automatisch sortiert in Jahresunterordner (z.B. "2026"). Bei einem Jahreswechsel generiert das Programm den neuen Ordner selbstständig.<br>
        <em>(Hinweis: Eine Erweiterung des Programms um ein Modul für Eingangsrechnungen ist geplant, weshalb dieser Ordner "are" für Ausgangsrechnungen steht).</em></li>
    </ul>

    <h2 id="kap5">5. Jahreswechsel</h2>
    <p>Zum Jahreswechsel (z.B. von 2026 auf 2027) haben Sie zwei Möglichkeiten:</p>
    <ul>
        <li><strong>A) Neues Profil anlegen:</strong> Klicken Sie oben auf "+ Neu" und nennen Sie es z.B. "Firma 2027". Das Programm legt automatisch neue, komplett leere Ausgabe- und Auswertungs-Ordner für Sie an.</li>
        <li><strong>B) Vorhandenes Profil anpassen:</strong> Gehen Sie in die "Einstellungen", ändern Sie das "Aktuelle Rechnungsjahr" im Dropdown z.B. auf 2027. Die Ordner werden bei Bestätigung generiert.<br>
        Um Journale der Vorjahre auszudrucken, wechseln Sie in den Reiter "Auswertungen" und ändern das Jahres-Dropdown einfach auf das alte Jahr (z.B. "2026").</li>
    </ul>

    <h2 id="kap6">6. Mandanten & Datenbanken</h2>
    <h3>Mandantenfähigkeit (Firmen):</h3>
    <p>Sie können oben links über das Dropdown-Menü bis zu 5 verschiedene Firmenprofile anlegen. Bei der Neuanlage werden Sie, genau wie beim Erststart, nach dem gewünschten Datenspeicherort (Grundpfad) für diese neue Firma gefragt. Jede Firma verwaltet somit ihre eigenen Dateipfade.</p>
    <div class="highlight">
        <strong>WICHTIG:</strong> Wenn Sie eine Firma anlegen oder bearbeiten, müssen für eine gültige ZUGFeRD eRechnung mindestens Name, PLZ, Ort, IBAN und USt-Id (bzw. Steuernummer) eingegeben werden!
    </div>
    <h3>Firma löschen:</h3>
    <p>Um ein Profil zu löschen, klicken Sie auf "Löschen".<br>
    Das Sicherheitspasswort ist ein kleines Rätsel: <em>Wie lautet die 5-stellige Haupt-Postleitzahl von Neu-Isenburg?</em></p>
    <h3>Kundenbank & Produktebank:</h3>
    <p>Ihre erfassten Kunden und Produkte werden gespeichert. In der Rechnungserfassung dient die "Bezeichnung" und das Suchen-Feld als Auto-Fill für diese Bestände.</p>

    <h2 id="kap7">7. Rechnungspositionen & Leistungszeitraum</h2>
    <div class="highlight">
        <strong>WICHTIG:</strong> Ist im Kopf UND in der Position ein Zeitraum angegeben, muss der Positionszeitraum ZWINGEND kalendarisch INNERHALB des Kopf-Zeitraums liegen. (Tipp: Ist Start- und Enddatum identisch, wird auf dem PDF automatisch nur ein einzelnes Datum gedruckt).
    </div>
    <p>Negative Preise (Rabatte) werden automatisch normgerecht berechnet.</p>

    <h2 id="kap8">8. Datumseingaben</h2>
    <p>Zulässige Formate: <code>TTMMJJ, TT,MM,JJ, TT.MM.JJJJ, TT,MM,JJJJ</code> oder <code>JJJJ-MM-TT</code>.</p>

    <h2 id="kap9">9. Textformatierungen</h2>
    <ul>
        <li>Zeilenumbruch in der CSV: <code>~cr</code></li>
        <li>Fett drucken: <code>~f Ihr Text f~</code></li>
        <li>Kursiv drucken: <code>~k Ihr Text k~</code></li>
    </ul>

    <h2 id="kap10">10. Journal & Auswertungen</h2>
    <p>Das Programm erstellt bei jedem Speichervorgang im Hintergrund eine Monats-CSV (z.B. <code>re202611.csv</code>). Im Reiter "Auswertungen" können Sie daraus mit einem Klick ein sauberes PDF-Journal erzeugen.</p>

    <h2 id="kap11">11. GitHub & Updates</h2>
    <p>Der Quellcode des Programms ist auf GitHub einsehbar:<br>
    <a href="https://github.com/JSoko/SokoIur-eRechnung-Zugferd/releases/new" target="_blank">Repository ansehen</a></p>
    <p>Neue Versionen können Sie hier herunterladen:<br>
    <a href="https://github.com/JSoko/SokoIur-eRechnung-Zugferd/releases" target="_blank">Releases ansehen</a></p>

    <h2 id="kap12">12. Lizenzen & Drittparty-Module</h2>
    <p>Dieses Programm wurde in Python geschrieben und nutzt für bestimmte Funktionen Open-Source-Bibliotheken von Drittanbietern. Nachfolgend finden Sie eine Auflistung der verwendeten Hauptkomponenten sowie Links zu deren jeweiligen Lizenzbedingungen:</p>
    <ul>
        <li><strong>Python</strong> (Programmiersprache)<br>Lizenz: Python Software Foundation License (PSF) <br><a href="https://docs.python.org/3/license.html" target="_blank">Zur Lizenz</a></li>
        <li><strong>CustomTkinter</strong> (Für das Design der Benutzeroberfläche)<br>Lizenz: MIT License <br><a href="https://github.com/TomSchimansky/CustomTkinter/blob/master/LICENSE" target="_blank">Zur Lizenz</a></li>
        <li><strong>ReportLab</strong> (Für die PDF-Generierung des Rechnungslayouts)<br>Lizenz: BSD License <br><a href="https://bitbucket.org/rptlab/reportlab/src/master/LICENSE.txt" target="_blank">Zur Lizenz</a></li>
        <li><strong>pypdf</strong> (Für das Einbetten der ZUGFeRD XML-Datei in das PDF)<br>Lizenz: BSD 3-Clause License <br><a href="https://github.com/py-pdf/pypdf/blob/main/LICENSE" target="_blank">Zur Lizenz</a></li>
    </ul>
    
    <br><br><br>
</body>
</html>"""
