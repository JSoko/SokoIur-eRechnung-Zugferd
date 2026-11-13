# Changelog – SokoIur eRechnung

    **Aktuelle Version: 2.000181**

    ## Version 2.000151

    ### ✨ UI/UX-Verbesserungen & Einstellungen

    
        * **Schnellnavigation (Shortcuts):** Die Tastenkürzel für den direkten Wechsel der Reiter (z. B. Alt+E für Erstellen) werden nun platzsparend und visuell elegant durch einen Unterstrich im jeweiligen Buchstaben der Tab-Überschrift (z. B. E̲RSTELLEN) signalisiert.

        * **Umbenennung:** Der Reiter „Einstellungen“ wurde in „Konfig.“ (Tastenkürzel Alt+K) umbenannt, um die Tab-Leiste kompakt zu halten.

        * **Modernes Karten-Design:** Der Reiter „Einstellungen“ wurde komplett überarbeitet und in übersichtliche Themen-Karten (Cards) unterteilt.

        * **Hover-Erklärungen (Tooltips):** Wichtige Buttons und Checkboxen in den Einstellungen sind nun mit hilfreichen Tooltips versehen, die beim Darüberfahren mit der Maus Erklärungen einblenden.

        * **DATEV-Konten Manager:** Der Konfigurations-Button für die DATEV-Kontenrahmen (SKR03/SKR04) ist nun prominent im Bereich der Stammdaten integriert.

    
    ## Version 2.000150

    ### ✨ Kommandozeile (CLI) & Fremdprogramm-Integration

    
        * **Strikte Profil-Validierung:** Wird das Programm über `--auto` oder `--edit` mit einem nicht existierenden Firmennamen aufgerufen, bricht es nun mit einer klaren Fehlermeldung ab. Zuvor wurde fälschlicherweise das Standardprofil herangezogen.

        * **Sicherheitswarnung bei Abbruch:** Wird die GUI über den Parameter `--edit` von einem Drittsystem aufgerufen, erscheint nun ein spezifischer Warnhinweis, wenn der Nutzer das Fenster ohne Rechnungserstellung (Beenden / X) schließen möchte. Dies beugt verwaisten Rechnungsnummern im Drittsystem vor.

        * **Saubere Textfelder:** Beim CLI-gesteuerten Einlesen einer temporären Rechnungs-CSV werden alte Anmerkungen (Zusatztexte) aus dem regulären Firmenbetrieb nun korrekt ignoriert, sodass eine saubere Maske zur Verfügung steht.

    
    ## Version 2.000146

    ### ✨ Neue Funktionen & Datenverwaltung

    
        * **Firma leeren:** Eine neue Funktion in den Einstellungen ermöglicht es, alle erfassten Buchungen, Rechnungen und Journale einer Firma vollständig zurückzusetzen. Stammdaten (Kunden, Produkte, Briefbogen) bleiben dabei unberührt.

        * **CSV-Import für Kunden:** Kundendaten können nun per CSV importiert werden. Anhand der Kundennummer werden bestehende Einträge automatisch überschrieben und aktualisiert, neue Kunden werden angehängt.

        * **CSV-Import für Produkte:** Produktdaten können ab sofort aus einer CSV-Datei importiert und an den bestehenden Stamm angehängt werden.

        * **Dokumentation:** Das Handbuch wurde um die genauen Import-Formate (Kopfzeilen) für Kunden und Produkte ergänzt.

    

    ## Version 2.000134

    ### ✨ DATEV-Export & Buchhaltung

    
        * **Automatisierter DATEV-Export:** In den Reitern „Ausgang“ und „Eingang“ können nun vollautomatisch DATEV-konforme ASCII-CSV-Dateien (Stapelverarbeitung) für den Steuerberater erzeugt werden.

        * **Steuer-Splitting:** Rechnungen mit unterschiedlichen Steuersätzen werden beim DATEV-Export automatisch centgenau zerlegt und auf die jeweils passenden Sachkonten aufgeteilt. Die Soll/Haben-Kennzeichen (S/H) werden vom System intelligent vergeben.

        * **DATEV-Konfigurationsmanager:** Im Reiter „Einst.“ wurde ein Manager für die DATEV-Buchhaltung hinzugefügt. Per Knopfdruck lassen sich hier die Standardkonten für den Kontenrahmen **SKR03** oder **SKR04** laden oder individuelle Aufwands-, Erlös- und Sammelkonten pflegen.

    

    ### ✨ Journale & Auswertungen

    
        * **Neue Export-Möglichkeiten:** In den Reitern „Ausgang“ und „Eingang“ wurden Buttons für den direkten CSV-Export hinzugefügt. Journale lassen sich nun auf Knopfdruck wahlweise als PDF (für den Ausdruck) oder als CSV (für den Import in Fremdsysteme oder Excel) generieren.

        * **Automatischer Start:** Nach der Generierung wird das erzeugte Journal (egal ob PDF oder CSV) nun direkt in der jeweiligen Standardanwendung Ihres Computers geöffnet, sodass lange Lade-Rückmeldungen entfallen.

        * **Klarere Ordnerstruktur:** Zur besseren logischen Trennung wurden die systemseitigen Journal-Ordner von `ausw` auf `aausw` (Ausgangsauswertungen) und von `einj` auf `eausw` (Eingangsauswertungen) umbenannt. Die entsprechenden Pfade werden bei neuen Profilen automatisch korrekt gesetzt.

        * **Bugfix PDF-Engine:** Ein iterativer Fehler bei der Erzeugung des Ausgangsjournals (PDF) wurde behoben, der durch falsch übergebene String-Variablen auftreten konnte.

    

    ### ✨ Bugfixes & CLI-Verbesserungen

    
        * **Firmendaten (Falzmarken):** Ein Fehler beim Speichern der Firmendaten wurde behoben. Das Feld 'Falzmarken' wurde korrekt in die Datenbankstruktur aufgenommen, sodass Änderungen nun fehlerfrei gesichert werden.

        * **CLI/Edit-Modus (Temp-Dateien):** Wird die GUI über ein Fremdprogramm mit einer temporären CSV-Datei aufgerufen, überschreibt diese nicht mehr fälschlicherweise den Pfad der echten Rechnungsdatenbank.

        * **Briefbogen-Ladefehler:** Der Briefbogen wird nun auch im Edit-Modus (bei externen Aufrufen) immer zuverlässig und direkt aus dem echten Firmen-Profil geladen, anstatt im Temp-Ordner gesucht zu werden.

        * **CLI-Parameter --renr:** Übergebene Rechnungsnummern aus Fremdprogrammen überschreiben in der GUI nun korrekt den alten Wert aus der CSV-Datei. Unnötige Duplikats-Warnungen bei der automatisierten Rechnungserstellung wurden beseitigt.

        * **Einstellungen (Beispielaufruf):** Der CLI-Beispielbefehl in den Einstellungen lässt sich nun markieren und herauskopieren (Read-Only Feld). Er aktualisiert sich zudem in Echtzeit, sobald die letzte Rechnungsnummer manuell korrigiert wird.

        * **Code-Bereinigung:** Unbenutzte Code-Fragmente wurden zur Fehlervermeidung aus den GUI-Modulen entfernt.

    

    ### 📚 Dokumentation & Handbuch-Erweiterung

    
        * **Funktionsübersicht & Anwendungsfälle:** Das integrierte Handbuch wurde um das neue Kapitel 3.3 ("Programmfunktionen, Verwendungsszenarien & Anwendungsfälle") erweitert. Die Unterschiede zwischen der Rechnungsstellung an Behörden (XRechnung via Leitweg-ID / ZRE-Portal) und an Geschäftskunden gemäß der kommenden E-Rechnungspflicht 2025-2028 (ZUGFeRD via E-Mail) werden klar herausgestellt.

        * **DATEV-Export Dokumentation:** Das Handbuch (Kapitel 12) wurde um eine ausführliche technische Dokumentation der neuen DATEV-Exportfunktionen inkl. ausdrücklichem **Beta-Warnhinweis** (Testlauf mit Steuerberater erforderlich) erweitert.

    

    ## 10.11.2026

    ### ✨ Neue Funktionen & XML-Korrekturen

    
        * **Automatische UTF-8-Konvertierung:** Werden fehlerhaft codierte Rechnungs-CSVs über die Kommandozeile oder die GUI geladen, repariert und konvertiert das Programm diese nun vollautomatisch in das benötigte UTF-8-Format.

        * **Referenzen normkonform getrennt:** Das Feld "Ihr Zeichen" (KundeAktenzeichen) wird als echte Leitweg-Referenz (BuyerReference BT-13) übergeben. Das interne Feld "Unser Zeichen" (Aktenzeichen) wird standardkonform als Rechnungsnotiz (IncludedNote) in die XML geschrieben.

        * **Kommandozeilen-Erweiterung:** Das Kunden-Aktenzeichen kann nun per Parameter `--kunde-az` gesetzt werden.

    

    ## 09.11.2026

    ### 📚 Dokumentation & Handbuch-Erweiterung

    
        * **Revisionssichere Archivierung (Kapitel 11.8):** Das Handbuch wurde um ein dediziertes Kapitel zur revisionssicheren Archivierung nach GoBD in Kombination mit Nextcloud & WORM-Speichern ergänzt.

    
    ### ⚡ Performance & Fehlerbehebungen (Bugfixes)

    
        * **Statistik-Korrektur:** Die Zählung der erstellten Ausgangsrechnungen im Reiter „Info“ wurde korrigiert.

        * **Performance-Boost im Eingangsordner:** Das Einlesen und Prüfen von Eingangsrechnungen wurde extrem beschleunigt (Caching der Journal-Datenbasis).

    
    ### 🛠 System & Architektur

    
        * **Neues Update-System:** Die Update-Prüfung erfolgt nun über erech.6078.de. Updates werden automatisch in das Netzlaufwerk kopiert.

        * **AppData-Nutzung:** Lokale Konfigurationsdateien werden ab sofort sicher im Windows-Benutzerverzeichnis (`%LOCALAPPDATA%`) abgelegt, was UAC-Berechtigungskonflikte behebt.

    

    ---