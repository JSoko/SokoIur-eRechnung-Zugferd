# Changelog – SokoIur eRechnung
**Aktuelle Version: 2.000149**

## Version 2.000150
### ✨ Kommandozeile (CLI) & Fremdprogramm-Integration
*   **Strikte Profil-Validierung:** Sicherer Abbruch mit Fehlermeldung, falls per `--auto` oder `--edit` ein unbekanntes `--profil` übergeben wird.
*   **Sicherheitswarnung bei Abbruch:** Spezifischer Warnhinweis beim Schließen im `--edit`-Modus, um verwaiste Rechnungsnummern im aufrufenden Fremdsystem zu vermeiden.
*   **Saubere Textfelder:** Temporäre CLI-Rechnungen importieren keine alten Anmerkungen (Zusatztexte) der Firma mehr.

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
