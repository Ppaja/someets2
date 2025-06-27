# src/actions/job_actions.py
import json
import threading
import requests
import time
import re
import google.generativeai as genai
from datetime import datetime
import random

from src.config import TELEMETRY_URL, PROFILE_PATH, GEMINI_API_KEY, TEXT_GENERATION_MODEL
from src.actions.communication import send_message, send_email
from src.game_integration.ets2_savegame_parser import SavegameParser

def _get_current_telemetry():
    try:
        response = requests.get(TELEMETRY_URL, timeout=1.0)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        return None

def _get_ingame_time_in_minutes(telemetry_data):
    if telemetry_data and (time_str := telemetry_data.get("game", {}).get("time")):
        try:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            return (dt.weekday() * 1440) + (dt.hour * 60) + dt.minute
        except (ValueError, TypeError, KeyError):
            return None
    return None

def _do_process_job_request(city_name: str):
    # ### DEV ###
    print(f"\n[DEBUG] Job-Anfrage gestartet für Stadt: '{city_name}'")

    send_message("Dispo", "Moment, ich schaue mal, was da ist...", sent_by_me=False)

    telemetry = _get_current_telemetry()
    current_time_minutes = _get_ingame_time_in_minutes(telemetry)
    
    if current_time_minutes is None:
        send_message("Dispo", "Ich kann die Ingame-Zeit gerade nicht abrufen, aber ich suche trotzdem nach Aufträgen.")
        print("[DEBUG] Konnte Ingame-Zeit nicht abrufen.")
    else:
        print(f"[DEBUG] Aktuelle Ingame-Zeit in Minuten: {current_time_minutes}")


    time.sleep(1)
    send_message("Dispo", f"Okay, du bist also in {city_name}. Ich suche nach Aufträgen von dort.", sent_by_me=False)
    time.sleep(2)

    try:
        reader = SavegameParser(profile_path=PROFILE_PATH)
        all_jobs = reader.get_freight_market_jobs(current_game_time_minutes=current_time_minutes)
        
        if not all_jobs:
             # ### DEV ###
             print("[DEBUG] FEHLER: Der Savegame-Parser hat KEINE Jobs zurückgegeben (leere Liste oder None).")
             send_message("Dispo", "Problem beim Lesen der Auftragsliste. Versuch es später nochmal.", sent_by_me=False)
             return

        # ### DEV ###
        print(f"[DEBUG] Parser hat insgesamt {len(all_jobs)} Jobs gefunden.")
        unique_start_cities = sorted(list(set([j['start_city'] for j in all_jobs])))
        print(f"[DEBUG] Einzigartige Startstädte in den Daten: {unique_start_cities}")

        target_city_lower = city_name.lower()
        jobs = [j for j in all_jobs if j['start_city'].lower() == target_city_lower]
        
        # ### DEV ###
        print(f"[DEBUG] Suche nach '{target_city_lower}'. Nach dem Filtern sind {len(jobs)} Jobs übrig.")


    except Exception as e:
        print(f"[DEBUG] Kritischer Fehler beim Laden der Jobs: {e}")
        send_message("Dispo", f"Ein technischer Fehler ist aufgetreten: {e}", sent_by_me=False)
        return

    if not jobs:
        send_message("Dispo", f"Tut mir leid, ich finde aktuell keine verfügbaren Aufträge von {city_name}. Versuch es später nochmal.", sent_by_me=False)
        return

    job_options = []
    if len(jobs) > 0:
        jobs.sort(key=lambda j: j['distance_km'])
        job_options.append(jobs[0])
        if len(jobs) > 1:
            job_options.append(jobs[-1])
        middle_jobs = jobs[1:-1]
        if len(middle_jobs) > 0:
            num_to_add = min(len(middle_jobs), 3)
            job_options.extend(random.sample(middle_jobs, num_to_add))

    unique_options = []
    seen_jobs = set()
    for job in job_options:
        fingerprint = (job['start_company'], job['target_company'], job['cargo'], job['distance_km'])
        if fingerprint not in seen_jobs:
            unique_options.append(job)
            seen_jobs.add(fingerprint)
    
    unique_options.sort(key=lambda j: j['distance_km'], reverse=True)
    job_options = unique_options

    job_list_for_prompt = "".join(
        f"Option {i+1}:\n"
        f"  - Von: {job['start_company']} in {job['start_city']}\n"
        f"  - Nach: {job['target_company']} in {job['target_city']}\n"
        f"  - Fracht: {job['cargo']}\n"
        f"  - Distanz: {job['distance_km']} km\n\n"
        for i, job in enumerate(job_options)
    )
    prompt = """Du bist ein KI-Disponent für eine Spedition im Spiel Euro Truck Simulator 2. Dein Fahrer in {city_name} braucht einen neuen Auftrag.

        Hier ist eine Liste der verfügbaren Aufträge. Die Namen sind bereits die korrekten Ingame-Namen:
        {job_list_for_prompt}
        
        Deine Aufgabe:
        1. Analysiere die Aufträge. Lange Strecken sind in der Regel gut.
        2. Wähle die beste Option für den Fahrer aus.
        3. Formuliere eine kurze, informelle Antwort für das Handy des Fahrers.
        4. Formuliere eine professionelle E-Mail mit den Details.
        
        Gib deine Antwort ausschließlich als JSON-Objekt mit den Schlüsseln "chosen_option", "phone_reply", "email_subject", "email_body" zurück.
        
        Für "email_body", nutze dieses Template und ersetze die Platzhalter NICHT: "Hallo Fahrer,\\n\\nIhr nächster Auftrag steht fest.\\n\\nAbholung:\\nFirma: {{start_company}}\\nStadt: {{start_city}}\\n\\nLieferung:\\nFirma: {{target_company}}\\nStadt: {{target_city}}\\n\\nDetails:\\nFracht: {{cargo}}\\nDistanz: {{distance_km}} km\\n\\nGute Fahrt!\\nIhre Disposition"
        
        Beispiel wie eine Antwort auszusehen hat:
        {{
          "chosen_option": 1,
          "phone_reply": "Hab was für dich: Du fährst Restmüll von Remondis in Pirmasens nach Hauenstein zu Schumacher Packaging. Sind 23 km. Details kommen per Mail.",
          "email_subject": "Transportauftrag: Restmüll von Pirmasens nach Hauenstein",
          "email_body": "Hallo Fahrer,\\n\\nIhr nächster Auftrag steht fest.\\n\\nAbholung:\\nFirma: {{start_company}}\\nStadt: {{start_city}}\\n\\nLieferung:\\nFirma: {{target_company}}\\nStadt: {{target_city}}\\n\\nDetails:\\nFracht: {{cargo}}\\nDistanz: {{distance_km}} km\\n\\nGute Fahrt!\\nIhre Disposition"
        }}
        """.format(city_name=city_name, job_list_for_prompt=job_list_for_prompt)

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(TEXT_GENERATION_MODEL)
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        if json_match := re.search(r'```json\s*([\s\S]*?)\s*```', response_text):
            response_text = json_match.group(1)
        
        response_data = json.loads(response_text)
        
        chosen_option_raw = response_data.get("chosen_option")
        chosen_option_index = -1
        if isinstance(chosen_option_raw, int):
            chosen_option_index = chosen_option_raw
        elif isinstance(chosen_option_raw, str):
            if match := re.search(r'\d+', chosen_option_raw):
                chosen_option_index = int(match.group(0))

        if not (1 <= chosen_option_index <= len(job_options)):
            raise ValueError(f"KI hat keine gültige Option gewählt: {chosen_option_raw}")

        chosen_job = job_options[chosen_option_index - 1]
        
        send_message("Dispo", response_data.get("phone_reply", "Konnte die Antwort nicht verarbeiten."), sent_by_me=False)

        time.sleep(2)
        send_email(
            sender="Disposition",
            subject=response_data.get("email_subject", "Neuer Auftrag").format(**chosen_job),
            body=response_data.get("email_body", "Details konnten nicht geladen werden.").format(**chosen_job),
            timestamp=time.time()
        )
        print("✅ Antworten an Handy und Laptop mit korrekten Daten gesendet.")

    except Exception as e:
        print(f"✗ Fehler bei der Gemini-Verarbeitung oder Daten-Validierung: {e}")
        send_message("Dispo", "Ich habe gerade ein Problem mit dem System. Schau später nochmal rein.", sent_by_me=False)

def process_job_request_async(city_name: str):
    """Startet die Job-Anfrage in einem separaten Thread."""
    threading.Thread(target=_do_process_job_request, args=(city_name,), daemon=True).start()