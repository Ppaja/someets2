# _temp_extract_raw_city_names.py
import sys
import re
from pathlib import Path

# Füge das 'src'-Verzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from config import PROFILE_PATH
    from game_integration.ets2_savegame_parser import SavegameParser
except ImportError as e:
    print(f"FEHLER: Konnte notwendige Module nicht importieren: {e}")
    input("Drücke Enter zum Beenden...")
    sys.exit(1)


def extract_all_raw_city_names():
    """
    Liest das aktuellste Savegame und extrahiert eine einzigartige Liste
    aller 'rohen' Städtenamen aus den Frachtmarkt-Aufträgen.
    """
    print("======================================================")
    print("  Extrahiere rohe Städtenamen aus dem Savegame...  ")
    print("======================================================")

    try:
        # Wir nutzen den existierenden Parser
        parser = SavegameParser(profile_path=PROFILE_PATH)
    except Exception as e:
        print(f"\nFEHLER bei der Initialisierung des Parsers: {e}")
        return

    # Dies ist eine benutzerdefinierte Parser-Funktion, die wir an den
    # Entschlüsselungs-Mechanismus des SavegameParser übergeben.
    def _internal_parser(content: str):
        raw_city_names = set()

        # 1. Alle Job-Angebote in eine Map laden für schnellen Zugriff
        job_data_map = {}
        job_pattern = re.compile(r'job_offer_data\s*:\s*([^\s{]+)\s*\{([^}]*)\}', re.DOTALL)
        for match in job_pattern.finditer(content):
            job_id, job_content = match.groups()
            if 'cargo: null' in job_content or 'target: ""' in job_content:
                continue
            
            target_match = re.search(r'target:\s*([^\s\n]+)', job_content)
            if target_match:
                job_data_map[job_id.strip()] = {'target': target_match.group(1)}

        # 2. Alle Firmen durchgehen und die Start- und Zielstädte extrahieren
        company_pattern = re.compile(r'company\s*:\s*(company\.volatile\.[^ ]+)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', re.DOTALL)
        for company_match in company_pattern.finditer(content):
            company_id, company_content = company_match.groups()
            
            # Nutze die interne (private) Methode des Parsers, um den Start-Stadtnamen zu bekommen
            start_city_info = parser._parse_company_id(company_id)
            raw_city_names.add(start_city_info['city'])

            offer_id_pattern = re.compile(r'job_offer\[\d+\]:\s*([^\s\n]+)')
            for offer_id_match in offer_id_pattern.finditer(company_content):
                offer_id = offer_id_match.group(1)
                if offer_id in job_data_map:
                    job_data = job_data_map[offer_id]
                    # Nutze die interne Methode für den Ziel-Stadtnamen
                    target_info = parser._parse_target_id(job_data.get('target', ''))
                    raw_city_names.add(target_info['city'])
        
        return sorted(list(raw_city_names))

    # Führe die Entschlüsselung mit unserer eigenen Parser-Funktion aus
    all_raw_names = parser._execute_with_decryption(_internal_parser)

    if not all_raw_names:
        print("\nKonnte keine Städtenamen extrahieren. Ist das Savegame gültig?")
        return

    print("\nFolgende rohe Städtenamen wurden in den Aufträgen gefunden:\n")
    for name in all_raw_names:
        print(f"- {name}")
    
    print("\n======================================================")
    print("Diese Liste kannst du nun mit deiner 'city_database.json' abgleichen.")


if __name__ == "__main__":
    extract_all_raw_city_names()
    input("\nDrücke Enter zum Beenden...")