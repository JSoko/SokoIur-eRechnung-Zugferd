## Inhaltsverzeichnis

        
            
                * [1. Zielgruppe, Zweck & Schnellstart](#kap1)

                * [2. Haftungsausschluss & Lizenzen](#kap2)

                * [3. Verwendungsszenarien & Use Cases](#kap3)

                * [4. Mini-Glossar](#kap4)

                * [5. FAQ – Häufige Fragen](#kap5)

            
            TEIL 2: Anwenderhandbuch
            
                * [6. Die Benutzeroberfläche (Tabs)](#kap6)

                * [7. Schritt-für-Schritt: ZUGFeRD-Rechnung](#kap7)

                * [8. Auswertungen & Einstellungen (Warnung)](#kap8)

                * [9. Rechnungsformate (ZUGFeRD/XML)](#kap9)

                * [10. Eingangsrechnungen erfassen](#kap10)

                * [11. Jahreswechsel](#kap11)

            
            TEIL 3: Administration & IT
            
                * [12. Ordnerstruktur & File-Locking](#kap12)

                * [13. Mandanten & Datenbanken](#kap13)

                * [14. DATEV-Export & Buchhaltung](#kap14)

                * [15. Import-Formate (CSV)](#kap15)

                * [16. Programmaufruf & CLI](#kap16)

                * [17. Revisionssicheres Archiv & GoBD-Audit-Log](#kap17)

                * [18. GitHub & Updates](#kap18)

                * [19. Schlagwortverzeichnis (Index)](#kap19)

            
        
    
    
    
        # SokoIur eRechnung

        ## Das Handbuch

        **Version: 2.000227**

    
    # TEIL 1: Allgemeiner Teil

    ## 1. Zielgruppe, Zweck & Schnellstart

    
    ### Für wen und was ist das Programm gedacht?

    Das Programm **SokoIur eRechnung** richtet sich an Freiberufler, Selbstständige, Handwerker sowie kleine bis mittlere Unternehmen, die rechtssichere elektronische Rechnungen im modernen **ZUGFeRD-** und **XRechnung-Standard** erstellen, empfangen und verwalten möchten. Es fungiert entweder als eigenständige Standalone-Lösung für den Arbeitsplatz oder als unsichtbare „Druck-Engine“ im Hintergrund, die von externen Branchenprogrammen via Kommandozeile ferngesteuert werden kann.

    ### Welche Aufgaben kann das Programm erfüllen?

    
        * **Ausgangsrechnungen:** Schreiben und Generieren von GoBD-konformen Rechnungen inkl. automatischer Steuerberechnung, optionalem Girocode (QR-Code) und integriertem PDF-Briefpapier.

        * **Eingangsrechnungen:** Automatisierte formelle Prüfung nach EN 16931 / § 14 UStG, Duplikatskontrolle (Hash & Inhalt) und revisionsvorbereitende Archivierung.

        * **Buchhaltung & Export:** Erstellung von Ein- und Ausgangsjournalen als PDF oder CSV sowie direkter DATEV-Export (EXTF) mit automatischem Steuer-Splitting.

        * **Netzwerk- & Mehrplatzbetrieb:** Parallele Nutzung über ein zentrales Netzlaufwerk mit integriertem File-Locking (Sperrdateien) zur Vermeidung von Konflikten.

    

    ### Installation & Ersteinrichtung

    Die Anwendung (`.exe`) kann in einem beliebigen Ordner auf Ihrem PC abgelegt werden – auch in systemgeschützten Verzeichnissen wie `C:\Programme`.

    
    
        **⚡ In 3 Schritten zur ersten Rechnung (Quickstart für Eilige):**

        1. **Grundpfad wählen:** Beim ersten Start einen zentralen Datenspeicherort (bei Mehrplatznutzung ein Netzlaufwerk) festlegen.

        2. **Briefbogen hinterlegen:** Im Reiter **⚙️ Konfig.** über den Button *„Briefbogen hinterlegen“* Ihre PDF-Vorlage hochladen.

        3. **Rechnung schreiben:** In den Reiter **📝 ERSTELLEN** wechseln, Kundendaten eintragen, Positionen hinzufügen und unten auf *„Zugpferdrechnung erstellen & öffnen (Alt+P)“* klicken.
    

    **WICHTIGER HINWEIS ZUM DATENSPEICHERORT:** Dieser Ordner darf sich aus Sicherheits- und Updategründen NICHT innerhalb oder unterhalb des Programmordners befinden! Wenn Sie das Programm von mehreren Rechnern aus nutzen möchten, wählen Sie hier zwingend ein freigegebenes Netzwerklaufwerk aus.

    
    ### Briefbogen hinterlegen:

    Um Ihr eigenes Rechnungsdesign (Logo, Fußzeile etc.) als Hintergrund für die Rechnungen zu verwenden, wechseln Sie in den Reiter **⚙️ Konfig.** und klicken Sie im Bereich der Firmendaten auf den Button **„📄 Briefbogen hinterlegen“**. Wählen Sie dort einfach Ihre PDF-Vorlage aus.

    *Tipp:* Verfügt Ihr Briefbogen über zwei Seiten, nutzt das Programm für die erste Rechnungsseite die erste Seite des Briefbogens. Für alle Folgeseiten nutzt es die zweite Seite. Wenn Ihr Briefbogen nur aus einer Seite besteht, deckt das Programm auf Folgeseiten den oberen Kopfbereich automatisch unsichtbar ab.

    
    ## 2. Haftungsausschluss, Support & Lizenzen

    ### Haftungsausschluss

    Das Programm „SokoIur eRechnung“ wird Ihnen unentgeltlich zur Verfügung gestellt. Eine Gewährleistung für die inhaltliche und technische Fehlerfreiheit, insbesondere für die 100%ige korrekte technische Umsetzung der komplexen ZUGFeRD- und XRechnung-Spezifikationen, wird ausdrücklich ausgeschlossen.

    ### Gewerbliche Nutzung & Support

    Die Nutzung ist kostenfrei. Wenn Sie das Programm gewerblich nutzen und die Weiterentwicklung wertschätzen, können Sie eine freiwillige Zahlung leisten. Kostenloser, individueller Support kann nicht geleistet werden.

    
        **Kontakt:** Webseite: [https://erech.6078.de](https://erech.6078.de) | E-Mail: [SokoIur@6078.de](mailto:SokoIur@6078.de)
    

    ### Lizenzerklärung (Freeware / Donationware)

    **1. Nutzungsrechte:** Das Programm (ausführbare Datei) wird als Freeware/Donationware bereitgestellt. Die private und gewerbliche Nutzung ist kostenfrei gestattet.

    **2. Weitergabe:** Die Software darf unverändert kostenlos weitergegeben werden. Kommerzieller Vertrieb ist untersagt.

    **3. Quellcode:** Der Quellcode ist auf [GitHub](https://github.com/JSoko/SokoIur-eRechnung-Zugferd) einsehbar. Die .exe darf nicht dekompiliert oder manipuliert werden.

    **4. Drittkomponenten & Lizenzen:** Dieses Programm wurde in [Python (PSF License)](https://docs.python.org/3/license.html) geschrieben und nutzt folgende Open-Source-Bibliotheken:

    
        * **CustomTkinter:** [MIT License](https://github.com/TomSchimansky/CustomTkinter/blob/master/LICENSE)

        * **ReportLab:** [BSD License](https://www.reportlab.com/open_source/license/)

        * **pypdf:** [BSD 3-Clause License](https://github.com/py-pdf/pypdf/blob/main/LICENSE)

        * **qrcode:** [BSD 3-Clause License](https://github.com/lincolnloop/python-qrcode/blob/master/LICENSE)

    
    
    ## 3. Verwendungsszenarien & Use Cases

    ### Typische Szenarien

    **Szenario A (Standalone):** Freiberufler nutzen das Tool als alleiniges Abrechnungswerkzeug für Kunden, Artikel und DATEV-Export.

    **Szenario B (Druck-Engine):** Mittelständische Branchensoftware übergibt CSV-Daten per CLI, das Tool bettet sie in den Briefbogen ein und versendet ZUGFeRD-PDFs ohne dass die GUI sichtbar wird.

    ### Spezifische Anwendungsfälle (Use Cases)

    
        * **Behörden (B2G - XRechnung):** Leitweg-ID im Feld "E-Mail / Leitweg-ID" eintragen, Endpoint-Schema auf `0204` setzen. Generiert reine XML-Dateien für Upload-Portale (ZRE/OZG-RE) und Begleit-PDFs.

        * **Geschäftskunden (B2B - E-Rechnungspflicht):** ZUGFeRD-Button nutzen. Enthält Menschen-lesbare PDF-Ansicht und unsichtbare EN 16931 XML-Daten.

        * **Stornorechnung:** Alte Rechnung via CSV laden, Beträge ins Minus setzen, Hinweistexte anpassen.

        * **Girocode:** EPC-QR-Code aufdrucken für schnelles Scannen und Bezahlen per Banking-App.

    

    ## 4. Mini-Glossar

    
        * **ZUGFeRD:** Ein Hybrid-Format, das eine normale PDF-Ansicht für Menschen mit einer unsichtbaren XML-Datei für Computer/Buchhaltung kombiniert.

        * **XRechnung:** Ein reines XML-Datenformat, das vor allem von öffentlichen Auftraggebern (Behörden) vorgeschrieben wird.

        * **Leitweg-ID:** Die digitale Postanschrift für Rechnungen an Behörden (erscheint anstelle einer normalen E-Mail-Adresse).

        * **WORM-Speicher:** (Write Once, Read Many) Ein Speichersystem, bei dem Dateien nach dem Schreiben nicht mehr verändert oder gelöscht werden können (wichtig für GoBD-Konformität).

        * **DATEV EXTF:** Ein standardisiertes ASCII-CSV-Format zum verlustfreien Import von Buchungsstapeln in die Kanzlei-Software des Steuerberaters.

    

    ## 5. FAQ – Häufige Fragen

    
    
        **Wie kann ich mein eigenes Logo auf die Rechnung drucken?**
        Das Programm nutzt eine PDF-Vorlage als Hintergrund. Erstellen Sie z. B. in Word Ihr Briefpapier mit Logo, speichern Sie es als PDF und hinterlegen Sie es im Reiter *Konfig.* unter „Briefbogen hinterlegen“.

    
    
    
        **Wie setze ich die Rechnungsnummern für das neue Jahr zurück?**
        Wechseln Sie im Reiter *Konfig.* einfach das „Aktuelle Rechnungsjahr“ und korrigieren Sie darunter die „Letzte Rechnungs-Nr.“ einmalig händisch auf den Startwert (z.B. RE-27-000).

    
    
    
        **Wie erstelle ich eine XRechnung für Behörden?**
        Tragen Sie bei der Rechnungserstellung in das Feld „E-Mail / Leitweg-ID“ die Leitweg-ID ein und setzen Sie das „Endpoint-Schema“ auf `0204`.

    
    
    
        **Das Programm startet nicht mehr oder ist gesperrt. Was tun?**
        Wenn eine Firma gesperrt ist (Lock), wurde das Programm evtl. unsanft beendet oder ein anderer Arbeitsplatz greift darauf zu. Beim Versuch, den Reiter zu wechseln, erscheint ein Hinweisfenster, in dem Sie den „Lock entfernen“ können.

    

    
    # TEIL 2: Anwenderhandbuch

    ## 6. Die Benutzeroberfläche (Tabs) im Detail

    *Tipp: Sie können zwischen allen Reitern schnell über die Tastatur wechseln. Halten Sie dazu die **Alt-Taste** gedrückt und tippen Sie den in eckigen Klammern markierten Buchstaben der Tab-Überschrift (z. B. [E]).*

    
    ### 📝 [E]RSTELLEN (Ausgangsrechnungen schreiben)

    Hier erfassen und generieren Sie Ihre eigenen Ausgangsrechnungen an Kunden inkl. automatischer Steuerberechnung.

    
    ### 📥 ER[F]ASSEN (Eingangsrechnungen prüfen)

    Haltautomatisierte Prüfung, Erfassung und Archivierung von Rechnungen Ihrer Lieferanten (Prüfung nach EN 16931 / § 14 UStG).

    
    ### 📊 [A]USGANG (Ausgangsjournal)

    Auswertung der geschriebenen Rechnungen als PDF, CSV oder DATEV-Export.

    
    ### 📊 E[I]NGANG (Eingangsjournal & Verwaltung)

    Durchsuchen, Verwalten und Auswerten der erfassten Eingangsrechnungen (Storno-Funktion inklusive).

    
    ### ⚙️ [K]onfig. (Einstellungen & Stammdaten)

    Zentrale Konfiguration Ihrer Firmen, Nummernkreise, DATEV-Konten und Stammdaten mit hilfreichen Tooltips.

    
    ### ℹ️ Info (Hilfe & Statistik)

    Dokumentation, Version, Statistiken und Update-Suche.

    ## 7. Schritt-für-Schritt: ZUGFeRD-Rechnung erstellen

    Der Reiter **📝 [E]RSTELLEN** führt Sie komfortabel durch die Erfassung einer gesetzlich konformen E-Rechnung.

    ### Schritt 1: Kopf- und Kundendaten (Eingabefelder)

    Im linken Bereich füllen Sie die Stammdaten der Rechnung aus. Das Programm vergibt Datum und Rechnungsnummer automatisch (diese lassen sich aber überschreiben).

    
        * **Pflichtfelder:** *Rechnungs-Nr.*, *Rechnungsdatum*, *Fälligkeit*, *Kunde Name*, *Straße*, *PLZ Ort* und die *E-Mail / Leitweg-ID*. Ohne diese Kerninformationen ist das Erzeugen einer gültigen strukturierten e-Rechnung unzulässig.

        * **Optionale Felder:** *Kunden-Nr.*, *Unser Zeichen* (Ihr Aktenzeichen), *Ihr Zeichen* (z. B. Bestellnummer des Kunden) sowie der *Leistungszeitraum (Kopf)*.

        * **Datenspeicherung (Kunden):** Wenn Sie die Checkbox *„Kunde speichern/updaten“* aktivieren, wird der Kunde beim Klick auf „Erstellen“ automatisch in Ihrer CSV-Datenbank gespeichert. Zukünftig können Sie den Kunden dann über das 🔍-Lupensymbol schnell suchen und laden.

    

    ### Schritt 2: Texte & Vorlagen bearbeiten

    Klicken Sie auf den Button **„📝 Texte & Vorlagen bearbeiten (Alt+T)“**. Hier können Sie wiederkehrende Textbausteine definieren:

    
        * *Header* (Über der Adresse), *Einleitung*, *Rechnungsvermerk*, *Zahlungsbedingungen*, *Vor Gruß* und *Gruß*.

        * **Vorlagen speichern:** Wenn Sie z. B. spezielle Texte für eine „Vorschussrechnung“ benötigen, tragen Sie die Texte ein und klicken unten auf **„➕ Als neue Vorlage...“**. 

        * Zurück im Hauptfenster können Sie über das Dropdown-Menü **„Textvorlage“** jederzeit zwischen Ihren gespeicherten Szenarien wechseln.

    

    ### Schritt 3: Positionen erfassen

    Klicken Sie rechts auf **„+ Position hinzufügen“**.

    
        * **Pflichtfeld:** *Bezeichnung*.

        * Menge, Einzelpreis und Steuersatz (19%, 7% oder 0%) sind vorausgefüllt, können aber jederzeit angepasst werden. Über das Dropdown-Feld bei der Bezeichnung können Sie zudem zuvor in den Einstellungen importierte oder gespeicherte Produkte abrufen.

    

    ### Schritt 4: Vorschau & Generierung

    Unter der Liste der Positionen sehen Sie die berechneten Gesamtbeträge. Ihnen stehen nun verschiedene Aktionen zur Verfügung:

    
        * **Testrechnung:** Erzeugt eine reine *Vorschau*. Es wird keine Rechnungsnummer blockiert/vergeben und kein Journaleintrag geschrieben. Ideal zur optischen Endkontrolle.

        * **Zugpferdrechnung erstellen (Alt+P):** Die empfohlene Standard-Funktion für Geschäftskunden. Generiert ein sichtbares PDF mit integrierten XML-Daten, verbucht den Vorgang im Journal und zählt die Rechnungsnummer eins hoch.

        * **XRechnung & Begleit-PDF:** Primär für Behörden (Leitweg-ID im Feld "E-Mail" erforderlich). Erzeugt die reine XML-Datei für das Behördenportal und ein Begleit-PDF für Ihre eigenen Akten.

    

    ## 8. Auswertungen (Tab AUSGANG) & Einstellungen (Tab Konfig.)

    
    ### Die Auswertungsmöglichkeiten (Tab 📊 [A]USGANG)

    Hier werten Sie alle im aktuellen Jahr geschriebenen Rechnungen aus. Wählen Sie Monat und Jahr, um folgende Berichte zu generieren:

    
        * **📄 Journal als PDF:** Erstellt eine saubere, druckbare Übersichtstabelle aller Ausgangsrechnungen inklusive Gesamtnettoumsatz und detailliert aufgeschlüsselter Steuerbeträge.

        * **📊 Journal als CSV:** Exportiert die Rechnungsdaten tabellarisch für die problemlose Weiterverarbeitung in Microsoft Excel oder ähnlichen Werkzeugen.

        * **📈 DATEV-Export:** Generiert eine formatierte ASCII-Datei für die Kanzleisoftware Ihres Steuerberaters. Rechnungen mit verschiedenen Steuersätzen werden vollautomatisch centgenau zerlegt (Steuer-Splitting) und mit den korrekten Soll/Haben-Kennzeichen verbucht.

        * **🛡️ Audit-Log PDF:** Erstellt ein formatierbares PDF-Revisionsprotokoll aller vorgenommenen Änderungen und Löschungen (inkl. erzwungener Begründungen) für das ausgewählte Jahr.

    

    ### Einstellungsmöglichkeiten & Gefahrenhinweise (Tab ⚙️ [K]onfig.)

    Im Reiter Konfiguration verwalten Sie Ihre Firmen, Nummernkreise, Briefbögen und DATEV-Sachkonten. Die Oberfläche ist in übersichtliche „Karten“ unterteilt. **Bitte beachten Sie folgende Besonderheiten und Gefahren:**

    
    
        **⚠️ VORSICHT BEI DATENVERLUST-RISIKEN:**

        
            * **🧹 Daten leeren:** Dieser Button im Bereich Profilverwaltung löscht *unwiderruflich alle geschriebenen Rechnungen, Rechnungs-PDFs und Journale* der aktiven Firma! Nutzen Sie diese Funktion nur, wenn Sie eine Testfirma zurücksetzen möchten. Stammdaten (Kunden/Produkte/Vorlagen) bleiben glücklicherweise erhalten.

            * **🗑 Profil löschen:** Entfernt die komplette Firma restlos aus der Konfiguration.

            * **Rechnungsnummer korrigieren:** Ein manueller Eingriff in den Zählerstand (z. B. ein Zurücksetzen der Nummer) kann dazu führen, dass bei der nächsten Rechnungserstellung alte Rechnungen ungewollt überschrieben werden, wenn die Nummer im Ordner bereits vergeben wurde.

        
    
    
    **Wichtige ungefährliche Konfigurationen:**

    
        * **DATEV-Konten:** Weisen Sie dem Programm mit, welche Sachkonten (SKR03 / SKR04) für den Buchhaltungs-Export genutzt werden sollen.

        * **Briefbogen hinterlegen:** Hier wählen Sie Ihr PDF mit Firmenlogo, das künftig im Hintergrund auf alle ausgehenden Rechnungen gedruckt wird.

        * **Firmendaten:** Tragen Sie Ihre IBAN, Bankdaten und Kontaktdaten ein und aktivieren Sie bei Bedarf den Andruck eines *Girocodes* (QR-Code zum automatischen Bezahlen per Banking-App).

    

    ## 9. Rechnungsformate (ZUGFeRD & XRechnung)

    Das Programm unterstützt:

    
        * **Testrechnung:** Erstellt eine reine Vorschau-PDF ohne Rechnungsnummer und ohne Journaleintrag im temporären Verzeichnis. Ideal, um das Aussehen vorab zu prüfen. Das Programm bleibt zur weiteren Bearbeitung geöffnet.

        * **ZUGFeRD:** Erzeugt eine Hybrid-PDF, die eine XML-Datei beinhaltet.

        * **XRechnung:** Erzeugt eine reine XML-Datei für das Behörden-Portal und als Beilage ein gesondertes, lesbares Begleit-PDF.

        * **Papierrechnung:** Erzeugt eine rein visuelle PDF ohne eingebettete XML-Daten (nur als Übergangslösung).

    

    ## 10. Eingangsrechnungen erfassen und auswerten

    Legen Sie neue Eingangsrechnungen Ihrer Lieferanten im Netzwerk in den Ordner `reneu`. Klicken Sie im Programm auf "Nächste Eingangsrechnung prüfen". Das Programm prüft diese automatisiert. Fehlerhafte Belege werden mit einer genauen Fehlermeldung abgewiesen. Nach der erfolgreichen Erfassung wird der Beleg im Archiv (`rchn`) gespeichert und automatisch fortlaufend im Eingangs-Journal (`eausw`) vermerkt.

    ## 11. Jahreswechsel

    Ändern Sie in den "Einstellungen" einfach das "Aktuelle Rechnungsjahr" im Dropdown oder legen Sie ein neues Firmenprofil für das neue Jahr an. Eine Anpassung der letzten Rechnungsnummer (z. B. auf 000 für den Neubeginn) kann dort ebenfalls vorgenommen werden.

    
    # TEIL 3: Administration & IT

    ## 12. Installation, Ordnerstruktur & File-Locking

    Das Programm trennt strikt zwischen Programmdateien (Installation), lokalen Arbeitsplatz-Einstellungen (AppData) und Firmendaten (Daten-Grundpfad auf dem Netzlaufwerk). In den Firmendaten legt das Programm automatisch alle relevanten Ordner für Journale (`aausw`, `eausw`) und Archive an.

    
    ### Integrierte Profil-Backups & Datensicherheit

    In der Konfigurationsoberfläche (Reiter **Konfig.**) können Sie per Knopfdruck ein ZIP-Archiv der aktiven Firma anlegen lassen und wiederherstellen. Die Wiederherstellung kann in die geöffnete oder in eine neue Firma erfolgen.

    
    
        **⚠️ WICHTIGER HINWEIS ZUR DATENSICHERHEIT:**

        Diese integrierte Backup-Funktion stellt lediglich eine *zusätzliche Sicherungsmöglichkeit* für den einzelnen Arbeitsplatz dar. Sie entbindet Sie keinesfalls von der Pflicht, die Programm- und Netzwerkdaten (Ihren kompletten Daten-Grundpfad) regelmäßig durch externe und professionelle System-Backups zu sichern!
    
    
    
        **🛡️ Admin-Hinweise zum Netzwerkbetrieb & File-Locking:**

        - Das Programm nutzt Sperrdateien (`erechnung.lock` und `erfassung.lock`) im Firmenverzeichnis, um gleichzeitige Schreibkonflikte im Netzwerk zu verhindern.

        - Sollte ein Arbeitsplatz abstürzen, erkennt das System verwaiste Locks und erlaubt nach einer Sicherheitswarnung das manuelle Entfernen der Sperre ("Lock entfernen").

        - Lokale Konfigurationen landen sicher in `%LOCALAPPDATA%\SokoIur_eRechnung`, was UAC-Berechtigungskonflikte ausschließt.
    

    ## 13. Mandanten & Datenbanken (Firmendaten)

    Sie können im Reiter "Konfig." beliebig viele verschiedene Firmenprofile verwalten. Das Programm synchronisiert neue Firmen automatisch über den geteilten Daten-Grundpfad an alle Arbeitsplätze im Netzwerk.

    ## 14. DATEV-Export & Buchhaltung

    SokoIur eRechnung bietet eine integrierte Exportfunktion für die Finanzbuchhaltung (Stapelverarbeitung im ASCII-CSV / EXTF-Format).

    
    
        **WICHTIGER HINWEIS (BETA-FUNKTION):**

        Die DATEV-Exportfunktionen wurden bisher nicht abschließend in einer produktiven DATEV-Umgebung getestet. Bitte übergeben Sie Daten zunächst probeweise mit Testdaten an Ihren Steuerberater, um den fehlerfreien Import (Feldzuordnungen, 7 Pflichtspalten, Längenbeschränkungen) sicherzustellen.
    

    ### Konfiguration (SKR03 / SKR04) & Automatisches Steuer-Splitting

    Im Reiter **⚙️ Konfig.** können Sie über **„📈 DATEV-Konten“** Standardkonten für SKR03/SKR04 laden. Rechnungen mit unterschiedlichen Steuersätzen werden beim DATEV-Export automatisch centgenau zerlegt, anteilig zurückgerechnet und mit intelligent vergebenen Soll/Haben-Kennzeichen (S/H) versehen.

    ## 15. Import-Formate (CSV)

    Alle CSV-Dateien müssen semikolongetrennt (`;`) und im Format UTF-8 vorliegen (bei ANSI-Dateien aus Excel erfolgt eine automatische Reparatur).

    
    ### Kundendaten Importieren

    Die Import-Datei muss folgende Kopfzeile exakt aufweisen (ohne Zeilenumbruch):

    `Name;Strasse;PLZ_Ort;Land;KundeNr;Aktenzeichen;KundeAktenzeichen;Endpoint;EndpointScheme`
    
    ### Produktdaten Importieren

    Die Import-Datei muss folgende Kopfzeile exakt aufweisen:

    `Bezeichnung;Menge;Einheit;EinzelpreisNetto;Steuersatz`
    
    ### Rechnungsentwürfe via CLI (rechnung.csv)

    Die `rechnung.csv` für den externen CLI-Aufruf benötigt feste Spalten. Die Kopfdaten werden in jeder Zeile wiederholt, lediglich die Positionsdaten ändern sich je Zeile.

    ## 16. Programmaufruf & Kommandozeile (CLI)

    
    ### Tastenkürzel-Übersicht (GUI):

    
        * `Alt + E` -> Zum Reiter ERSTELLEN wechseln

        * `Alt + F` -> Zum Reiter ERFASSEN wechseln

        * `Alt + A` -> Zum Reiter AUSGANG wechseln

        * `Alt + I` -> Zum Reiter EINGANG wechseln

        * `Alt + K` -> Zum Reiter Konfig. wechseln

        * `Alt + L` -> Letzte Rechnungs-CSV laden

        * `Alt + T` -> Texte bearbeiten (Header, Einleitung, Gruß)

        * `Alt + P` -> ZUGFeRD-Rechnung generieren, öffnen & beenden

    

    ### Die Kommandozeilenparameter (CLI Cheat-Sheet)

    
        
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
        
    

    ## 17. Revisionssicheres Archiv & GoBD-Audit-Log

    
    ### Das GoBD Audit-Log (Verfahrensdokumentation)

    Um den strengen Anforderungen der GoBD an Nachvollziehbarkeit und Unveränderbarkeit (vgl. Rz. 58 und Rz. 107-111) zu genügen, führt das Programm automatisch getrennte Audit-Logs für den Ausgangs- und Eingangsbereich. Diese finden Sie im Netzwerkordner unter `audit/<Jahr>`.

    
    Wann werden welche Einträge protokolliert?
    Das System schreibt in folgenden Situationen automatisch einen unveränderlichen Eintrag in das Audit-Log:

    
        * **Neuerstellung (Eingang & Ausgang):** Sobald eine Ausgangsrechnung generiert (Aktion: *Erstellt*) oder eine Eingangsrechnung erfasst wird. Das Log verzeichnet dabei präzise und überschneidungsfrei, auf welchem Weg die Rechnung erzeugt wurde: durch einen normalen Programmstart (Modus: `GUI`), durch manuelle Nachbearbeitung nach Aufruf durch ein Fremdprogramm (Modus: `CLI (--edit)`) oder vollautomatisiert im Hintergrund durch die Kommandozeile (Modus: `CLI (--auto)`).
* **Änderung / Überschreiben (Ausgang):** Wird eine bereits vergebene Rechnungsnummer im Reiter "ERSTELLEN" erneut aufgerufen und überschrieben (Aktion: *Geändert*), protokolliert das System diesen Vorgang zum Schutz der fortlaufenden Nummernkreise.

        * **Löschung / Storno (Eingang):** Wird ein bereits verbuchter Beleg vom Nutzer nachträglich wieder aus dem Eingangsjournal gelöscht bzw. storniert (Aktion: *Gelöscht*).

    

    Konfiguration und Export
    
        * **Konfigurierbarer Begründungszwang:** In den Einstellungen (Reiter Konfig.) können Sie die Option "GoBD: Begründungszwang bei Änderung/Löschung" aktivieren. Das Programm zwingt den Anwender dann bei jeder Datenänderung (Überschreiben) oder Löschung zur Eingabe eines Revisionsgrundes. Dieser Grund wird unveränderlich mit dem Log-Eintrag verknüpft. Dies dient bei Betriebsprüfungen als lückenloser Nachweis über die Historie.

        * **Exportfunktion:** In den Reitern für Ausgang und Eingang lässt sich das zugehörige jahresbasierte Audit-Log jederzeit komfortabel über den Button "🛡️ Audit-Log PDF" als übersichtliche PDF-Tabelle für den Prüfer generieren.

    

    Zur Erfüllung der GoBD wird *zusätzlich* empfohlen, die generierten Verzeichnisse (`rchn` für den Eingang und `are` für den Ausgang) automatisch in einen **WORM-Onlinespeicher** (Write Once, Read Many; z.B. via Nextcloud) zu synchronisieren, der eine nachträgliche Veränderung durch Nutzer oder Ransomware technisch ausschließt.

    ## 18. GitHub & Updates

    Quellcode und Releases sind im offiziellen GitHub-Repository unter [https://github.com/JSoko/SokoIur-eRechnung-Zugferd](https://github.com/JSoko/SokoIur-eRechnung-Zugferd) einsehbar. Über die integrierte Update-Funktion wird die neue Version direkt in Ihr Netzlaufwerk geladen, um die Verteilung an alle Arbeitsplätze zu erleichtern.

    ## 19. Schlagwortverzeichnis (Index)

    
        **B**

        [Briefbogen hinterlegen](#kap1)

        [Buchhaltung](#kap14)
        **D**

        [Daten-Speicherort](#kap1)

        [Daten-Speicherort (Admin)](#kap12)

        [Datenschutz](#kap2)

        [DATEV-Export](#kap14)
        **E**

        [Eingangsrechnungen prüfen](#kap10)

        [E-Rechnungspflicht](#kap3)
        **G**

        [Girocode (QR-Code)](#kap3)
        **I**

        [Import (Kunden & Produkte)](#kap15)
        **J**

        [Jahreswechsel](#kap11)

        [Journale (Ausgang / Eingang)](#kap6)
        **L**

        [Leitweg-ID (Use Case)](#kap3)

        [Leitweg-ID (Glossar)](#kap4)
        **M**

        [Mandanten & Firmenprofile](#kap13)
        **N**

        [Netzwerkbetrieb & File-Locking](#kap12)
        **S**

        [Standardtexte](#kap7)

        [Stornorechnung](#kap3)
        **T**

        [Testrechnung](#kap7)
        **X**

        [XRechnung (Format)](#kap9)

        [XRechnung (Glossar)](#kap4)
        **Z**

        [ZUGFeRD (Format)](#kap9)

        [ZUGFeRD (Glossar)](#kap4)
    
    ---

    
        © Joachim Sokolowski, Offenbacher Str. 99, 63263 Neu-Isenburg