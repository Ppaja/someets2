
# src/actions/communication.py
import json
import os
import time
import requests
from datetime import datetime
import winsound

from src.config import (
    PHONE_MESSAGE_FILE, LAPTOP_MAIL_FILE, TELEMETRY_URL,
    SMS_SOUND_PATH, MAIL_SOUND_PATH
)

def _play_sound(sound_path):
    """Spielt eine Sound-Datei asynchron ab, wenn sie existiert."""
    if sound_path.exists():
        try:
            winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Fehler beim Abspielen von Sound {sound_path}: {e}")
    else:
        print(f"Sound-Datei nicht gefunden: {sound_path}")

def get_current_ingame_time_str():
    """Holt die aktuelle Ingame-Zeit und gibt sie als formatierten String zurück."""
    try:
        response = requests.get(TELEMETRY_URL, timeout=0.5)
        response.raise_for_status()
        data = response.json()
        game_data = data.get("game")
        if game_data and "time" in game_data:
            iso_time_str = game_data.get("time")
            if iso_time_str:
                dt = datetime.fromisoformat(iso_time_str.replace("Z", "+00:00"))
                return f"{dt.hour:02d}:{dt.minute:02d}"
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        pass # Fallback auf Echtzeit, wenn Telemetrie nicht erreichbar
    return datetime.now().strftime("%H:%M")

def send_message(sender, message_text, sent_by_me=False):
    """Sendet eine Nachricht an das Handy."""
    if not sent_by_me:
        _play_sound(SMS_SOUND_PATH)

    try:
        data = {"conversations": []}
        if PHONE_MESSAGE_FILE.exists():
            with open(PHONE_MESSAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        conversation = next((c for c in data["conversations"] if c["sender"] == sender), None)
        if not conversation:
            conversation = {"sender": sender, "messages": []}
            data["conversations"].append(conversation)
        
        new_message = {
            "text": message_text, "timestamp": time.time(),
            "ingame_time": get_current_ingame_time_str(),
            "sent_by_me": sent_by_me, "read": sent_by_me
        }
        conversation["messages"].append(new_message)
        
        with open(PHONE_MESSAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📱 Nachricht an {sender} gesendet.")
    except Exception as e:
        print(f"Fehler beim Senden der Nachricht: {e}")

def send_email(sender, subject, body, timestamp):
    """Sendet eine E-Mail an den Laptop."""
    _play_sound(MAIL_SOUND_PATH)
    try:
        data = {"emails": []}
        if LAPTOP_MAIL_FILE.exists():
            with open(LAPTOP_MAIL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        new_email = {
            "sender": sender, "subject": subject,
            "body": body.replace('\\n', '\n'),
            "timestamp": timestamp, "read": False
        }
        data["emails"].append(new_email)
        
        with open(LAPTOP_MAIL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📧 E-Mail von {sender} an Laptop gesendet.")
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")

def create_sample_files_if_missing():
    """Erstellt Beispiel-Nachrichten/Mails, falls die Dateien nicht existieren."""
    if not PHONE_MESSAGE_FILE.exists():
        sample_conversations = {
            "conversations": [{
                "sender": "Dispo",
                "messages": [{
                    "text": "Willkommen an Bord! Melde dich hier, wenn du einen neuen Auftrag brauchst.",
                    "timestamp": time.time() - 86400, "sent_by_me": False, "read": True, "ingame_time": "12:00"
                }]
            }]
        }
        with open(PHONE_MESSAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(sample_conversations, f, ensure_ascii=False, indent=2)
        print("✅ Beispiel-Nachrichtendatei erstellt.")

    if not LAPTOP_MAIL_FILE.exists():
        sample_emails = {"emails": []}
        with open(LAPTOP_MAIL_FILE, 'w', encoding='utf-8') as f:
            json.dump(sample_emails, f, ensure_ascii=False, indent=2)
        print("✅ Leere E-Mail-Datei erstellt.")