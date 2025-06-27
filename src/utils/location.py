# src/utils/location.py
import json
import math
import requests
from pathlib import Path

from src.config import TELEMETRY_URL

CITY_DB_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "city_database.json"
# TELEMETRY_URL = "http://172.24.176.1:25555/api/ets2/telemetry"
print(f"TELEMETRY_URL: {TELEMETRY_URL}")
def load_city_database():
    """Lädt die Städte-Koordinaten-Datenbank."""
    if not CITY_DB_FILE.exists():
        print(f"❌ FEHLER: Die Datei '{CITY_DB_FILE}' wurde nicht gefunden.")
        return None
    try:
        with open(CITY_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ FEHLER: Die Datei '{CITY_DB_FILE}' enthält ungültiges JSON.")
        return None

def get_current_coordinates():
    """Holt die aktuellen X, Y, Z Koordinaten des Spielers vom Telemetrie-Server."""
    try:
        response = requests.get(TELEMETRY_URL, timeout=0.5)
        response.raise_for_status()
        data = response.json()
        if data.get("game", {}).get("connected"):
            if "x" in (truck_pos := data.get("truck", {}).get("placement", {})):
                return {"x": truck_pos.get("x", 0), "y": truck_pos.get("y", 0), "z": truck_pos.get("z", 0)}
    except (requests.exceptions.RequestException, json.JSONDecodeError):
        pass
    return None

def _calculate_distance_2d(pos1, pos2):
    """Berechnet die 2D-Distanz (X/Z-Ebene)."""
    dx = pos1["x"] - pos2["x"]
    dz = pos1["z"] - pos2["z"]
    return math.sqrt(dx*dx + dz*dz)

def get_nearest_city_from_db(player_coords, city_db):
    """
    Findet die nächstgelegene Stadt aus der kompletten Koordinaten-Datenbank.
    Gibt den "schönen" Namen (Schlüssel) zurück.
    """
    if not all([player_coords, city_db]):
        return None

    nearest_city_name = None
    min_distance = float('inf')

    for city_name, city_coords in city_db.items():
        distance = _calculate_distance_2d(player_coords, city_coords)
        if distance < min_distance:
            min_distance = distance
            nearest_city_name = city_name
            
    return nearest_city_name