"""
audit.py
--------
Funktionen für das revisionssichere GoBD-Audit-Log.
"""
import os
import csv
import socket
from datetime import datetime

def write_audit_log(firm_dir, bereich, aktion, beleg_nr, bemerkung="", cli_mode="GUI"):
    if not firm_dir or not os.path.exists(firm_dir): return
    
    jahr = str(datetime.now().year)
    audit_dir = os.path.join(firm_dir, "audit", jahr)
    os.makedirs(audit_dir, exist_ok=True)
    
    pfad = os.path.join(audit_dir, f"audit_{bereich}_{jahr}.csv")
    file_exists = os.path.exists(pfad)
    
    computername = os.environ.get('COMPUTERNAME', socket.gethostname())
    zeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    fieldnames = ["Zeitstempel", "Arbeitsplatz", "Modus", "Aktion", "BelegNr", "Bemerkung"]
    
    try:
        with open(pfad, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "Zeitstempel": zeit,
                "Arbeitsplatz": computername,
                "Modus": cli_mode,
                "Aktion": aktion,
                "BelegNr": beleg_nr,
                "Bemerkung": bemerkung
            })
    except Exception as e:
        print(f"Fehler beim Schreiben des Audit-Logs: {e}")