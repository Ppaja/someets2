# src/ui/phone_ui_lieferdienst.py
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
import time
import threading
import keyboard
import json
import os
import requests
import difflib
import re
from PIL import Image, ImageTk
import pygame
import math

# Lokale Imports
from src.config import (
    PHONE_WIDTH, PHONE_HEIGHT, PHONE_MESSAGE_FILE, DELIVERY_DATA_FILE,
    PROFILE_PATH, TELEMETRY_URL, DATA_DIR
)
from src.actions.communication import send_message
from src.actions.job_actions import process_job_request_async
from src.game_integration.ets2_savegame_parser import SavegameParser
from src.utils.location import get_current_coordinates, get_nearest_city_from_db, load_city_database
from src.utils.translation import get_pretty_city_name

class NaviMap:
    def __init__(self):
        self.road_network = []
        self.points_of_interest = []
        self.live_truck_data = {}
        self.camera_offset = pygame.math.Vector2(0, 0)
        self.camera_zoom = 0.15
        self.map_surface = None
        self.font = None
        self.is_initialized = False

        # Farben
        self.COLOR_BACKGROUND = (28, 28, 30) # #1c1c1e
        self.COLOR_ROAD = (100, 100, 100)
        self.COLOR_TRUCK = (0, 150, 255)
        self.COLOR_POI = (255, 190, 0)
        self.COLOR_PICKUP = (52, 199, 89) # Grün
        self.COLOR_DELIVERY = (255, 69, 58) # Rot

    def init_pygame(self, width, height):
        if self.is_initialized: return
        pygame.init()
        self.map_surface = pygame.Surface((width, height))
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.load_road_network()
        self.load_pois()
        self.is_initialized = True
        print("✅ NaviMap initialisiert.")

    def load_road_network(self):
        road_file = DATA_DIR.parent / "cache" / "road_network.json"
        if road_file.exists():
            try:
                with open(road_file, 'r') as f:
                    self.road_network = json.load(f)
            except json.JSONDecodeError:
                self.road_network = []

    def load_pois(self):
        poi_file = DATA_DIR / "locations.json"
        if poi_file.exists():
            with open(poi_file, 'r') as f: data = json.load(f)
            for loc in data.get("locations", []):
                if not loc.get("corners"): continue
                center_x = sum(c['x'] for c in loc["corners"]) / len(loc["corners"])
                center_z = sum(c['z'] for c in loc["corners"]) / len(loc["corners"])
                self.points_of_interest.append({
                    'x': center_x, 'z': center_z, 'name': loc['name'],
                    'display_name': loc.get('display_name', 'Unbenannter Ort')
                })

    def world_to_screen(self, x, z):
        screen_x = (x * self.camera_zoom) + self.camera_offset.x
        screen_y = (z * self.camera_zoom) + self.camera_offset.y
        return int(screen_x), int(screen_y)

    def set_view_to_order(self, pickup_coords, delivery_coords):
        if not self.is_initialized: return
        
        center_x = (pickup_coords['x'] + delivery_coords['x']) / 2
        center_z = (pickup_coords['z'] + delivery_coords['z']) / 2

        dist_x = abs(pickup_coords['x'] - delivery_coords['x'])
        dist_z = abs(pickup_coords['z'] - delivery_coords['z'])
        
        map_width, map_height = self.map_surface.get_size()
        
        zoom_x = (map_width * 0.8) / dist_x if dist_x > 0 else 1
        zoom_y = (map_height * 0.8) / dist_z if dist_z > 0 else 1

        self.camera_zoom = min(zoom_x, zoom_y, 0.2)

        self.camera_offset.x = map_width / 2 - (center_x * self.camera_zoom)
        self.camera_offset.y = map_height / 2 - (center_z * self.camera_zoom)

    def update_truck_position(self, truck_data):
        if truck_data and 'placement' in truck_data:
            self.live_truck_data = {
                'x': truck_data['placement']['x'],
                'z': truck_data['placement']['z'],
                'heading': truck_data['placement']['heading'],
            }

    def draw(self, pickup_coords=None, delivery_coords=None):
        if not self.is_initialized: return None
        
        self.map_surface.fill(self.COLOR_BACKGROUND)

        for segment in self.road_network:
            if len(segment) > 1:
                pygame.draw.lines(self.map_surface, self.COLOR_ROAD, False, [self.world_to_screen(p[0], p[1]) for p in segment], 2)

        if pickup_coords:
            pos = self.world_to_screen(pickup_coords['x'], pickup_coords['z'])
            pygame.draw.circle(self.map_surface, self.COLOR_PICKUP, pos, 8, 3)
        if delivery_coords:
            pos = self.world_to_screen(delivery_coords['x'], delivery_coords['z'])
            pygame.draw.circle(self.map_surface, self.COLOR_DELIVERY, pos, 8, 3)

        if self.live_truck_data:
            map_width, map_height = self.map_surface.get_size()
            truck_pos = self.world_to_screen(self.live_truck_data['x'], self.live_truck_data['z'])

            # Prüfen, ob der Spieler auf der Karte sichtbar ist
            is_on_screen = (0 <= truck_pos[0] <= map_width) and (0 <= truck_pos[1] <= map_height)

            if is_on_screen:
                # Wenn sichtbar: Zeichne den normalen Pfeil
                heading_rad = self.live_truck_data['heading']
                p1 = (truck_pos[0] + 12 * math.cos(heading_rad), truck_pos[1] + 12 * math.sin(heading_rad))
                p2 = (truck_pos[0] + 7 * math.cos(heading_rad + 2.5), truck_pos[1] + 7 * math.sin(heading_rad + 2.5))
                p3 = (truck_pos[0] + 7 * math.cos(heading_rad - 2.5), truck_pos[1] + 7 * math.sin(heading_rad - 2.5))
                pygame.draw.polygon(self.map_surface, self.COLOR_TRUCK, [p1, p2, p3])
                pygame.draw.circle(self.map_surface, self.COLOR_TRUCK, truck_pos, 4)
            else:
                # Wenn nicht sichtbar: Klemme die Position an den Rand und zeichne einen Punkt
                clamped_x = max(5, min(truck_pos[0], map_width - 5))
                clamped_y = max(5, min(truck_pos[1], map_height - 5))
                
                # Zeichne einen äußeren Kreis als Umrandung und einen inneren als Punkt
                pygame.draw.circle(self.map_surface, (255, 255, 255), (clamped_x, clamped_y), 8, 2) # Weiße Umrandung
                pygame.draw.circle(self.map_surface, self.COLOR_TRUCK, (clamped_x, clamped_y), 6) # Blauer Punkt

        return self.map_surface
    
class PhoneOverlayLieferdienst:
    def __init__(self, master, delivery_manager):
        self.window = tk.Toplevel(master)
        self.window.overrideredirect(True)
        self.window.wm_attributes('-topmost', True)
        
        self.manager = delivery_manager
        self.visible = False
        self.animation_running = False
        self.current_screen = "home"
        self.selected_index = 0
        
        self.messages = []
        self.current_conversation = None
        self.last_message_check = 0
        self.last_ingame_time_str = "00:00"
        
        self.image_references = []
        self.delivery_data = {"stats": {}, "history": []}
        self.available_orders = []
        self.is_map_drawing = False
        
        self.setup_window()
        self.city_database = load_city_database()
        self.create_ui()
        self.load_messages()
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_messages, daemon=True)
        self.monitor_thread.start()
        
        self.update_loop()

    def rgb_to_hex(self, rgb):
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def setup_window(self):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.target_x = screen_width - PHONE_WIDTH - 30
        self.target_y = screen_height - PHONE_HEIGHT - 50
        self.hidden_x = screen_width + 50
        self.window.geometry(f"{PHONE_WIDTH}x{PHONE_HEIGHT}+{self.hidden_x}+{self.target_y}")
        self.window.configure(bg='#1a1a1a')

    def create_ui(self):
        self.phone_body = tk.Frame(self.window, bg='#1a1a1a', bd=0)
        self.phone_body.pack(fill='both', expand=True, padx=3, pady=3)
        self.phone_frame = tk.Frame(self.phone_body, bg='#000000', bd=0, relief='flat')
        self.phone_frame.pack(fill='both', expand=True, padx=4, pady=8)
        
        self.create_notch()
        self._create_status_bar()
        
        self.screen_frame = tk.Frame(self.phone_frame, bg='#000000')
        self.screen_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        self.create_home_indicator()
        
        self.navi_map = NaviMap()

        self.screens = {
            "home": self._create_home_screen(),
            "messages": self._create_messages_screen(),
            "message_detail": self._create_message_detail_screen(),
            "city_selection": self._create_city_selection_screen(),
            "browser_home": self._create_browser_home_screen(),
            "police_login": self._create_police_login_screen(),
            "police_database": self._create_police_database_screen(),
            "delivery_dashboard": self._create_delivery_dashboard_screen(),
            "delivery_order_detail": self._create_delivery_order_detail_screen(),
        }
        self.show_screen("home")

    def create_notch(self):
        notch_frame = tk.Frame(self.phone_frame, bg='#000000', height=8)
        notch_frame.pack(fill='x')
        notch_frame.pack_propagate(False)
        island = tk.Frame(notch_frame, bg='#1c1c1e', height=6, width=120)
        island.place(relx=0.5, rely=0.5, anchor='center')

    def _create_status_bar(self):
        status_bar = tk.Frame(self.phone_frame, bg='#000000', height=35)
        status_bar.pack(fill='x', pady=(2, 0))
        status_bar.pack_propagate(False)
        self.time_label = tk.Label(status_bar, text="00:00", bg='#000000', fg='#ffffff', font=('SF Pro Display', 16, 'bold'))
        self.time_label.pack(side='left', padx=20, pady=8)
        status_icons = tk.Frame(status_bar, bg='#000000')
        status_icons.pack(side='right', padx=20, pady=8)
        battery_label = tk.Label(status_icons, text="🔋", bg='#000000', fg='#34c759', font=('Apple Color Emoji', 14))
        battery_label.pack(side='right', padx=2)
        signal_label = tk.Label(status_icons, text="📶", bg='#000000', fg='#ffffff', font=('Apple Color Emoji', 14))
        signal_label.pack(side='right', padx=2)

    def create_home_indicator(self):
        indicator_frame = tk.Frame(self.phone_frame, bg='#000000', height=12)
        indicator_frame.pack(side='bottom', fill='x')
        indicator_frame.pack_propagate(False)
        indicator = tk.Frame(indicator_frame, bg='#8e8e93', height=4, width=140)
        indicator.place(relx=0.5, rely=0.5, anchor='center')

    def _create_home_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#000000')
        wallpaper_frame = tk.Frame(screen, bg='#1a1a2e')
        wallpaper_frame.pack(fill='both', expand=True)
        apps_frame = tk.Frame(wallpaper_frame, bg='#1a1a2e')
        apps_frame.pack(expand=True, fill='both', padx=25, pady=40)
        self.apps = [
            {"name": "Messages", "icon": "💬", "color": "#34c759", "screen": "messages"},
            {"name": "Liefer-App", "icon": "🛵", "color": "#ff9500", "screen": "delivery_dashboard"},
            {"name": "Browser", "icon": "🌐", "color": "#007aff", "screen": "browser_home"},
            {"name": "Settings", "icon": "⚙️", "color": "#8e8e93", "screen": None}
        ]
        self.app_buttons = []
        for i, app in enumerate(self.apps):
            row, col = divmod(i, 2)
            container = tk.Frame(apps_frame, bg='#1a1a2e')
            container.grid(row=row, column=col, padx=25, pady=25, sticky='nsew')
            icon_bg = tk.Frame(container, bg=app["color"], width=66, height=66)
            icon_bg.pack()
            icon_bg.pack_propagate(False)
            icon_label = tk.Label(icon_bg, text=app["icon"], bg=app["color"], fg='#ffffff', font=('Apple Color Emoji', 28))
            icon_label.place(relx=0.5, rely=0.5, anchor='center')
            name_label = tk.Label(container, text=app["name"], bg='#1a1a2e', fg='#ffffff', font=('SF Pro Display', 12, 'normal'))
            name_label.pack(pady=(8, 0))
            self.app_buttons.append({"frame": container, "app": app})
        for i in range(2): apps_frame.grid_columnconfigure(i, weight=1)
        return screen

    def _create_messages_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#000000')
        header = tk.Frame(screen, bg='#1c1c1e', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        title_label = tk.Label(header, text="Messages", bg='#1c1c1e', fg='#ffffff', font=('SF Pro Display', 20, 'bold'))
        title_label.place(relx=0.5, rely=0.5, anchor='center')
        self.messages_list_frame = tk.Frame(screen, bg='#000000')
        self.messages_list_frame.pack(fill='both', expand=True)
        return screen

    def _create_message_detail_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#000000')
        header = tk.Frame(screen, bg='#1c1c1e', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        back_btn = tk.Label(header, text="‹", bg='#1c1c1e', fg='#007aff', font=('SF Pro Display', 24, 'normal'))
        back_btn.place(x=20, y=20)
        self.contact_name_label = tk.Label(header, text="", bg='#1c1c1e', fg='#ffffff', font=('SF Pro Display', 18, 'bold'))
        self.contact_name_label.place(relx=0.5, rely=0.5, anchor='center')
        self.messages_container = tk.Canvas(screen, bg='#000000', highlightthickness=0)
        self.messages_container.pack(fill='both', expand=True, padx=8)
        self.messages_frame = tk.Frame(self.messages_container, bg='#000000')
        self.messages_container.create_window((0, 0), window=self.messages_frame, anchor='nw')
        return screen

    def _create_city_selection_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#000000')
        header = tk.Frame(screen, bg='#1c1c1e', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        back_btn = tk.Label(header, text="‹", bg='#1c1c1e', fg='#007aff', font=('SF Pro Display', 24))
        back_btn.place(x=20, y=15)
        title_label = tk.Label(header, text="Standort auswählen", bg='#1c1c1e', fg='#ffffff', font=('SF Pro Display', 18, 'bold'))
        title_label.place(relx=0.5, rely=0.5, anchor='center')
        self.city_list_canvas = tk.Canvas(screen, bg='#000000', highlightthickness=0)
        self.city_list_canvas.pack(fill='both', expand=True, padx=10, pady=10)
        self.city_list_frame = tk.Frame(self.city_list_canvas, bg='#000000')
        self.city_list_canvas.create_window((0, 0), window=self.city_list_frame, anchor='nw', width=PHONE_WIDTH - 40)
        self.city_list_items = []
        return screen

    def _create_browser_home_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#f2f2f7')
        header = tk.Frame(screen, bg='#f2f2f7', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        url_bar = tk.Frame(header, bg='#ffffff', height=36, bd=1, relief='solid')
        url_bar.pack(pady=12, padx=20, fill='x')
        url_bar.pack_propagate(False)
        url_label = tk.Label(url_bar, text="🔒 Favoriten", bg='#ffffff', fg='#8e8e93', font=('SF Pro Display', 14))
        url_label.pack(side='left', padx=15, pady=8)
        self.bookmarks = [{"name": "Polizei Akten", "icon": "👮", "action": self.open_police_database}]
        self.bookmark_buttons = []
        for i, bookmark in enumerate(self.bookmarks):
            btn_frame = tk.Frame(screen, bg='#ffffff', bd=0, relief='flat')
            btn_frame.pack(pady=8, padx=20, fill='x')
            icon_label = tk.Label(btn_frame, text=bookmark['icon'], font=('Apple Color Emoji', 24), bg='#ffffff')
            icon_label.pack(side='left', padx=20, pady=15)
            name_label = tk.Label(btn_frame, text=bookmark['name'], font=('SF Pro Display', 16, 'normal'), bg='#ffffff', fg='#000000', anchor='w')
            name_label.pack(side='left', fill='x', expand=True, pady=15)
            arrow_label = tk.Label(btn_frame, text="›", font=('SF Pro Display', 18), bg='#ffffff', fg='#c7c7cc')
            arrow_label.pack(side='right', padx=20, pady=15)
            self.bookmark_buttons.append({"frame": btn_frame, "bookmark": bookmark})
        return screen

    def _create_police_login_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#0d1b2a')
        loading_frame = tk.Frame(screen, bg='#0d1b2a')
        loading_frame.pack(expand=True, fill='both')
        logo_label = tk.Label(loading_frame, text="🔐", font=('Apple Color Emoji', 80), bg='#0d1b2a', fg='#ffffff')
        logo_label.pack(pady=(80, 20))
        title_label = tk.Label(loading_frame, text="ZENTRALES\nVERKEHRSREGISTER", font=('SF Pro Display', 16, 'bold'), fg='#ffffff', bg='#0d1b2a', justify='center')
        title_label.pack(pady=(0, 30))
        status_label = tk.Label(loading_frame, text="Verbinde mit sicherem Server...", font=('SF Pro Display', 14), fg='#8e8e93', bg='#0d1b2a')
        status_label.pack(pady=10)
        self.loading_dots = tk.Label(loading_frame, text="●○○", font=('SF Pro Display', 20), fg='#007aff', bg='#0d1b2a')
        self.loading_dots.pack(pady=20)
        return screen

    def _create_police_database_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#f2f2f7')
        header = tk.Frame(screen, bg='#007aff', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        back_btn = tk.Label(header, text="‹", bg='#007aff', fg='#ffffff', font=('SF Pro Display', 24))
        back_btn.place(x=20, y=15)
        title_label = tk.Label(header, text="ZVR - Aktenübersicht", font=('SF Pro Display', 18, 'bold'), fg='#ffffff', bg='#007aff')
        title_label.place(relx=0.5, rely=0.5, anchor='center')
        self.police_summary_frame = tk.Frame(screen, bg='#ffffff', bd=0, relief='flat')
        self.police_summary_frame.pack(fill='x', padx=15, pady=15)
        self.police_records_canvas = tk.Canvas(screen, bg='#f2f2f7', highlightthickness=0)
        self.police_records_canvas.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        self.police_records_frame = tk.Frame(self.police_records_canvas, bg='#f2f2f7')
        self.police_records_canvas.create_window((0, 0), window=self.police_records_frame, anchor='nw')
        self.police_record_items = []
        return screen

    def _create_delivery_dashboard_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#1c1c1e')
        header = tk.Frame(screen, bg='#1c1c1e', height=60); header.pack(fill='x')
        tk.Label(header, text="Liefer-Dashboard", bg='#1c1c1e', fg='#ffffff', font=('SF Pro Display', 20, 'bold')).place(relx=0.5, rely=0.5, anchor='center')
        
        stats_frame = tk.Frame(screen, bg='#2c2c2e'); stats_frame.pack(fill='x', padx=15, pady=10)
        self.earnings_label = tk.Label(stats_frame, text="Gesamtverdienst: 0.00€", bg='#2c2c2e', fg='white', font=('SF Pro Display', 14)); self.earnings_label.pack(anchor='w', padx=10, pady=5)
        self.deliveries_label = tk.Label(stats_frame, text="Erledigte Aufträge: 0", bg='#2c2c2e', fg='white', font=('SF Pro Display', 14)); self.deliveries_label.pack(anchor='w', padx=10, pady=5)

        tk.Label(screen, text="Verfügbare Aufträge", bg='#1c1c1e', fg='#a0a0a0', font=('SF Pro Display', 16, 'bold')).pack(anchor='w', padx=15, pady=(10,5))
        self.order_list_frame = tk.Frame(screen, bg='#1c1c1e')
        self.order_list_frame.pack(fill='both', expand=True, padx=15)
        self.order_list_items = []
        return screen

    def _create_delivery_order_detail_screen(self):
        screen = tk.Frame(self.screen_frame, bg='#1c1c1e')
        header = tk.Frame(screen, bg='#1c1c1e', height=50); header.pack(fill='x')
        tk.Label(header, text="Auftragsdetails", bg='#1c1c1e', fg='white', font=('SF Pro Display', 18, 'bold')).place(relx=0.5, rely=0.5, anchor='center')

        map_frame_width = PHONE_WIDTH - 14
        map_frame_height = 200
        self.map_frame = tk.Frame(screen, width=map_frame_width, height=map_frame_height, bg='black')
        self.map_frame.pack(pady=10)
        self.map_label = tk.Label(self.map_frame, bg='black')
        self.map_label.pack()

        self.window.after(100, lambda: self.navi_map.init_pygame(map_frame_width, map_frame_height))
        os.environ['SDL_WINDOWID'] = str(self.map_frame.winfo_id())
        os.environ['SDL_VIDEODRIVER'] = 'windib'

        self.info_frame = tk.Frame(screen, bg='#2c2c2e')
        self.info_frame.pack(fill='both', expand=True, padx=15, pady=10)
        return screen

    def load_delivery_data(self):
        if DELIVERY_DATA_FILE.exists():
            try:
                with open(DELIVERY_DATA_FILE, 'r', encoding='utf-8') as f:
                    self.delivery_data = json.load(f)
            except json.JSONDecodeError:
                pass
        self.update_dashboard_stats()

    def update_dashboard_stats(self):
        stats = self.delivery_data.get("stats", {})
        if hasattr(self, 'earnings_label'):
            self.earnings_label.config(text=f"Gesamtverdienst: {stats.get('total_earnings', 0.0):.2f}€")
            self.deliveries_label.config(text=f"Erledigte Aufträge: {stats.get('completed_deliveries', 0)}")

    def update_available_orders_list(self, orders):
        self.available_orders = orders
        if self.current_screen != "delivery_dashboard": return

        for item in self.order_list_items: item.destroy()
        self.order_list_items.clear()

        if self.manager.game_state != "IDLE" and self.manager.current_order:
            order = self.manager.current_order
            item_frame = tk.Frame(self.order_list_frame, bg='#2c2c2e')
            item_frame.pack(fill='x', pady=5)
            tk.Label(item_frame, text=f"AKTIV: Lieferung für {order['customer_display_name']}", fg='#ff9500', bg='#2c2c2e', font=('SF Pro Display', 14, 'bold')).pack(pady=5)
            tk.Label(item_frame, text="Details ansehen (Enter)", fg='white', bg='#2c2c2e').pack(pady=5)
            self.order_list_items.append(item_frame)
        else:
            for i, order in enumerate(self.available_orders):
                item_frame = tk.Frame(self.order_list_frame, bg='#2c2c2e')
                item_frame.pack(fill='x', pady=5)
                tk.Label(item_frame, text=f"Abholung: {order['restaurant_display_name']}", fg='white', bg='#2c2c2e', anchor='w').pack(fill='x', padx=10)
                tk.Label(item_frame, text=f"Ziel: {order['customer_display_name']}", fg='white', bg='#2c2c2e', anchor='w').pack(fill='x', padx=10)
                tk.Label(item_frame, text=f"Belohnung: ca. {order['cost'] * 1.25:.2f}€", fg='#34c759', bg='#2c2c2e', anchor='w').pack(fill='x', padx=10, pady=(0,5))
                self.order_list_items.append(item_frame)
        
        self.update_selection_highlight()

    def show_screen(self, screen_name):
        for screen in self.screens.values():
            screen.pack_forget()
        
        self.screens[screen_name].pack(fill='both', expand=True)
        self.current_screen = screen_name
        self.selected_index = 0
        
        if screen_name == "messages": self.update_messages_list()
        elif screen_name == "message_detail": self.show_conversation()
        elif screen_name == "city_selection": self.update_city_list()
        elif screen_name == "police_login": 
            self.animate_loading_dots()
            self.window.after(2500, self.load_and_show_police_data)
        elif screen_name == "delivery_dashboard":
            self.stop_map_drawing()
            self.load_delivery_data()
            self.update_available_orders_list(self.manager.available_orders)
        elif screen_name == "delivery_order_detail":
            self.update_order_detail_view()
            self.start_map_drawing()
        else:
            self.stop_map_drawing()
        
        self.update_selection_highlight()

    def start_map_drawing(self):
        self.is_map_drawing = True
        self.draw_map_loop()

    def stop_map_drawing(self):
        self.is_map_drawing = False

    def draw_map_loop(self):
        if not self.is_map_drawing or not self.visible or not self.navi_map.is_initialized:
            return

        order = self.manager.current_order
        pickup_coords, delivery_coords = None, None
        if order:
            pickup_loc = self.manager.all_locations.get(order['restaurant_name'])
            delivery_loc = self.manager.all_locations.get(order['customer_name'])
            if pickup_loc and delivery_loc:
                pickup_coords = {'x': sum(c['x'] for c in pickup_loc['corners'])/len(pickup_loc['corners']), 'z': sum(c['z'] for c in pickup_loc['corners'])/len(pickup_loc['corners'])}
                delivery_coords = {'x': sum(c['x'] for c in delivery_loc['corners'])/len(delivery_loc['corners']), 'z': sum(c['z'] for c in delivery_loc['corners'])/len(delivery_loc['corners'])}

        pygame_surface = self.navi_map.draw(pickup_coords, delivery_coords)
        if pygame_surface:
            img_data = pygame.image.tostring(pygame_surface, 'RGB')
            img = Image.frombytes('RGB', pygame_surface.get_size(), img_data)
            photo = ImageTk.PhotoImage(image=img)
            self.map_label.config(image=photo)
            self.map_label.image = photo

        self.window.after(50, self.draw_map_loop)

    def update_navi_map_truck(self, telemetry_data):
        if self.navi_map.is_initialized and telemetry_data and telemetry_data.get("truck"):
            self.navi_map.update_truck_position(telemetry_data["truck"])

    def update_order_detail_view(self):
        for w in self.info_frame.winfo_children(): w.destroy()
        order = self.manager.current_order
        if not order: return

        state = self.manager.game_state
        if state == "WAITING_FOR_PICKUP":
            title = f"Abholen bei: {order['restaurant_display_name']}"
            color = self.rgb_to_hex(self.navi_map.COLOR_PICKUP)
        elif state == "WAITING_FOR_DELIVERY":
            title = f"Liefern an: {order['customer_display_name']}"
            color = self.rgb_to_hex(self.navi_map.COLOR_DELIVERY)
        else:
            title = "Kein aktiver Auftrag"; color = "white"

        tk.Label(self.info_frame, text=title, font=('SF Pro Display', 16, 'bold'), fg=color, bg='#2c2c2e').pack(pady=5)
        item_list_str = "\n".join([f"• {qty}x {name}" for name, qty in order['items'].items()])
        tk.Label(self.info_frame, text=item_list_str, justify='left', fg='white', bg='#2c2c2e').pack(pady=5)

        pickup_loc = self.manager.all_locations.get(order['restaurant_name'])
        delivery_loc = self.manager.all_locations.get(order['customer_name'])
        if pickup_loc and delivery_loc:
            pickup_coords = {'x': sum(c['x'] for c in pickup_loc['corners'])/len(pickup_loc['corners']), 'z': sum(c['z'] for c in pickup_loc['corners'])/len(pickup_loc['corners'])}
            delivery_coords = {'x': sum(c['x'] for c in delivery_loc['corners'])/len(delivery_loc['corners']), 'z': sum(c['z'] for c in delivery_loc['corners'])/len(delivery_loc['corners'])}
            self.navi_map.set_view_to_order(pickup_coords, delivery_coords)

    def setup_keyboard_hooks(self, enable):
        hooks = {'up': self.on_key_up, 'down': self.on_key_down, 'left': self.on_key_left,
                 'right': self.on_key_right, 'enter': self.on_key_enter, 'backspace': self.on_key_backspace}
        for key, func in hooks.items():
            try:
                if enable: keyboard.on_press_key(key, func, suppress=True)
                else: keyboard.unhook_key(key)
            except (KeyError, AttributeError): pass

    def on_key_up(self, e): self._navigate(-1)
    def on_key_down(self, e): self._navigate(1)
    def on_key_left(self, e): self._navigate(-1, horizontal=True)
    def on_key_right(self, e): self._navigate(1, horizontal=True)

    def _navigate(self, direction, horizontal=False):
        if self.current_screen == "message_detail":
            self.messages_container.yview_scroll(direction, "units")
            return

        if self.current_screen == "home":
            if horizontal:
                if self.selected_index % 2 == 0 and direction == 1: self.selected_index += 1
                elif self.selected_index % 2 != 0 and direction == -1: self.selected_index -= 1
            else:
                new_index = self.selected_index + direction * 2
                if 0 <= new_index < len(self.apps): self.selected_index = new_index
        else:
            items_len = 0
            if self.current_screen == 'messages': items_len = len(getattr(self, 'message_items', []))
            elif self.current_screen == 'city_selection': items_len = len(self.city_list_items)
            elif self.current_screen == 'browser_home': items_len = len(self.bookmark_buttons)
            elif self.current_screen == 'police_database': items_len = len(self.police_record_items)
            elif self.current_screen == 'delivery_dashboard': items_len = len(self.order_list_items)
            
            if items_len > 0: self.selected_index = (self.selected_index + direction) % items_len
        self.update_selection_highlight()

    def on_key_enter(self, e):
        # NEU: Logik für die Hilfe-Anfrage
        is_delivery_chat = (
            self.current_screen == "message_detail" and
            self.manager and self.manager.current_order and
            self.current_conversation and
            self.current_conversation['sender'] == self.manager.current_order['customer_display_name']
        )
        
        if is_delivery_chat:
            self.manager.ask_for_help()
            return # Verhindert, dass andere Enter-Aktionen ausgeführt werden

        # Bisherige Logik
        if self.current_screen == "home":
            if self.selected_index < len(self.apps):
                if (screen := self.apps[self.selected_index]["screen"]): self.show_screen(screen)
        elif self.current_screen == "messages" and self.selected_index < len(self.messages):
            self.current_conversation = self.messages[self.selected_index]
            self.show_screen("message_detail")
        elif self.current_screen == "message_detail" and self.current_conversation.get("sender") == "Dispo":
            self.show_screen("city_selection")
        elif self.current_screen == "city_selection" and self.selected_index < len(self.available_cities):
            city = self.available_cities[self.selected_index]
            send_message("Dispo", f"Bin in {city.capitalize()}, brauche neuen Auftrag.", sent_by_me=True)
            process_job_request_async(city)
            self.show_screen("message_detail")
        elif self.current_screen == "browser_home" and self.selected_index < len(self.bookmarks):
            self.bookmarks[self.selected_index]['action']()
        elif self.current_screen == "delivery_dashboard":
            if self.manager.game_state != "IDLE":
                self.show_screen("delivery_order_detail")
            elif self.selected_index < len(self.available_orders):
                order_to_accept = self.available_orders[self.selected_index]
                self.manager.accept_order(order_to_accept['id'])

    def on_key_backspace(self, e):
        back_map = {
            "delivery_order_detail": "delivery_dashboard",
            "delivery_dashboard": "home",
            "police_database": "browser_home", "police_login": "browser_home",
            "browser_home": "home", "city_selection": "message_detail",
            "message_detail": "messages", "messages": "home"
        }
        if target_screen := back_map.get(self.current_screen): self.show_screen(target_screen)
        else: self.toggle_visibility()

    def update_selection_highlight(self):
        if self.current_screen == "home":
            for i, btn in enumerate(self.app_buttons):
                is_selected = (i == self.selected_index)
                btn["frame"].config(bg='#2c2c2e' if is_selected else '#1a1a2e')
                for child in btn["frame"].winfo_children():
                    if isinstance(child, tk.Frame):
                        child.config(highlightbackground='#007aff' if is_selected else '#1a1a2e', highlightthickness=2 if is_selected else 0)
        elif self.current_screen == "messages" and hasattr(self, 'message_items'):
            for i, item in enumerate(self.message_items):
                bg_color = '#1c1c1e' if i == self.selected_index else '#000000'
                item["frame"].config(bg=bg_color, highlightbackground='#007aff', highlightthickness=(1 if i == self.selected_index else 0))
                for child in item["frame"].winfo_children():
                    if child.cget('bg') not in ['#3a3a3c', '#007aff']: child.config(bg=bg_color)
        elif self.current_screen == "delivery_dashboard":
            for i, item_frame in enumerate(self.order_list_items):
                is_selected = (i == self.selected_index)
                bg_color = '#48484a' if is_selected else '#2c2c2e'
                item_frame.config(bg=bg_color)
                for child in item_frame.winfo_children():
                    child.config(bg=bg_color)

    def load_messages(self):
        try:
            if PHONE_MESSAGE_FILE.exists():
                with open(PHONE_MESSAGE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = data.get('conversations', [])
                    self.messages.sort(key=lambda c: c['messages'][-1]['timestamp'], reverse=True)
        except Exception as e:
            print(f"Fehler beim Laden der Nachrichten: {e}")

    def monitor_messages(self):
        while self.monitoring:
            try:
                if PHONE_MESSAGE_FILE.exists() and os.path.getmtime(PHONE_MESSAGE_FILE) != self.last_message_check:
                    self.last_message_check = os.path.getmtime(PHONE_MESSAGE_FILE)
                    self.load_messages()
                    if self.visible: self.window.after(0, self.refresh_current_view)
            except Exception as e: print(f"Message monitoring Fehler: {e}")
            time.sleep(1)

    def refresh_current_view(self):
        if self.current_screen == "messages": self.update_messages_list()
        elif self.current_screen == "message_detail" and self.current_conversation:
            sender = self.current_conversation['sender']
            self.current_conversation = next((c for c in self.messages if c['sender'] == sender), None)
            self.show_conversation()

    def update_ingame_time(self):
        try:
            response = requests.get(TELEMETRY_URL, timeout=0.5)
            if response.ok and (time_str := response.json().get("game", {}).get("time")):
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                self.last_ingame_time_str = f"{dt.hour:02d}:{dt.minute:02d}"
        except requests.RequestException: pass
        self.time_label.config(text=self.last_ingame_time_str)

    def update_loop(self):
        self.update_ingame_time()
        self.window.after(1000, self.update_loop)

    def toggle_visibility(self):
        if self.animation_running: return
        self.visible = not self.visible
        self.setup_keyboard_hooks(self.visible)
        if self.visible and self.current_screen == "delivery_order_detail":
            self.start_map_drawing()
        else:
            self.stop_map_drawing()
        start_x, end_x = (self.target_x, self.hidden_x) if not self.visible else (self.hidden_x, self.target_x)
        self.animate_slide(start_x, end_x)

    def is_visible(self): return self.visible

    def animate_slide(self, start_x, end_x):
        self.animation_running = True
        start_time = time.time()
        duration = 0.35
        def animate():
            progress = min((time.time() - start_time) / duration, 1.0)
            eased = 1 - (1 - progress) ** 2.5
            current_x = start_x + (end_x - start_x) * eased
            self.window.geometry(f"{PHONE_WIDTH}x{PHONE_HEIGHT}+{int(current_x)}+{self.target_y}")
            if progress < 1.0: self.window.after(12, animate)
            else: self.animation_running = False
        animate()

    def close(self):
        self.monitoring = False
        self.stop_map_drawing()
        if self.navi_map.is_initialized:
            pygame.quit()
        try:
            self.setup_keyboard_hooks(False)
        except:
            pass
            
    def update_messages_list(self):
        for w in self.messages_list_frame.winfo_children(): w.destroy()
        self.message_items = []
        for conv in self.messages:
            item_frame = tk.Frame(self.messages_list_frame, bg='#000000', height=80)
            item_frame.pack(fill='x', pady=1, padx=15)
            item_frame.pack_propagate(False)
            avatar_frame = tk.Frame(item_frame, bg='#3a3a3c', width=55, height=55)
            avatar_frame.place(x=0, y=12)
            avatar_frame.pack_propagate(False)
            avatar_label = tk.Label(avatar_frame, text=conv["sender"][0].upper(), bg='#3a3a3c', fg='#ffffff', font=('SF Pro Display', 22, 'bold'))
            avatar_label.place(relx=0.5, rely=0.5, anchor='center')
            name_label = tk.Label(item_frame, text=conv["sender"], bg='#000000', fg='#ffffff', font=('SF Pro Display', 17, 'bold'), anchor='w')
            name_label.place(x=70, y=15)
            last_msg_text = conv["messages"][-1]["text"]
            preview = (last_msg_text[:30] + '...') if len(last_msg_text) > 30 else last_msg_text
            preview_label = tk.Label(item_frame, text=preview, bg='#000000', fg='#8e8e93', font=('SF Pro Display', 15), anchor='w')
            preview_label.place(x=70, y=40)
            time_label = tk.Label(item_frame, text=conv["messages"][-1].get("ingame_time", ""), bg='#000000', fg='#8e8e93', font=('SF Pro Display', 13), anchor='e')
            time_label.place(x=200, y=15, width=80)
            if not conv.get("read", True):
                unread_dot = tk.Frame(item_frame, bg='#007aff', width=8, height=8)
                unread_dot.place(x=285, y=40)
            chevron_label = tk.Label(item_frame, text="›", bg='#000000', fg='#3a3a3c', font=('SF Pro Display', 20))
            chevron_label.place(x=290, y=25)
            self.message_items.append({"frame": item_frame, "conversation": conv})
        self.update_selection_highlight()

    def show_conversation(self):
        if not self.current_conversation: return
        self.contact_name_label.config(text=self.current_conversation["sender"])
        for w in self.messages_frame.winfo_children(): w.destroy()
        self.image_references.clear()
        for i, msg in enumerate(self.current_conversation["messages"]):
            is_sent = msg.get("sent_by_me", False)
            msg_container = tk.Frame(self.messages_frame, bg='#000000')
            msg_container.pack(fill='x', pady=3)
            max_width = int(PHONE_WIDTH * 0.7)
            image_match = re.match(r"\[Bild gesendet: (.*?)\]", msg["text"])
            if image_match:
                image_path = image_match.group(1).strip()
                try:
                    img = Image.open(image_path)
                    img.thumbnail((180, 180))
                    photo = ImageTk.PhotoImage(img)
                    img_label = tk.Label(msg_container, image=photo, bg='#000000', bd=0)
                    img_label.image = photo
                    self.image_references.append(photo)
                    if is_sent: img_label.pack(side='right', padx=(50, 15))
                    else: img_label.pack(side='left', padx=(15, 50))
                except FileNotFoundError:
                    error_text = f"Bild nicht gefunden:\n{os.path.basename(image_path)}"
                    bubble = tk.Label(msg_container, text=error_text, bg="#ff3b30", fg='white', font=('SF Pro Display', 14), wraplength=max_width, justify='left', padx=16, pady=12, bd=0)
                    if is_sent: bubble.pack(side='right', padx=(50, 15))
                    else: bubble.pack(side='left', padx=(15, 50))
            else:
                bubble_bg = '#007aff' if is_sent else '#3a3a3c'
                bubble = tk.Label(msg_container, text=msg["text"], bg=bubble_bg, fg='#ffffff', font=('SF Pro Display', 16), wraplength=max_width, justify='left', padx=16, pady=12, bd=0)
                if is_sent: bubble.pack(side='right', padx=(50, 15))
                else: bubble.pack(side='left', padx=(15, 50))
            if i == len(self.current_conversation["messages"]) - 1 and (time_text := msg.get("ingame_time", "")):
                time_label = tk.Label(msg_container, text=time_text, bg='#000000', fg='#8e8e93', font=('SF Pro Display', 12))
                if is_sent: time_label.pack(side='right', padx=(0, 20), pady=(2, 0))
                else: time_label.pack(side='left', padx=(20, 0), pady=(2, 0))
        self.messages_frame.update_idletasks()
        self.messages_container.config(scrollregion=self.messages_container.bbox("all"))
        self.messages_container.yview_moveto(1.0)

    def update_city_list(self):
        for item in self.city_list_items: item.destroy()
        self.city_list_items.clear()
        try:
            parser = SavegameParser(profile_path=PROFILE_PATH)
            cities_with_jobs_raw = parser.get_available_cities() or []
        except Exception as e:
            self.available_cities = [f"Fehler: {e}"]
            return
        pretty_cities_with_jobs = sorted(list(set([get_pretty_city_name(raw_name) for raw_name in cities_with_jobs_raw])))
        player_coords = get_current_coordinates()
        nearest_city_name = get_nearest_city_from_db(player_coords, self.city_database)
        final_city_list = []
        if nearest_city_name:
            matching_city_in_list = next((city for city in pretty_cities_with_jobs if city.lower() == nearest_city_name.lower()), None)
            if matching_city_in_list:
                final_city_list.append(matching_city_in_list)
                pretty_cities_with_jobs.remove(matching_city_in_list)
        final_city_list.extend(pretty_cities_with_jobs)
        self.available_cities = final_city_list
        for city_name in self.available_cities:
            city_frame = tk.Frame(self.city_list_frame, bg='#000000', height=50)
            city_frame.pack(fill='x', pady=1)
            city_frame.pack_propagate(False)
            icon_text = "📍"
            if nearest_city_name and city_name.lower() == nearest_city_name.lower():
                icon_text = "🛰️"
            icon_label = tk.Label(city_frame, text=icon_text, bg='#000000', fg='#ffffff', font=('Apple Color Emoji', 18))
            icon_label.place(x=20, y=15)
            city_label = tk.Label(city_frame, text=city_name, bg='#000000', fg='#ffffff', font=('SF Pro Display', 17), anchor='w')
            city_label.place(x=60, y=15)
            chevron_label = tk.Label(city_frame, text="›", bg='#000000', fg='#3a3a3c', font=('SF Pro Display', 20))
            chevron_label.place(x=270, y=10)
            self.city_list_items.append(city_frame)
        self.city_list_frame.update_idletasks()
        self.city_list_canvas.config(scrollregion=self.city_list_canvas.bbox("all"))
        self.update_selection_highlight()

    def open_police_database(self):
        self.show_screen("police_login")

    def animate_loading_dots(self):
        if self.current_screen != "police_login": return
        dots_states = ["●○○", "○●○", "○○●", "●●○", "●●●"]
        current_state = 0
        def update_dots():
            nonlocal current_state
            if self.current_screen == "police_login":
                self.loading_dots.config(text=dots_states[current_state])
                current_state = (current_state + 1) % len(dots_states)
                self.window.after(300, update_dots)
        update_dots()

    def load_and_show_police_data(self):
        try:
            parser = SavegameParser(profile_path=PROFILE_PATH)
            self.police_data = parser.get_police_offence_log()
        except Exception as e:
            self.police_data = None
        self.populate_police_database_screen()
        self.show_screen("police_database")

    def populate_police_database_screen(self):
        for w in self.police_summary_frame.winfo_children(): w.destroy()
        for item in self.police_record_items: item['frame'].destroy()
        self.police_record_items.clear()
        if not self.police_data: 
            error_label = tk.Label(self.police_summary_frame, text="Keine Daten verfügbar", font=('SF Pro Display', 13), bg='#ffffff', fg='#8e8e93')
            error_label.pack(pady=20)
            return
        summary_header = tk.Label(self.police_summary_frame, text="📊 Übersicht", font=('SF Pro Display', 15, 'bold'), bg='#ffffff', fg='#000000')
        summary_header.pack(anchor='w', padx=15, pady=(12, 8))
        summary = self.police_data.get('summary', {})
        stats_frame = tk.Frame(self.police_summary_frame, bg='#ffffff')
        stats_frame.pack(fill='x', padx=15, pady=(0, 12))
        fines_label = tk.Label(stats_frame, text=f"💰 Gesamtschaden: {summary.get('total_fines', 0)} €", font=('SF Pro Display', 11, 'bold'), bg='#ffffff', fg='#ff3b30')
        fines_label.pack(anchor='w', pady=1)
        crash_label = tk.Label(stats_frame, text=f"🚗 Aktenkundige Unfälle: {summary.get('ai_crash_count', 0)}", font=('SF Pro Display', 11, 'bold'), bg='#ffffff', fg='#ff9500')
        crash_label.pack(anchor='w', pady=1)
        for offence in self.police_data.get('offences', []):
            item_frame = tk.Frame(self.police_records_frame, bg='#ffffff', bd=0, relief='flat')
            item_frame.pack(fill='x', pady=5, padx=0)
            content_frame = tk.Frame(item_frame, bg='#ffffff')
            content_frame.pack(fill='x', padx=20, pady=15)
            type_label = tk.Label(content_frame, text=f"⚠️ {offence['type_human']}", font=('SF Pro Display', 12, 'bold'), bg='#ffffff', fg='#000000')
            type_label.pack(anchor='w')
            fine_label = tk.Label(content_frame, text=f"Strafe: -{offence['fine']} €", font=('SF Pro Display', 11), bg='#ffffff', fg='#ff3b30')
            fine_label.pack(anchor='w', pady=(2, 0))
            time_label = tk.Label(content_frame, text=f"🕐 {offence['formatted_time']}", font=('SF Pro Display', 11), bg='#ffffff', fg='#8e8e93')
            time_label.pack(anchor='w', pady=(2, 0))
            separator = tk.Frame(item_frame, bg='#e5e5ea', height=1)
            separator.pack(fill='x', side='bottom')
            self.police_record_items.append({'frame': item_frame, 'data': offence})
        self.police_records_frame.update_idletasks()
        self.police_records_canvas.config(scrollregion=self.police_records_canvas.bbox("all"))