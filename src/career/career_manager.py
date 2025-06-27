# src/career/career_manager.py
import threading
import time
import json
from pathlib import Path
import requests

from src.config import DATA_DIR, TELEMETRY_URL
from src.actions.communication import send_email
from src.utils.location import get_current_coordinates, load_city_database, get_nearest_city_from_db
from src.utils.geometry import is_point_in_polygon
from src.game_integration.ets2_savegame_parser import SavegameParser
from src.utils.translation import get_pretty_city_name

CAREER_DATA_FILE = DATA_DIR / "career_data.json"
COMPANY_LOCATIONS_FILE = DATA_DIR / "company_locations.json"

class CareerManager:
    def __init__(self, laptop_ui_instance):
        self.laptop_ui = laptop_ui_instance
        self.career_data = self._load_json(CAREER_DATA_FILE, default={"status": "unemployed", "company": None, "application_pending": None})
        self.company_locations = self._load_json(COMPANY_LOCATIONS_FILE, default={})
        self.parser = SavegameParser()
        self.city_db = load_city_database()
        
        self._is_running = False
        self.monitor_thread = None
        print("✨ CareerManager initialisiert.")

    def _load_json(self, file_path: Path, default=None):
        if not file_path.exists():
            if default is not None:
                self.save_career_data(default)
            return default or {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default or {}

    def save_career_data(self, data=None):
        if data is None: data = self.career_data
        with open(CAREER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def start(self):
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self._is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("✨ CareerManager: Monitoring-Thread gestartet.")

    def stop(self):
        self._is_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        print("✨ CareerManager: Monitoring-Thread beendet.")

    def apply_for_job(self, company_name):
        if self.career_data.get("status") != "unemployed": return
        self.career_data["application_pending"] = company_name.lower()
        self.save_career_data()
        
        subject = f"Ihre Bewerbung bei NETTO - Eingangsbestätigung"
        body = (f"Sehr geehrte Damen und Herren,\n\n"
                f"vielen Dank für Ihr Interesse an einer Tätigkeit als Lieferfahrer bei NETTO Marken-Discount.\n\n"
                f"Ihre Bewerbungsunterlagen sind bei uns eingegangen und werden derzeit geprüft. "
                f"Wir möchten Sie gerne zu einem persönlichen Gespräch einladen.\n\n"
                f"📍 TERMINVEREINBARUNG:\n"
                f"Bitte besuchen Sie eine unserer Filialen für ein kurzes Kennenlerngespräch. "
                f"Parken Sie einfach auf unserem Gelände und schalten Sie den Motor aus - "
                f"unser Filialleiter wird dann zu Ihnen kommen.\n\n"
                f"Wir freuen uns darauf, Sie kennenzulernen!\n\n"
                f"Mit freundlichen Grüßen\n"
                f"Ihr NETTO Personalteam\n\n"
                f"---\n"
                f"NETTO Marken-Discount Stiftung & Co. KG\n"
                f"Personalabteilung\n"
                f"industriepark-ponholz.de")
        
        send_email("NETTO Personalabteilung", subject, body, time.time())

    def _monitor_loop(self):
        while self._is_running:
            if self.career_data.get("application_pending"):
                self._check_for_interview()
            time.sleep(5)

    def _check_for_interview(self):
        company_to_check = self.career_data["application_pending"]
        locations = self.company_locations.get(company_to_check, [])
        if not locations: return
        coords = get_current_coordinates()
        if not coords: return
        try:
            response = requests.get(TELEMETRY_URL, timeout=0.5)
            engine_on = response.json().get("truck", {}).get("engineOn", True)
            if not engine_on:
                player_pos = (coords['x'], coords['z'])
                for location in locations:
                    polygon = [(c['x'], c['z']) for c in location['corners']]
                    if is_point_in_polygon(player_pos, polygon):
                        print(f"INTERVIEW TRIGGERED! Spieler ist bei {location['template_name']} und Motor ist aus.")
                        self.career_data["application_pending"] = None
                        self.save_career_data()
                        self.laptop_ui.window.after(0, self.laptop_ui.play_fullscreen_video, "bewerbung.mp4", lambda: self.complete_hiring(company_to_check))
                        return
        except (requests.RequestException, json.JSONDecodeError): pass

    def complete_hiring(self, company_name):
        self.career_data["status"] = "employed"
        self.career_data["company"] = company_name
        self.save_career_data()
        
        police_data = self.parser.get_police_offence_log()
        witty_comment = "Ihr Gespräch war überzeugend und Ihre Führungszeugnis ist einwandfrei. Perfekt für unser Team!"
        
        if police_data:
            total_fines = police_data.get("summary", {}).get("total_fines", 0)
            crash_count = police_data.get("summary", {}).get("ai_crash_count", 0)
            
            if total_fines > 1000:
                witty_comment = "Ihre Verkehrsakte ist... interessant. Aber wir schätzen Fahrer mit Erfahrung. Sie sind dabei!"
            elif crash_count > 5:
                witty_comment = "Wir sehen, dass Sie bereits intensive Kontakte mit anderen Verkehrsteilnehmern hatten. Das zeigt Engagement!"
        
        subject = f"Herzlich Willkommen bei NETTO! 🎉"
        body = (f"Sehr geehrte Damen und Herren,\n\n"
                f"wir freuen uns sehr, Ihnen mitteilen zu können, dass Sie ab sofort Teil des NETTO-Teams sind!\n\n"
                f"{witty_comment}\n\n"
                f"🚛 IHR NEUER ARBEITSPLATZ:\n"
                f"Als Lieferfahrer bei NETTO sind Sie ein wichtiger Teil unserer Logistikkette. "
                f"Sie sorgen dafür, dass unsere Filialen immer bestens versorgt sind.\n\n"
                f"💻 MITARBEITERPORTAL:\n"
                f"Sie haben nun Zugriff auf unser internes Mitarbeiterportal über den Browser auf Ihrem Laptop. "
                f"Dort können Sie:\n"
                f"• Neue Aufträge anfordern\n"
                f"• Ihre Leistungsdaten einsehen\n"
                f"• Aktuelle Unternehmensnachrichten lesen\n"
                f"• Ihren Dienstplan verwalten\n\n"
                f"🎯 ERSTE SCHRITTE:\n"
                f"Loggen Sie sich in das Mitarbeiterportal ein und fordern Sie Ihren ersten Auftrag an. "
                f"Unser Dispositionsteam wird Ihnen passende Touren zuweisen.\n\n"
                f"Wir wünschen Ihnen einen erfolgreichen Start und freuen uns auf die Zusammenarbeit!\n\n"
                f"Mit freundlichen Grüßen\n"
                f"Ihr NETTO Personalteam\n\n"
                f"---\n"
                f"Bei Fragen wenden Sie sich gerne an:\n"
                f"📧 personal@netto-online.de\n"
                f"📞 0800 - NETTO-JOB")
        
        send_email("NETTO Personalteam", subject, body, time.time())

    def find_company_job(self):
        if self.career_data.get("status") != "employed": return
        
        company_name_human = "NETTO"
        self.laptop_ui.update_intranet_status(f"🔍 Durchsuche Frachtmarkt für {company_name_human}-Aufträge...")

        all_jobs = self.parser.get_freight_market_jobs()
        player_coords = get_current_coordinates()
        
        if not all_jobs or not player_coords:
            self.laptop_ui.update_intranet_status("❌ Fehler: Konnte Frachtmarkt nicht erreichen oder Standort nicht ermitteln.")
            return

        player_city = get_nearest_city_from_db(player_coords, self.city_db)
        player_city_pretty = get_pretty_city_name(player_city) if player_city else None

        best_job = None
        job_type = "Standardauftrag"

        # 1. Priorität: Von Spielerstadt zu NETTO (Direktauftrag)
        if player_city_pretty:
            jobs_from_player_city_to_netto = [
                j for j in all_jobs 
                if j['start_city'] == player_city_pretty and company_name_human.lower() in j.get('target_company', '').lower()
            ]
            if jobs_from_player_city_to_netto:
                best_job = sorted(jobs_from_player_city_to_netto, key=lambda j: j['distance_km'])[0]
                job_type = "Direktlieferung"

        # 2. Priorität: Von NETTO-Filiale irgendwohin (Interne Umlagerung)
        if not best_job:
            jobs_from_netto = [j for j in all_jobs if company_name_human.lower() in j.get('start_company', '').lower()]
            if jobs_from_netto:
                best_job = sorted(jobs_from_netto, key=lambda j: j['distance_km'])[0]
                job_type = "Filial-Umlagerung"

        # 3. Priorität: Von irgendwo zu NETTO (Zulieferung)
        if not best_job:
            jobs_to_netto = [j for j in all_jobs if company_name_human.lower() in j.get('target_company', '').lower()]
            if jobs_to_netto:
                best_job = sorted(jobs_to_netto, key=lambda j: j['distance_km'])[0]
                job_type = "Warenlieferung"

        # 4. Priorität: Aushilfsfahrt von Spielerstadt
        if not best_job and player_city_pretty:
            jobs_from_player_city = [j for j in all_jobs if j['start_city'] == player_city_pretty]
            if jobs_from_player_city:
                best_job = sorted(jobs_from_player_city, key=lambda j: j['distance_km'])[0]
                job_type = "Externe Aushilfsfahrt"

        # Ergebnis verarbeiten
        if best_job:
            self.laptop_ui.update_intranet_status(f"✅ {job_type} gefunden! Details werden per E-Mail übermittelt.")
            self._send_job_email(best_job, job_type)
        else:
            self.laptop_ui.update_intranet_status("⏳ Aktuell keine passenden Aufträge verfügbar. Versuchen Sie es in wenigen Minuten erneut.")

    def _send_job_email(self, job, job_type):
        company_name_human = "NETTO"
        
        # Job-spezifische Einleitungen
        intro_texts = {
            "Direktlieferung": f"eine Direktlieferung für eine {company_name_human}-Filiale steht bereit.",
            "Filial-Abholung": f"eine wichtige Fracht steht verladen auf unserer {company_name_human}-Filiale bereit.",
            "Warenlieferung": f"eine dringende Warenlieferung für {company_name_human} muss abgeholt werden.",
            "Externe Aushilfsfahrt": f"da intern wenig Verkehr herrscht, haben wir eine externe Aushilfsfahrt organisiert."
        }
        
        intro_text = intro_texts.get(job_type, "ein neuer Transportauftrag wartet auf Sie.")
        
        # Prioritätskennzeichnung
        priority_icon = "🔴" if job_type in ["Direktlieferung", "Filial-Abholung"] else "🟡"
        
        subject = f"{priority_icon} {job_type}: {job['cargo']} | {job['start_city']} → {job['target_city']}"
        
        body = (
            f"Liebe Kollegin, lieber Kollege,\n\n"
            f"{intro_text}\n\n"
            f"📋 AUFTRAGSDATEN:\n"
            f"Auftragstyp: {job_type}\n"
            f"Fracht: {job['cargo']}\n"
            f"Entfernung: {job['distance_km']} km\n\n"
            f"📍 ABHOLUNG:\n"
            f"Unternehmen: {job['start_company']}\n"
            f"Standort: {job['start_city']}\n\n"
            f"🎯 LIEFERUNG:\n"
            f"Unternehmen: {job['target_company']}\n"
            f"Standort: {job['target_city']}\n\n"
            f"⚠️ WICHTIGE HINWEISE:\n"
            f"• Bitte beachten Sie die Annahmefrist im Frachtmarkt\n"
            f"• Kontrollieren Sie die Ladung vor Abfahrt\n"
            f"• Melden Sie Verzögerungen umgehend an die Disposition\n"
            f"• Fahren Sie vorsichtig und halten Sie alle Verkehrsregeln ein\n\n"
            f"Bei Fragen oder Problemen erreichen Sie uns unter:\n"
            f"📞 Disposition: 0800-NETTO-24\n"
            f"📧 disposition@netto-logistik.de\n\n"
            f"Gute und sichere Fahrt!\n\n"
            f"Ihr Dispositionsteam\n"
            f"NETTO Logistik GmbH"
        )
        
        send_email("NETTO Disposition", subject, body, time.time())
