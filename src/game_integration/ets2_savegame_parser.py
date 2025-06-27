# src/game_integration/ets2_savegame_parser.py
import subprocess
import re
from pathlib import Path
import os
from typing import List, Dict, Optional, Any

from src.config import PROFILE_PATH, SII_DECRYPT_EXE, OFFENCE_TYPE_MAP
from src.utils.translation import (
    translate_name, COMPANY_MAP, CARGO_MAP,
    get_pretty_city_name, get_raw_city_names
)

class SavegameParser:
    def __init__(self, profile_path: Path = PROFILE_PATH):
        self.profile_dir = profile_path
        self.save_dir = self.profile_dir / "save"
        if not self.save_dir.exists():
            raise FileNotFoundError(f"Das Speicherverzeichnis wurde nicht gefunden: {self.save_dir}")
        self.temp_decrypted_file = "decrypted_save.sii"

    def _find_latest_save(self) -> Optional[Path]:
        all_saves = list(self.save_dir.glob("**/game.sii"))
        return max(all_saves, key=lambda p: p.stat().st_mtime) if all_saves else None

    def _decrypt_save(self, input_file: Path) -> Optional[str]:
        if not SII_DECRYPT_EXE.exists():
            print(f"✗ FEHLER: '{SII_DECRYPT_EXE}' nicht gefunden.")
            return None
        try:
            subprocess.run(
                [str(SII_DECRYPT_EXE), str(input_file), self.temp_decrypted_file],
                capture_output=True, text=True, check=True, encoding='utf-8'
            )
            return self.temp_decrypted_file
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"✗ FEHLER bei der Entschlüsselung: {e}")
            return None

    def _cleanup(self):
        if os.path.exists(self.temp_decrypted_file):
            try:
                os.remove(self.temp_decrypted_file)
            except OSError as e:
                print(f"✗ Fehler beim Löschen der temporären Datei: {e}")

    def _parse_company_id(self, company_id: str) -> Dict[str, str]:
        parts = company_id.strip().split('.')
        return {'name': parts[-2], 'city': parts[-1]} if len(parts) >= 2 else {'name': company_id, 'city': 'Unbekannt'}

    def _parse_target_id(self, target_id: str) -> Dict[str, str]:
        clean_id = target_id.strip().replace('"', '')
        parts = clean_id.split('.')
        return {'name': parts[0], 'city': parts[1]} if len(parts) >= 2 else {'name': clean_id, 'city': 'Unbekannt'}

    def _format_game_time(self, minutes: int) -> str:
        if minutes < 0: return "Unbekannt"
        day, rem = divmod(minutes, 1440)
        hour, minute = divmod(rem, 60)
        return f"Tag {day + 1}, {hour:02d}:{minute:02d}"

    def _execute_with_decryption(self, parser_func, *args, **kwargs):
        latest_save = self._find_latest_save()
        if not latest_save:
            print("✗ Kein Savegame gefunden.")
            return None
        
        decrypted_file_path = self._decrypt_save(latest_save)
        if not decrypted_file_path:
            return None

        try:
            with open(decrypted_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return parser_func(content, *args, **kwargs)
        except Exception as e:
            print(f"Ein unerwarteter Fehler beim Parsen ist aufgetreten: {e}")
            return None
        finally:
            self._cleanup()

    def get_available_cities(self) -> Optional[List[str]]:
        """Gibt eine Liste aller rohen Städtenamen zurück, die Jobs haben."""
        def _parser(content):
            cities = set()
            company_pattern = re.compile(r'company\s*:\s*company\.volatile\.([^ ]+)\s*\{')
            for match in company_pattern.finditer(content):
                company_id = match.group(1)
                city = company_id.split('.')[-1]
                cities.add(city)
            return sorted(list(cities))
        return self._execute_with_decryption(_parser)

    def get_freight_market_jobs(self, start_city: Optional[str] = None, current_game_time_minutes: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Sucht nach Frachtmarkt-Aufträgen.
        Wenn 'start_city' (ein schöner Name) angegeben ist, werden alle zugehörigen rohen Städte durchsucht.
        """
        def _parser(content, raw_start_cities_filter: Optional[List[str]] = None):
            return self._parse_job_content(content, current_game_time_minutes, raw_start_cities_filter)

        # Wandle den schönen Namen in eine Liste roher Namen um
        raw_cities_to_search = get_raw_city_names(start_city) if start_city else None
        
        # Führe die Pars-Funktion mit dem Filter aus
        all_jobs, _ = self._execute_with_decryption(_parser, raw_start_cities_filter=raw_cities_to_search) or ([], set())
        return all_jobs

    def get_last_delivery_log_details(self) -> Optional[Dict[str, Any]]:
        def _parser(content):
            log_entries = re.findall(r'delivery_log_entry\s*:\s*[^\s{]+\s*\{([^}]*)\}', content, re.DOTALL)
            if not log_entries: return None
            params = re.findall(r'params\[\d+\]:\s*"?([^"\n]+)"?', log_entries[-1])
            if len(params) < 4: return None
            
            source_parts = params[1].split('.')
            target_parts = params[2].split('.')
            
            return {
                "cargo_dev": params[3],
                "source_company_dev": source_parts[-2], "source_city_dev": source_parts[-1],
                "target_company_dev": target_parts[-2], "target_city_dev": target_parts[-1],
            }
        return self._execute_with_decryption(_parser)

    def get_police_offence_log(self) -> Optional[Dict[str, Any]]:
        def _parser(content):
            offences = []
            entry_pattern = re.compile(r'police_offence_log_entry\s*:\s*[^\s{]+\s*\{([^}]*)\}', re.DOTALL)
            for match in entry_pattern.finditer(content):
                entry_content = match.group(1)
                game_time_m = re.search(r'game_time:\s*(\d+)', entry_content)
                type_m = re.search(r'type:\s*(\d+)', entry_content)
                fine_m = re.search(r'fine:\s*(\d+)', entry_content)
                if game_time_m and type_m and fine_m:
                    offence_type = int(type_m.group(1))
                    offences.append({
                        "game_time_minutes": int(game_time_m.group(1)),
                        "formatted_time": self._format_game_time(int(game_time_m.group(1))),
                        "type_id": offence_type,
                        "type_human": OFFENCE_TYPE_MAP.get(offence_type, f"Unbekannt ({offence_type})"),
                        "fine": int(fine_m.group(1)),
                    })
            offences.sort(key=lambda x: x['game_time_minutes'], reverse=True)
            
            summary = {
                'ai_crash_count': int(m.group(1)) if (m := re.search(r'ai_crash_count:\s*(\d+)', content)) else 0,
                'red_light_fine_count': int(m.group(1)) if (m := re.search(r'red_light_fine_count:\s*(\d+)', content)) else 0,
                'total_fines': sum(o['fine'] for o in offences)
            }
            return {"summary": summary, "offences": offences}
        return self._execute_with_decryption(_parser)

    def _parse_job_content(self, content: str, current_game_time_minutes: Optional[int] = None, raw_start_cities_filter: Optional[List[str]] = None) -> (List[Dict[str, Any]], set):
        job_data_map = {}
        job_pattern = re.compile(r'job_offer_data\s*:\s*([^\s{]+)\s*\{([^}]*)\}', re.DOTALL)
        for match in job_pattern.finditer(content):
            job_id, job_content = match.groups()
            if 'cargo: null' in job_content or 'target: ""' in job_content: continue
            job_details = {'id': job_id.strip()}
            fields = {'target': r'target:\s*([^\s\n]+)', 'cargo': r'cargo:\s*([^\s\n]+)', 'distance_km': r'shortest_distance_km:\s*(\d+)', 'expiration_time': r'expiration_time:\s*(\d+)'}
            for key, pattern in fields.items():
                if field_match := re.search(pattern, job_content):
                    job_details[key] = field_match.group(1)
            job_data_map[job_details['id']] = job_details

        all_jobs, available_cities_raw = [], set()
        company_pattern = re.compile(r'company\s*:\s*(company\.volatile\.[^ ]+)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', re.DOTALL)
        for company_match in company_pattern.finditer(content):
            company_id, company_content = company_match.groups()
            start_company_info = self._parse_company_id(company_id)
            
            # Wenn ein Filter gesetzt ist und die Stadt nicht im Filter ist, überspringen
            if raw_start_cities_filter and start_company_info['city'] not in raw_start_cities_filter:
                continue
            
            available_cities_raw.add(start_company_info['city'])
            offer_id_pattern = re.compile(r'job_offer\[\d+\]:\s*([^\s\n]+)')
            for offer_id_match in offer_id_pattern.finditer(company_content):
                offer_id = offer_id_match.group(1)
                if offer_id in job_data_map:
                    job_data = job_data_map[offer_id]
                    distance = int(job_data.get('distance_km', 0))
                    if distance < 1: continue
                    
                    time_left = -1
                    if current_game_time_minutes is not None:
                        expiration_time = int(job_data.get('expiration_time', 0))
                        time_left = expiration_time - current_game_time_minutes
                        if time_left < 5: continue

                    target_info = self._parse_target_id(job_data.get('target', ''))
                    
                    all_jobs.append({
                        'start_company': translate_name(start_company_info['name'], COMPANY_MAP),
                        'start_city': get_pretty_city_name(start_company_info['city']),
                        'target_company': translate_name(target_info['name'], COMPANY_MAP),
                        'target_city': get_pretty_city_name(target_info['city']),
                        'cargo': translate_name(job_data.get('cargo', 'N/A'), CARGO_MAP),
                        'distance_km': distance,
                        'time_left_minutes': time_left,
                        'source_id': offer_id
                    })
        return all_jobs, available_cities_raw