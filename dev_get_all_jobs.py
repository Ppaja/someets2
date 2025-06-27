# get_all_jobs.py
import sys
from pathlib import Path
from datetime import datetime

# Füge das 'src'-Verzeichnis zum Python-Pfad hinzu, damit wir die Module importieren können
# Dies ist notwendig, da wir das Skript aus dem Hauptverzeichnis ausführen
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from config import PROFILE_PATH
    from game_integration.ets2_savegame_parser import SavegameParser
except ImportError as e:
    print(f"FEHLER: Konnte notwendige Module nicht importieren: {e}")
    print("Stelle sicher, dass du dieses Skript aus dem Hauptverzeichnis deines Projekts ausführst.")
    input("Drücke Enter zum Beenden...")
    sys.exit(1)


def export_all_jobs_to_txt():
    """
    Liest das aktuellste Savegame, extrahiert alle Frachtmarkt-Aufträge
    und speichert sie in einer datierten TXT-Datei.
    """
    print("=======================================")
    print("  ETS2 Auftrags-Export wird gestartet  ")
    print("=======================================")
    print(f"\nLese Profil von: {PROFILE_PATH}")

    try:
        parser = SavegameParser(profile_path=PROFILE_PATH)
        print("Savegame-Parser erfolgreich initialisiert.")
    except FileNotFoundError as e:
        print(f"\nFEHLER: Das Profil- oder Speicherverzeichnis wurde nicht gefunden: {e}")
        print("Bitte überprüfe den 'PROFILE_PATH' in der 'src/config.py' Datei.")
        return
    except Exception as e:
        print(f"\nEin unerwarteter Fehler bei der Initialisierung ist aufgetreten: {e}")
        return

    print("\nSuche nach allen verfügbaren Frachtmarkt-Aufträgen...")
    # Wir rufen get_freight_market_jobs ohne Argumente auf, um alle Jobs zu erhalten
    jobs = parser.get_freight_market_jobs()

    if not jobs:
        print("\nKeine Aufträge gefunden oder Fehler beim Parsen des Savegames.")
        print("Stelle sicher, dass du im Spiel bist und Aufträge im Frachtmarkt verfügbar sind.")
        return

    # Sortiere die Jobs, z.B. nach Stadt und dann nach Distanz
    jobs.sort(key=lambda j: (j['start_city'], -j['distance_km']))
    
    # Erstelle einen eindeutigen Dateinamen mit Zeitstempel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"alle_auftraege_{timestamp}.txt"
    output_path = project_root / output_filename

    print(f"\n{len(jobs)} Aufträge gefunden. Schreibe sie in die Datei: {output_filename}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Alle verfügbaren Frachtmarkt-Aufträge\n")
            f.write(f"Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Profil: {PROFILE_PATH}\n")
            f.write("="*80 + "\n\n")

            current_city = None
            for i, job in enumerate(jobs):
                # Füge eine Überschrift für jede neue Stadt hinzu
                if job['start_city'] != current_city:
                    current_city = job['start_city']
                    f.write(f"\n--- Aufträge ab {current_city.upper()} ---\n\n")

                f.write(f"Auftrag #{i+1}\n")
                f.write(f"  Von:    {job['start_company']} in {job['start_city']}\n")
                f.write(f"  Nach:   {job['target_company']} in {job['target_city']}\n")
                f.write(f"  Fracht: {job['cargo']}\n")
                f.write(f"  Distanz: {job['distance_km']} km\n")
                f.write("-" * 40 + "\n")

        print("\nErfolgreich! Die Datei wurde erstellt.")
        print("=======================================")

    except Exception as e:
        print(f"\nFEHLER beim Schreiben der Datei: {e}")


if __name__ == "__main__":
    export_all_jobs_to_txt()
    input("\nDrücke Enter zum Beenden...")