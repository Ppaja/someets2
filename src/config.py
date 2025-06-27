# src/config.py
import os
from pathlib import Path

# Basisverzeichnis des Projekts
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Pfade ---
PROFILE_PATH = Path(r"C:\Users\Anwender\Documents\Euro Truck Simulator 2\profiles\7374726166656E74657374")
DATA_DIR = BASE_DIR / "data"
TOOLS_DIR = BASE_DIR / "tools"
SFX_DIR = BASE_DIR / "sfx"

# --- Dateipfade ---
PHONE_MESSAGE_FILE = DATA_DIR / "phone_messages.json"
LAPTOP_MAIL_FILE = DATA_DIR / "laptop_mail.json"
ETS2_LOG_FILE = DATA_DIR / "ets2_log.json"
SII_DECRYPT_EXE = TOOLS_DIR / "SII_Decrypt.exe"
DELIVERY_DATA_FILE = DATA_DIR / "delivery_data.json" 

# --- Sound-Dateien ---
SMS_SOUND_PATH = SFX_DIR / "sms_sound.wav"
MAIL_SOUND_PATH = SFX_DIR / "mail_sound.wav"

# --- Netzwerk & APIs ---
TELEMETRY_URL = "http://172.24.176.1:25555/api/ets2/telemetry"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEXT_GENERATION_MODEL = "gemini-2.5-flash" # Oder dein bevorzugtes Modell

# --- UI-Einstellungen ---
# Handy
PHONE_WIDTH = 320
PHONE_HEIGHT = 550
# Laptop
LAPTOP_WIDTH = 800
LAPTOP_HEIGHT = 500



OFFENCE_TYPE_MAP = {
    0: "Unfall mit Fremdbeteiligung",
    1: "Übermüdung / Ruhezeit ignoriert", 
    2: "Falsche Fahrbahn / Geisterfahrt",
    3: "Geschwindigkeitsüberschreitung (Blitzer)", 
    4: "Fahren ohne Licht bei Nacht", 
    5: "Rotlichtverstoß", 
    6: "Geschwindigkeitsüberschreitung", 
    7: "Wiegekontrolle umgangen",
    8: "Illegaler Anhänger",
    9: "Fahrzeugkontrolle umgangen",
    10: "Illegaler Grenzübertritt",
    11: "Seitenstreifen unbefugt befahren",
    12: "Fahren mit beschädigtem Fahrzeug",
}
