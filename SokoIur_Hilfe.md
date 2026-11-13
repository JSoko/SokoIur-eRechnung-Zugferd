## Inhaltsverzeichnis

        
    
    
    
        # SokoIur eRechnung - Handbuch

        **Version: 2.000181**

    ## 1. Zielgruppe, Zweck & Schnellstart 🟢

    
    ### Für wen und what ist das Programm gedacht?

    Das Programm **SokoIur eRechnung** richtet sich an Freiberufler, Selbstständige, Handwerker sowie kleine bis mittlere Unternehmen, die rechtssichere elektronische Rechnungen im modernen **ZUGFeRD-** und **XRechnung-Standard** erstellen, empfangen und verwalten möchten. Es fungiert entweder als eigenständige Standalone-Lösung für den Arbeitsplatz oder als unsichtbare „Druck-Engine“ im Hintergrund, die von externen Branchenprogrammen via Kommandozeile ferngesteuert werden kann.

    ### Welche Aufgaben kann das Programm erfüllen?

    
        * **Ausgangsrechnungen:** Schreiben und Generieren von GoBD-konformen Rechnungen inkl. automatischer Steuerberechnung, optionalem Girocode (QR-Code) und integriertem PDF-Briefpapier.

        * **Eingangsrechnungen:** Automatisierte formelle Prüfung nach EN 16931 / § 14 UStG, Duplikatskontrolle (Hash & Inhalt) und revisionsvorbereitende Archivierung.

        * **Buchhaltung & Export:** Erstellung von Ein- und Ausgangsjournalen als PDF oder CSV sowie direkter DATEV-Export (EXTF) mit automatischem Steuer-Splitting.

        * **Netzwerk- & Mehrplatzbetrieb:** Parallele Nutzung über ein zentrales Netzlaufwerk mit integriertem File-Locking (Sperrdateien) zur Vermeidung von Konflikten.

    

    ### Installation & Ersteinrichtung

    Die Anwendung (`.exe`) kann in einem beliebigen Ordner auf Ihrem PC abgelegt werden – auch in systemgeschützten Verzeichnissen wie `C:\Programme`. Lokale Geräteeinstellungen speichert das Programm automatisch sicher in Ihrem Windows-Benutzerverzeichnis (`%LOCALAPPDATA%\SokoIur_eRechnung`), sodass keine Administratorrechte für den täglichen Betrieb nötig sind.

    
    
        **⚡ In 3 Schritten zur ersten Rechnung (Quickstart für Eilige):**

        1. **Grundpfad wählen:** Beim ersten Start einen zentralen Datenspeicherort (bei Mehrplatznutzung ein Netzlaufwerk) festlegen.

        2. **Briefbogen hinterlegen:** Im Reiter **⚙️ Konfig.** über den Button *„Briefbogen hinterlegen“* Ihre PDF-Vorlage hochladen.

        3. **Rechnung schreiben:** In den Reiter **📝 ERSTELLEN** wechseln, Kundendaten eintragen, Positionen hinzufügen und unten auf *„Zugpferdrechnung erstellen & öffnen (Alt+P)“* klicken.
    

    **WICHTIGER HINWEIS ZUM DATENSPEICHERORT:** Dieser Ordner darf sich aus Sicherheits- und Updategründen NICHT innerhalb oder unterhalb des Programmordners befinden! Wenn Sie das Programm von mehreren Rechnern aus nutzen möchten, wählen Sie hier zwingend ein freigegebenes Netzwerklaufwerk aus.

    Anschließend legt das Programm dort alle benötigten Unterordner und leeren Konfigurations-Dateien (`.csv`) automatisch für Ihre erste Firma an.

    
    ### Briefbogen hinterlegen:

    Um Ihr eigenes Rechnungsdesign (Logo, Fußzeile etc.) als Hintergrund für die Rechnungen zu verwenden, wechseln Sie in den Reiter **⚙️ Konfig.** und klicken Sie im Bereich der Firmendaten auf den Button **„📄 Briefbogen hinterlegen“**. Wählen Sie dort einfach Ihre PDF-Vorlage aus.

    *Tipp:* Verfügt Ihr Briefbogen über zwei Seiten, nutzt das Programm für die erste Rechnungsseite die erste Seite des Briefbogens. Für alle Folgeseiten nutzt es die zweite Seite. Wenn Ihr Briefbogen nur aus einer Seite besteht, deckt das Programm auf Folgeseiten den oberen Kopfbereich automatisch unsichtbar ab.

    
    ## 2. Haftungsausschluss, Support & Datenschutz

    ### Haftungsausschluss

    Das Programm „SokoIur eRechnung“ wird Ihnen unentgeltlich zur Verfügung gestellt. Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische Umsetzung der komplexen ZUGFeRD- und XRechnung-Spezifikationen, wird ausdrücklich ausgeschlossen.

    ### Gewerbliche Nutzung & Support

    Die Nutzung ist kostenfrei. Wenn Sie das Programm gewerblich nutzen und die Weiterentwicklung wertschätzen, können Sie eine freiwillige Zahlung leisten. Kostenloser, individueller Support kann nicht geleistet werden.

    
        **Kontakt:** Webseite: [https://erech.6078.de](https://erech.6078.de) | E-Mail: [SokoIur@6078.de](mailto:SokoIur@6078.de)
    

    ## 2.1 Lizenzerklärung (Freeware / Donationware)

    **1. Nutzungsrechte:** Das Programm (ausführbare Datei) wird als Freeware/Donationware bereitgestellt. Die private und gewerbliche Nutzung ist kostenfrei gestattet.

    **2. Weitergabe:** Die Software darf unverändert kostenlos weitergegeben werden. Kommerzieller Vertrieb ist untersagt.

    **3. Quellcode:** Der Quellcode ist auf GitHub einsehbar. Die .exe darf nicht dekompiliert oder manipuliert werden.

    **4. Drittkomponenten:** Dieses Programm nutzt Open-Source-Bibliotheken (Python, CustomTkinter, ReportLab, pypdf, qrcode).

    
    ## 3. Programmaufruf & CLI (Power-User Cheat-Sheet) 🔵

    SokoIur eRechnung is ein Rechnungstool zur Erstellung elektronischer Rechnungen. Es kann komplett über die grafische Oberfläche (GUI) gesteuert werden oder als "Druck-Engine" für externe Branchensoftware fungieren.

    
    ### Tastenkürzel-Übersicht (GUI):

    
        * `Alt + E` -> Zum Reiter ERSTELLEN wechseln

        * `Alt + F` -> Zum Reiter ERFASSEN wechseln

        * `Alt + A` -> Zum Reiter AUSGANG wechseln

        * `Alt + I` -> Zum Reiter EINGANG wechseln

        * `Alt + K` -> Zum Reiter Konfig. wechseln

        * `F1` -> Hilfe & Info aufrufen

        * `Alt + L` -> Letzte Rechnungs-CSV laden

        * `Alt + T` -> Texte bearbeiten (Header, Einleitung, Gruß)

        * `Alt + P` -> ZUGFeRD-Rechnung generieren, öffnen & beenden

        * `+` (Plus-Taste) -> Neue Position im Formular hinzufügen

    

    ## 3.1 Die Benutzeroberfläche (Tabs) im Detail

    *Tipp: Sie können zwischen allen Reitern schnell über die Tastatur wechseln. Halten Sie dazu die **Alt-Taste** gedrückt und tippen Sie den unterstrichenen Buchstaben der Tab-Überschrift.*

    ### 📝 E̲RSTELLEN (Ausgangsrechnungen schreiben)

    Hier erfassen und generieren Sie Ihre eigenen Ausgangsrechnungen an Kunden inkl. automatischer Steuerberechnung.

    ### 📥 ERF̲ASSEN (Eingangsrechnungen prüfen)

    Haltautomatisierte Prüfung, Erfassung und Archivierung von Rechnungen Ihrer Lieferanten (Prüfung nach EN 16931 / § 14 UStG).

    ### 📊 A̲USGANG (Ausgangsjournal)

    Auswertung der geschriebenen Rechnungen als PDF, CSV oder DATEV-Export.

    ### 📊 EI̲NGANG (Eingangsjournal & Verwaltung)

    Durchsuchen, Verwalten und Auswerten der erfassten Eingangsrechnungen (Storno-Funktion inklusive).

    ### ⚙️ K̲onfig. (Einstellungen & Stammdaten)

    Zentrale Konfiguration Ihrer Firmen, Nummernkreise, DATEV-Konten und Stammdaten mit hilfreichen Tooltips.

    ### ℹ️ Info (Hilfe & Statistik)

    Dokumentation, Version, Statistiken und Update-Suche.

    
    ## 3.2 Die Kommandozeilenparameter (CLI Cheat-Sheet) 🔵

    
        
            Parameter
            Beschreibung / Verwendung
        
        
            `--auto`
            Startet die Rechnungserstellung vollautomatisch unsichtbar im Hintergrund.
        
        
            `--edit`
            Startet die GUI zur manuellen Nachbearbeitung (enthält Schutz vor versehentlichem Schließen).
        
        
            `--profil "Name"`
            Wählt das Firmenprofil aus (bricht bei nicht existierendem Profil sicherheitshalber ab).
        
        
            `--renr "Nummer"`
            Überschreibt die in der CSV enthaltene Rechnungsnummer.
        
        
            `--rechnung "Pfad"`
            Pfad zur einzulesenden `rechnung.csv` (z. B. Export-Datei aus Fremdsoftware).
        
        
            `--kopie "Pfad"`
            Zusätzliches Zielverzeichnis für eine Kopie der generierten Rechnung.
        
    

    ## 3.3 Programmfunktionen, Verwendungsszenarien & Anwendungsfälle

    ### Kernfunktionen & Typische Szenarien

    **Szenario A (Standalone):** Freiberufler nutzen das Tool als Abrechnungswerkzeug für Kunden, Artikel und DATEV-Export.

    **Szenario B (Druck-Engine):** Mittelständische Branchensoftware übergibt CSV-Daten per CLI (`--auto`), das Tool bettet sie in den Briefbogen ein und versendet ZUGFeRD-PDFs ohne GUI.

    ### Spezifische Anwendungsfälle (Use Cases)

    
        * **Behörden (B2G - XRechnung):** Leitweg-ID im Feld "E-Mail / Leitweg-ID" eintragen, Endpoint-Schema auf `0204` setzen. Generiert reine XML-Dateien für Upload-Portale (ZRE/OZG-RE) und Begleit-PDFs.

        * **Geschäftskunden (B2B - E-Rechnungspflicht):** ZUGFeRD-Button nutzen. Enthält Menschen-lesbare PDF-Ansicht und unsichtbare EN 16931 XML-Daten.

        * **Stornorechnung:** Alte Rechnung via CSV laden, Beträge ins Minus setzen, Hinweistexte anpassen.

        * **Girocode:** EPC-QR-Code aufdrucken für schnelles Scannen und Bezahlen per Banking-App.

    

    ## 4. Ordnerstruktur und Admin-Guide 🔵

    Das Programm trennt strikt zwischen Programmdateien (Installation), lokalen Einstellungen (AppData) und Firmendaten (Daten-Grundpfad auf dem Netzlaufwerk).

    
    
        **🛡️ Admin-Hinweise zum Netzwerkbetrieb & File-Locking:**

        - Das Programm nutzt Sperrdateien (`erechnung.lock` und `erfassung.lock`) im Firmenverzeichnis, um gleichzeitige Schreibkonflikte im Netzwerk zu verhindern.

        - Sollte ein Arbeitsplatz abstürzen, erkennt das System verwaiste Locks und erlaubt nach einer Sicherheitswarnung das manuelle Entfernen der Sperre ("Lock entfernen").

        - Lokale Konfigurationen landen sicher in `%LOCALAPPDATA%\SokoIur_eRechnung`, was UAC-Berechtigungskonflikte ausschließt.
    

    ## 5. Jahreswechsel

    Ändern Sie in den "Einstellungen" einfach das "Aktuelle Rechnungsjahr" im Dropdown oder legen Sie ein neues Firmenprofil an.

    ## 6. Mandanten, Datenbanken & Firmendaten

    Sie können im Reiter "Konfig." verschiedene Firmenprofile verwalten. Das Programm synchronisiert neue Firmen automatisch über den geteilten Daten-Grundpfad.

    ## 7. Rechnungspositionen, Leistungszeitraum & Duplikate

    Ist im Kopf UND in der Position ein Zeitraum angegeben, muss der Positionszeitraum zwingend innerhalb des Kopf-Zeitraums liegen.

    ## 8. Rechnungsformate, Papierrechnung & elektronische Empfängeradresse

    Das Programm unterstützt ZUGFeRD (Hybrid-PDF mit XML), reine XRechnung (XML + Begleit-PDF) und Papierrechnungen (Übergangslösung).

    ## 9. Datumseingaben

    Zulässige Formate: `TTMMJJ, TT,MM,JJ, TT.MM.JJJJ, TT,MM,JJJJ` oder `JJJJ-MM-TT`.

    ## 10. Standardtexte & Formatierungen

    Über "Texte bearbeiten" (`Alt+T`) legen Sie Zahlungsbedingungen (BT-20) und Rechnungsvermerke (BT-22) fest. Formatierungs-Kürzel: Zeilenumbruch `~cr`, Fett `~f Text f~`, Kursiv `~k Text k~`.

    ## 11. Eingangsrechnungen erfassen und auswerten

    Legen Sie neue Eingangsrechnungen in den Ordner `reneu`. Das Programm prüft diese automatisiert. Fehlerhafte Belege werden abgewiesen. Nach erfolgreicher Erfassung wird der Beleg im Archiv (`rchn`) gespeichert und im Journal (`eausw`) vermerkt.

    ## 11.8 Hinweise zur revisionssicheren Archivierung (Ausblick)

    Zur Erfüllung der GoBD wird empfohlen, die generierten Verzeichnisse (`rchn` und `are`) automatisch in einen **WORM-Onlinespeicher** (z.B. via Nextcloud) zu synchronisieren, der eine nachträgliche Veränderung technisch ausschließt.

    ## 12. DATEV-Export & Buchhaltung 🔵

    SokoIur eRechnung bietet eine integrierte Exportfunktion für die Finanzbuchhaltung (Stapelverarbeitung im ASCII-CSV / EXTF-Format).

    
    
        **WICHTIGER HINWEIS (BETA-FUNKTION):**

        Die DATEV-Exportfunktionen wurden bisher nicht abschließend in einer produktiven DATEV-Umgebung getestet. Bitte übergeben Sie Daten zunächst probeweise mit Testdaten an Ihren Steuerberater, um den fehlerfreien Import (Feldzuordnungen, 7 Pflichtspalten, Längenbeschränkungen) sicherzustellen.
    

    ### 12.1 Konfiguration (SKR03 / SKR04) & Automatisches Steuer-Splitting

    Im Reiter **⚙️ Konfig.** können Sie über **„📈 DATEV-Konten“** Standardkonten für SKR03/SKR04 laden. Rechnungen mit unterschiedlichen Steuersätzen werden beim DATEV-Export automatisch centgenau zerlegt, anteilig zurückgerechnet und mit intelligent vergebenen Soll/Haben-Kennzeichen (S/H) versehen.

    ## 13. GitHub & Updates

    Quellcode und Releases sind auf GitHub einsehbar. Über die Update-Funktion wird die neue Version direkt in Ihr Netzlaufwerk geladen.

    ## 14. Import-Formate (CSV)

    Alle CSV-Dateien müssen semikolongetrennt (`;`) und im Format UTF-8 vorliegen (bei ANSI-Dateien aus Excel erfolgt eine automatische Reparatur).

    ## 15. Mini-Glossar für Einsteiger

    
        * **ZUGFeRD:** Ein Hybrid-Format, das eine normale PDF-Ansicht für Menschen mit einer unsichtbaren XML-Datei für Computer/Buchhaltung kombiniert.

        * **XRechnung:** Ein reines XML-Datenformat, das vor allem von öffentlichen Auftraggebern (Behörden) vorgeschrieben wird.

        * **Leitweg-ID:** Die digitale Postanschrift für Rechnungen an Behörden (erscheint anstelle einer normalen E-Mail-Adresse).

        * **WORM-Speicher:** (Write Once, Read Many) Ein Speichersystem, bei dem Dateien nach dem Schreiben nicht mehr verändert oder gelöscht werden können (wichtig für GoBD-Konformität).

        * **DATEV EXTF:** Ein standardisiertes ASCII-CSV-Format zum verlustfreien Import von Buchungsstapeln in die Kanzlei-Software des Steuerberaters.

    

    ## 16. FAQ – Häufig gestellte Fragen

    
    
        **Wie kann ich mein eigenes Logo auf die Rechnung drucken?**
        Das Programm nutzt eine PDF-Vorlage als Hintergrund. Erstellen Sie z. B. in Word Ihr Briefpapier mit Logo, speichern Sie es als PDF und hinterlegen Sie es im Reiter *Konfig.* unter „Briefbogen hinterlegen“.

    
    
    
        **Wie setze ich die Rechnungsnummern für das neue Jahr zurück?**
        Wechseln Sie im Reiter *Konfig.* einfach das „Aktuelle Rechnungsjahr“ und korrigieren Sie darunter die „Letzte Rechnungs-Nr.“ einmalig händisch auf den Startwert.

    
    
    
        **Wie erstelle ich eine XRechnung für Behörden?**
        Tragen Sie bei der Rechnungserstellung in das Feld „E-Mail / Leitweg-ID“ die Leitweg-ID ein und setzen Sie das „Endpoint-Schema“ auf `0204`.

    
    
    
        **Das Programm startet nicht mehr oder ist gesperrt. Was tun?**
        Wenn eine Firma gesperrt ist (Lock), wurde das Programm evtl. unsanft beendet. Beim Versuch, den Reiter zu wechseln, erscheint ein Hinweisfenster, in dem Sie den „Lock entfernen“ können.

    

    ## 17. Schlagwortverzeichnis (Index)

    
        **B**

        [Briefbogen hinterlegen](#kap1)

        [Buchhaltung](#kap12)
        **D**

        [Daten-Speicherort](#kap1)

        [Datenschutz](#kap2)

        [DATEV-Export](#kap12)
        **E**

        [Eingangsrechnungen prüfen](#kap11)

        [E-Rechnungspflicht](#kap3_3)
        **G**

        [Girocode (QR-Code)](#kap3_3)
        **I**

        [Import (Kunden & Produkte)](#kap14)
        **J**

        [Jahreswechsel](#kap5)

        [Journale (Ausgang / Eingang)](#kap3_1)
        **L**

        [Leitweg-ID](#kap3_3)
        **M**

        [Mandanten & Firmenprofile](#kap6)
        **N**

        [Netzwerkbetrieb](#kap1)
        **S**

        [Standardtexte](#kap10)

        [Stornorechnung](#kap3_3)
        **X**

        [XRechnung](#kap8)
        **Z**

        [ZUGFeRD](#kap8)
    
    ---

    
        © Joachim Sokolowski, Offenbacher Str. 99, 63263 Neu-Isenburg