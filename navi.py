import pygame
import requests
import time
import math
import json
import os

from src.config import TELEMETRY_URL

# --- KONFIGURATION ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
FPS = 30

# Farben
COLOR_BACKGROUND = (30, 30, 30)
COLOR_ROAD = (100, 100, 100)
COLOR_TRUCK = (0, 150, 255)
COLOR_TEXT = (220, 220, 220)
COLOR_POI = (255, 190, 0)
COLOR_POI_LABEL_BG = (0, 0, 0, 180)

# --- DATEIPFADE (SAUBER GETRENNT) ---
# Eingabedaten (wird nur gelesen)
POI_FILE = "data/locations.json"
# Ausgabedaten / Cache (wird geschrieben und gelesen)
CACHE_DIR = "cache"
ROAD_SAVE_FILE = os.path.join(CACHE_DIR, "road_network.json") # GEÄNDERT

# --- ANWENDUNGS-SETUP ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ETS2 Self-Learning Navi v2.1 - Clean Data")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)
font_poi = pygame.font.SysFont("Arial", 16, bold=True)

# --- DATENSPEICHER ---
road_network = []
points_of_interest = []
current_road_segment = []
live_truck_data = {}

# Kamera-Steuerung
camera_offset = pygame.math.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
camera_zoom = 0.15
is_dragging = False
drag_start_pos = None

def load_road_network():
    """Lädt das gespeicherte Straßennetz aus dem Cache-Ordner."""
    global road_network
    if os.path.exists(ROAD_SAVE_FILE):
        try:
            with open(ROAD_SAVE_FILE, 'r') as f:
                road_network = json.load(f)
            print(f"Erfolgreich {len(road_network)} Straßensegmente aus {ROAD_SAVE_FILE} geladen.")
        except json.JSONDecodeError:
            print(f"Fehler: {ROAD_SAVE_FILE} ist beschädigt. Starte mit einer leeren Karte.")
            road_network = []

def save_road_network():
    """Speichert das aktuelle Straßennetz im Cache-Ordner."""
    # NEU: Stellt sicher, dass der Cache-Ordner existiert, bevor gespeichert wird.
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    if len(current_road_segment) > 1:
        road_network.append(current_road_segment)
    
    with open(ROAD_SAVE_FILE, 'w') as f:
        json.dump(road_network, f)
    print(f"Straßennetz mit {len(road_network)} Segmenten in {ROAD_SAVE_FILE} gespeichert.")

def load_pois():
    """Lädt POIs aus der JSON-Datei und berechnet ihre Mittelpunkte."""
    global points_of_interest
    if not os.path.exists(POI_FILE):
        print(f"Info: Keine POI-Datei unter {POI_FILE} gefunden. Überspringe.")
        return

    try:
        with open(POI_FILE, 'r') as f:
            data = json.load(f)
        
        for location in data.get("locations", []):
            corners = location.get("corners")
            if not corners: continue
            
            sum_x = sum(c['x'] for c in corners)
            sum_z = sum(c['z'] for c in corners)
            center_x = sum_x / len(corners)
            center_z = sum_z / len(corners)
            
            points_of_interest.append({
                'center_x': center_x,
                'center_z': center_z,
                'display_name': location.get('display_name', 'Unbenannter Ort')
            })
        print(f"Erfolgreich {len(points_of_interest)} POIs aus {POI_FILE} geladen.")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Fehler beim Lesen der POI-Datei {POI_FILE}: {e}")

def poll_telemetry():
    try:
        response = requests.get(TELEMETRY_URL, timeout=0.5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def world_to_screen(x, z):
    screen_x = (x * camera_zoom) + camera_offset.x
    screen_y = (z * camera_zoom) + camera_offset.y
    return int(screen_x), int(screen_y)

def draw_hud():
    if live_truck_data:
        speed_text = f"Geschwindigkeit: {live_truck_data.get('speed', 0):.0f} km/h"
        zoom_text = f"Zoom: {camera_zoom:.2f}"
        speed_surface = font.render(speed_text, True, COLOR_TEXT)
        zoom_surface = font.render(zoom_text, True, COLOR_TEXT)
        screen.blit(speed_surface, (10, 10))
        screen.blit(zoom_surface, (10, 30))
    else:
        status_surface = font.render("Warte auf Verbindung zum Spiel...", True, COLOR_TEXT)
        screen.blit(status_surface, (10, 10))

# --- HAUPTSCHLEIFE ---
load_road_network()
load_pois()
running = True
while running:
    # Event-Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEWHEEL:
            mouse_pos_before_zoom = pygame.math.Vector2(pygame.mouse.get_pos())
            world_pos_before_zoom = (mouse_pos_before_zoom - camera_offset) / camera_zoom
            if event.y > 0: camera_zoom *= 1.25
            else: camera_zoom /= 1.25
            camera_zoom = max(0.01, min(camera_zoom, 5.0))
            world_pos_after_zoom = (mouse_pos_before_zoom - camera_offset) / camera_zoom
            camera_offset += (world_pos_after_zoom - world_pos_before_zoom) * camera_zoom
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_dragging = True
            drag_start_pos = pygame.math.Vector2(event.pos)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            is_dragging = False
            drag_start_pos = None
        if event.type == pygame.MOUSEMOTION and is_dragging:
            drag_end_pos = pygame.math.Vector2(event.pos)
            camera_offset += drag_end_pos - drag_start_pos
            drag_start_pos = drag_end_pos

    # Daten holen und verarbeiten
    data = poll_telemetry()
    if data and data.get('truck') and data.get('game', {}).get('connected'):
        live_truck_data = {
            'x': data['truck']['placement']['x'],
            'z': data['truck']['placement']['z'],
            'heading': data['truck']['placement']['heading'],
            'speed': data['truck']['speed'] * 3.6,
        }
        is_moving = live_truck_data.get('speed', 0) > 5
        if is_moving:
            new_point = (live_truck_data['x'], live_truck_data['z'])
            if not current_road_segment or (new_point[0] != current_road_segment[-1][0] or new_point[1] != current_road_segment[-1][1]):
                current_road_segment.append(new_point)
        else:
            if len(current_road_segment) > 1:
                road_network.append(current_road_segment)
            current_road_segment = []
    else:
        live_truck_data = {}

    # Kamera zentrieren
    if live_truck_data and not is_dragging:
        truck_screen_pos = world_to_screen(live_truck_data['x'], live_truck_data['z'])
        center_screen = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        camera_offset.x -= (truck_screen_pos[0] - center_screen[0])
        camera_offset.y -= (truck_screen_pos[1] - center_screen[1])

    # Zeichnen
    screen.fill(COLOR_BACKGROUND)
    for segment in road_network:
        if len(segment) > 1:
            pygame.draw.lines(screen, COLOR_ROAD, False, [world_to_screen(p[0], p[1]) for p in segment], 3)
    if len(current_road_segment) > 1:
        pygame.draw.lines(screen, COLOR_ROAD, False, [world_to_screen(p[0], p[1]) for p in current_road_segment], 3)
    
    mouse_pos = pygame.mouse.get_pos()
    hovered_poi_label = None
    for poi in points_of_interest:
        poi_screen_pos = world_to_screen(poi['center_x'], poi['center_z'])
        pygame.draw.circle(screen, COLOR_POI, poi_screen_pos, 7)
        if math.hypot(poi_screen_pos[0] - mouse_pos[0], poi_screen_pos[1] - mouse_pos[1]) < 10:
            hovered_poi_label = poi['display_name']

    if live_truck_data:
        truck_pos = world_to_screen(live_truck_data['x'], live_truck_data['z'])
        heading_rad = live_truck_data['heading']
        p1 = (truck_pos[0] + 15 * math.cos(heading_rad), truck_pos[1] + 15 * math.sin(heading_rad))
        p2 = (truck_pos[0] + 8 * math.cos(heading_rad + 2.5), truck_pos[1] + 8 * math.sin(heading_rad + 2.5))
        p3 = (truck_pos[0] + 8 * math.cos(heading_rad - 2.5), truck_pos[1] + 8 * math.sin(heading_rad - 2.5))
        pygame.draw.polygon(screen, COLOR_TRUCK, [p1, p2, p3])
        pygame.draw.circle(screen, COLOR_TRUCK, truck_pos, 5)

    draw_hud()
    if hovered_poi_label:
        label_surface = font_poi.render(hovered_poi_label, True, COLOR_TEXT)
        label_rect = label_surface.get_rect(center=(mouse_pos[0], mouse_pos[1] - 25))
        bg_rect = label_rect.inflate(10, 5)
        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surface.fill(COLOR_POI_LABEL_BG)
        screen.blit(bg_surface, bg_rect)
        screen.blit(label_surface, label_rect)

    pygame.display.flip()
    clock.tick(FPS)

# --- Aufräumen ---
save_road_network()
pygame.quit()