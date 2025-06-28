# src/startTelemetry.py
import subprocess
import sys
from pathlib import Path
from src.config import TELEMETRY_SERVER_EXE

def start_telemetry_server():
    """
    Startet den ETS2 Telemetry Server, falls die Executable vorhanden ist.
    Überspringt den Start, wenn die Datei nicht gefunden wird.
    """
    try:
        # Prüfen ob ein gültiger Pfad konfiguriert ist
        if str(TELEMETRY_SERVER_EXE) in [".", "./"]:
            print("Telemetry Server Pfad nicht konfiguriert (Standard: '.')")
            print("Bitte TELEMETRY_SERVER_EXE in config.py anpassen")
            print("Überspringe Telemetry Server Start...")
            return False
            
        # Prüfen ob der Pfad existiert
        if not TELEMETRY_SERVER_EXE.exists():
            print(f"Telemetry Server nicht gefunden: {TELEMETRY_SERVER_EXE}")
            print("Überspringe Telemetry Server Start...")
            return False
            
        # Prüfen ob es eine Datei ist (nicht Verzeichnis)
        if not TELEMETRY_SERVER_EXE.is_file():
            print(f"Pfad ist keine Datei: {TELEMETRY_SERVER_EXE}")
            print("Überspringe Telemetry Server Start...")
            return False
            
        # Prüfen ob es eine .exe Datei ist
        if not str(TELEMETRY_SERVER_EXE).lower().endswith('.exe'):
            print(f"Datei ist keine .exe: {TELEMETRY_SERVER_EXE}")
            print("Überspringe Telemetry Server Start...")
            return False
            
        # Telemetry Server starten
        print(f"Starte Telemetry Server: {TELEMETRY_SERVER_EXE}")
        
        # Subprocess mit detach, damit das Hauptskript nicht blockiert wird
        subprocess.Popen(
            str(TELEMETRY_SERVER_EXE),
            cwd=TELEMETRY_SERVER_EXE.parent,  # Working directory auf das Verzeichnis der exe setzen
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print("Telemetry Server erfolgreich gestartet!")
        return True
        
    except Exception as e:
        print(f"Fehler beim Starten des Telemetry Servers: {e}")
        print("Überspringe Telemetry Server Start...")
        return False

if __name__ == "__main__":
    # Für Testzwecke
    start_telemetry_server()
