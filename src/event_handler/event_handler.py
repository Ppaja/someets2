# src/event_handler/event_handler.py
import threading
import time
from datetime import datetime
import random
import re

from src.config import PROFILE_PATH
from src.game_integration.ets2_event_logger import ETS2EventLogger
from src.game_integration.ets2_savegame_parser import SavegameParser
from src.actions.communication import send_message, send_email
from src.utils.translation import get_human_job_details

class ETS2EventHandler:
    def __init__(self, profile_path: str = PROFILE_PATH):
        self.profile_path = profile_path
        self.logger = ETS2EventLogger(profile_path=self.profile_path, event_callback=self._handle_logged_event)
        self.logger_thread = None
        self.last_ai_crash_count = None
        self.active_jobs = {}
        print("✨ ETS2EventHandler initialisiert.")

    def _handle_logged_event(self, event_type: str, details: dict):
        handler_map = {
            "OVERALL_STATS_UPDATE": self._check_ai_crashes,
            "JOB_STARTED": self._store_job_start_details,
            "JOB_COMPLETED": self._check_job_delivery_status,
            "JOB_CANCELLED": self._check_job_delivery_status,
        }
        if handler := handler_map.get(event_type):
            handler(event_type, details)

    def _check_ai_crashes(self, event_type: str, details: dict):
        current_count = details.get("ai_crash_count")
        if current_count is not None:
            if self.last_ai_crash_count is not None and current_count > self.last_ai_crash_count:
                send_message("Dispo", "Gerade Info bekommen: Unfall mit deinem LKW? Alles okay bei dir?", sent_by_me=False)
            self.last_ai_crash_count = current_count

    def _store_job_start_details(self, event_type: str, details: dict):
        if job_id := details.get("id"):
            self.active_jobs[job_id] = details

    def _check_job_delivery_status(self, event_type: str, details: dict):
        job_id = details.get("job_id")
        if not (job_id and job_id in self.active_jobs):
            return

        start_details = self.active_jobs.pop(job_id)
        final_job_details = start_details.copy()

        try:
            parser = SavegameParser(profile_path=self.profile_path)
            if savegame_details := parser.get_last_delivery_log_details():
                final_job_details.update(get_human_job_details(savegame_details))
        except Exception as e:
            print(f"✗ Kritischer Fehler bei der Savegame-Analyse für Job-Details: {e}")

        cargo = final_job_details.get('cargo_human', 'die Lieferung')
        source = final_job_details.get('source_city_human', 'Unbekannt')
        target = final_job_details.get('target_city_human', 'Unbekannt')

        if event_type == "JOB_COMPLETED":
            is_late = False
            try:
                if (deadline_str := start_details.get("deadline_time")) and \
                   (completion_str := details.get("completion_iso_time")):
                    deadline_dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                    completion_dt = datetime.fromisoformat(completion_str.replace('Z', '+00:00'))
                    if completion_dt > deadline_dt:
                        is_late = True
            except (ValueError, TypeError):
                pass # Fehler beim Parsen, Pünktlichkeit unklar

            if is_late:
                self._send_late_delivery_email(final_job_details, details)
            else:
                send_message("Dispo", f"Fracht '{cargo}' von {source} nach {target} pünktlich abgeschlossen! Gute Arbeit!", sent_by_me=False)
        
        elif event_type == "JOB_CANCELLED":
            send_message("Dispo", f"Auftrag '{cargo}' von {source} nach {target} wurde abgebrochen. Bitte gib uns Bescheid, was passiert ist.", sent_by_me=False)

    def _send_late_delivery_email(self, job_details: dict, end_details: dict):
        customer = job_details.get('target_company_human', 'Unbekannter Kunde')
        cargo = job_details.get('cargo_human', 'N/A')
        source = job_details.get('source_city_human', 'N/A')
        target = job_details.get('target_city_human', 'N/A')
        
        subject = f"Lieferung verspätet: {source} -> {target}"
        body = (
            f"Hallo Fahrer,\n\n"
            f"Wir haben eine Rückmeldung zu Ihrer letzten Lieferung von {source} nach {target} erhalten.\n\n"
            f"Die Fracht '{cargo}' wurde leider verspätet geliefert. Der Kunde ({customer}) war nicht zufrieden.\n\n"
            f"Bitte stellen Sie sicher, dass zukünftige Lieferungen pünktlich erfolgen.\n\n"
            f"Mit freundlichen Grüßen,\nIhre Disposition"
        )
        send_email("Disposition", subject, body, time.time())
        #  kurz warten
        time.sleep(3)
        send_message("Dispo", f"Deine Lieferung von {source} nach {target} war leider zu spät. Schau in deine Mails.", sent_by_me=False)

    def start(self):
        if not self.logger_thread or not self.logger_thread.is_alive():
            self.logger_thread = threading.Thread(target=self.logger.run, daemon=True)
            self.logger_thread.start()
            print("✨ ETS2EventHandler: Logger-Thread gestartet.")

    def stop(self):
        if self.logger_thread and self.logger_thread.is_alive():
            self.logger.stop()
            self.logger_thread.join(timeout=5)
            print("✨ ETS2EventHandler: Logger-Thread beendet.")
