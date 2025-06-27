# main.py
import os
from dotenv import load_dotenv
from src.config import PHONE_MESSAGE_FILE, LAPTOP_MAIL_FILE
from src.device_manager import DeviceManager
from src.actions.communication import create_sample_files_if_missing

# Lade Umgebungsvariablen aus der .env Datei
load_dotenv()

def main():
    """
    Hauptfunktion zum Starten der Anwendung.
    """
    print("=====================================")
    print("  ETS2 Immersion Hub wird gestartet  ")
    print("=====================================")

    # Erstellt Beispiel-Nachrichten/Mails, falls die Dateien nicht existieren
    create_sample_files_if_missing()

    # Initialisiert und startet den Device Manager, der alles weitere steuert
    manager = DeviceManager()
    manager.run()

    print("=====================================")
    print("   ETS2 Immersion Hub wurde beendet   ")
    print("=====================================")


if __name__ == "__main__":
    # Stelle sicher, dass der Gemini API Key gesetzt ist
    if not os.getenv("GEMINI_API_KEY"):
        print("\nFEHLER: Der GEMINI_API_KEY wurde nicht in der .env-Datei gefunden.")
        print("Bitte erstelle eine .env-Datei im Hauptverzeichnis mit dem Inhalt:")
        print('GEMINI_API_KEY="DEIN_API_SCHLUESSEL"\n')
    else:
        main()
