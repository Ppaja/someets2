# src/game_integration/ets2_event_logger.py
import json
import time
import re
import requests
from datetime import datetime
from typing import Optional, Callable

from src.config import PROFILE_PATH, ETS2_LOG_FILE, TELEMETRY_URL
from src.utils.translation import get_human_job_details
from .ets2_savegame_parser import SavegameParser

class ETS2EventLogger:
    def __init__(self, profile_path: str = PROFILE_PATH, log_file: str = ETS2_LOG_FILE, event_callback: Optional[Callable] = None):
        self.profile_path = profile_path
        self.log_file = log_file
        self.log_entries = self._load_log()
        self._is_running = False
        self.event_callback = event_callback

        self._last_telemetry_data = {}
        self._current_job_id = None
        self._last_game_connected_state = False
        self._last_overall_stats_update_time = 0
        self._overall_stats_update_interval = 300  # 5 Minuten

        self.savegame_parser = None
        try:
            self.savegame_parser = SavegameParser(self.profile_path)
        except FileNotFoundError as e:
            print(f"✗ FEHLER: ETS2 Profilpfad nicht gefunden: {e}. Savegame-Statistiken werden nicht geloggt.")
        except Exception as e:
            print(f"✗ Unerwarteter Fehler beim Initialisieren des Savegame Parsers: {e}.")

        print(f"📋 ETS2EventLogger initialisiert. Log-Datei: {self.log_file}")

    def _load_log(self) -> list:
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f).get('events', [])
            except (json.JSONDecodeError, AttributeError):
                return []
        return []

    def _save_log(self):
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump({'events': self.log_entries}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"✗ Fehler beim Speichern der Log-Datei: {e}")

    def _log_event(self, event_type: str, details: dict):
        event = {
            "timestamp": time.time(),
            "datetime_iso": datetime.now().isoformat(),
            "type": event_type,
            "details": details
        }
        self.log_entries.append(event)
        self._save_log()
        print(f"LOG: {event_type} - {details.get('message', details)}")
        if self.event_callback:
            self.event_callback(event_type, details)

    def _get_telemetry_data(self) -> dict:
        try:
            response = requests.get(TELEMETRY_URL, timeout=0.5)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            return {"game": {"connected": False}}

    def _get_game_time_str(self, telemetry_data: dict) -> str:
        if iso_time_str := telemetry_data.get("game", {}).get("time"):
            try:
                dt = datetime.fromisoformat(iso_time_str.replace("Z", "+00:00"))
                return f"{dt.hour:02d}:{dt.minute:02d}"
            except (ValueError, TypeError):
                pass
        return "N/A"

    def _process_telemetry_data(self, telemetry_data: dict):
        game_connected = telemetry_data.get("game", {}).get("connected", False)
        if game_connected != self._last_game_connected_state:
            event_type = "GAME_CONNECTED" if game_connected else "GAME_DISCONNECTED"
            self._log_event(event_type, {"message": f"ETS2 Spiel {'verbunden' if game_connected else 'getrennt'}."})
            if game_connected:
                self._update_overall_stats_from_savegame() # Direkt beim Verbinden aktualisieren
            self._last_game_connected_state = game_connected

        if not game_connected or telemetry_data.get("game", {}).get("paused", False):
            return

        job_data = telemetry_data.get("job", {})
        is_job_active_now = bool(job_data.get("sourceCity") and job_data.get("destinationCity"))
        last_job_data = self._last_telemetry_data.get("job", {})
        was_job_active_before = bool(last_job_data.get("sourceCity") and last_job_data.get("destinationCity"))

        if is_job_active_now and not was_job_active_before:
            job_details = {
                "id": f"job_{int(time.time())}",
                "source_company_dev": job_data.get("sourceCompany", "N/A"),
                "source_city_dev": job_data.get("sourceCity", "N/A"),
                "target_company_dev": job_data.get("destinationCompany", "N/A"),
                "target_city_dev": job_data.get("destinationCity", "N/A"),
                "cargo_dev": job_data.get("cargo", "N/A"),
                "deadline_time": job_data.get("deadlineTime", "N/A"),
            }
            job_details.update(get_human_job_details(job_details))
            self._log_event("JOB_STARTED", job_details)
            self._current_job_id = job_details["id"]

        elif not is_job_active_now and was_job_active_before:
            revenue = last_job_data.get("income", 0)
            event_type = "JOB_COMPLETED" if revenue > 0 else "JOB_CANCELLED"
            job_end_details = {
                "job_id": self._current_job_id,
                "revenue": revenue,
                "ingame_time": self._get_game_time_str(telemetry_data),
                "completion_iso_time": telemetry_data.get("game", {}).get("time")
            }
            self._log_event(event_type, job_end_details)
            self._current_job_id = None

        self._last_telemetry_data = telemetry_data

    def _update_overall_stats_from_savegame(self):
        if not self.savegame_parser: return
        current_time = time.time()
        if current_time - self._last_overall_stats_update_time < self._overall_stats_update_interval:
            return

        print("... Lese Savegame für Gesamtstatistiken ...")
        def _parser(content):
            return {
                "total_distance_km": int(m.group(1)) if (m := re.search(r'total_distance:\s*(\d+)', content)) else 0,
                "ai_crash_count": int(m.group(1)) if (m := re.search(r'ai_crash_count:\s*(\d+)', content)) else 0,
                "red_light_fine_count": int(m.group(1)) if (m := re.search(r'red_light_fine_count:\s*(\d+)', content)) else 0,
            }
        
        stats = self.savegame_parser._execute_with_decryption(_parser)
        if stats:
            self._log_event("OVERALL_STATS_UPDATE", stats)
            self._last_overall_stats_update_time = current_time

    def run(self):
        self._is_running = True
        print("🚀 ETS2EventLogger gestartet. Warte auf Telemetriedaten...")
        while self._is_running:
            telemetry_data = self._get_telemetry_data()
            self._process_telemetry_data(telemetry_data)
            if telemetry_data.get("game", {}).get("connected", False):
                self._update_overall_stats_from_savegame()
            time.sleep(1)

    def stop(self):
        self._is_running = False
        print("🛑 ETS2EventLogger gestoppt.")
        self._save_log()
