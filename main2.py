# main2.py
import tkinter as tk
from tkinter import messagebox
import threading
import time
import json
import random
import requests
from pathlib import Path
import os
import sys
import keyboard
from dotenv import load_dotenv
from collections import Counter
import uuid

load_dotenv()

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / 'src'))

try:
    from ui.phone_ui_lieferdienst import PhoneOverlayLieferdienst
    from ui.order_menu_ui import OrderMenuOverlay
    from utils.geometry import is_point_in_polygon
    from src.startTelemetry import start_telemetry_server
    from actions.communication import send_message, create_sample_files_if_missing
    from config import DELIVERY_DATA_FILE, TELEMETRY_URL
except ImportError as e:
    print(f"FEHLER: Konnte eine benötigte Komponente nicht importieren: {e}")
    sys.exit(1)

# --- Konstanten ---
LOCATIONS_FILE = project_root / "data" / "locations.json"
POLL_INTERVAL_S = 1.0
PROFIT_MARGIN = 1.25

class DeliveryManager:
    def __init__(self, phone_ui_instance):
        self.phone = phone_ui_instance
        self.locations_data = self._load_locations()
        self.all_locations = {loc['name']: loc for loc in self.locations_data['locations']}
        
        self.player_wallet = 100.00
        self.player_inventory = None
        
        self.current_order = None
        self.available_orders = []
        self.game_state = "IDLE"
        
        self.last_engine_state = False
        self.order_menu_window = None
        self.current_location_name = None

        self.delivery_data = self.load_delivery_data()
        if self.phone:
            self.phone.delivery_data = self.delivery_data
            self.phone.update_dashboard_stats()

        print("✅ DeliveryManager initialisiert.")

    def load_delivery_data(self):
        if DELIVERY_DATA_FILE.exists():
            with open(DELIVERY_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"stats": {"total_earnings": 0.0, "completed_deliveries": 0}, "history": []}

    def save_delivery_data(self):
        with open(DELIVERY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.delivery_data, f, indent=2)

    def _load_locations(self):
        if not LOCATIONS_FILE.exists():
            messagebox.showerror("Fehler", f"Die Datei {LOCATIONS_FILE} wurde nicht gefunden!")
            sys.exit(1)
        with open(LOCATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_new_order(self):
        if self.game_state != "IDLE" or len(self.available_orders) > 0:
            return

        delivery_points = {name: data for name, data in self.all_locations.items() if data['type'] == 'delivery_point'}
        customer = random.choice(list(delivery_points.values()))
        restaurant_name = random.choice(list(self.locations_data['menu'].keys()))
        menu = self.locations_data['menu'][restaurant_name]
        
        num_items_to_order = random.randint(2, 4)
        ordered_item_names = random.choices([item['name'] for item in menu], k=num_items_to_order)
        required_items_with_quantity = dict(Counter(ordered_item_names))
        
        order_cost = sum(next(item['price'] for item in menu if item['name'] == name) * qty for name, qty in required_items_with_quantity.items())

        new_order = {
            "id": str(uuid.uuid4()),
            "customer_name": customer['name'],
            "customer_display_name": customer['display_name'],
            "restaurant_name": restaurant_name,
            "restaurant_display_name": self.all_locations[restaurant_name]['display_name'],
            "items": required_items_with_quantity,
            "cost": order_cost
        }

        self.available_orders.append(new_order)
        self.phone.update_available_orders_list(self.available_orders)
        print(f"Ein neuer Auftrag ist verfügbar: Lieferung für {customer['display_name']}.")

    def accept_order(self, order_id):
        order = next((o for o in self.available_orders if o['id'] == order_id), None)
        if not order or self.game_state != "IDLE":
            return

        self.current_order = order
        self.available_orders.remove(order)
        self.game_state = "WAITING_FOR_PICKUP"
        
        self.phone.show_screen("delivery_order_detail")
        self.phone.update_available_orders_list(self.available_orders)
        
        print(f"Auftrag für {order['customer_display_name']} angenommen.")
        
        # KORREKTUR: sent_by_me=True hinzugefügt
        send_message(
            order['customer_display_name'], 
            "Hey, ich habe deine Bestellung über die App erhalten und mache mich auf den Weg zum Restaurant!",
            sent_by_me=True
        )

    def update_from_telemetry(self, telemetry_data):
        if not telemetry_data or not telemetry_data.get("game", {}).get("connected"):
            self.current_location_name = None
            return
        
        if self.phone.visible:
            self.phone.update_navi_map_truck(telemetry_data)
    
        truck_data = telemetry_data.get("truck", {})
        player_pos_dict = truck_data.get("placement", {})
        engine_on = truck_data.get("engineOn", False)
    
        if player_pos_dict:
            player_coords_tuple = (player_pos_dict.get('x', 0), player_pos_dict.get('z', 0))
            found_location_name = None
            for loc_name, loc_data in self.all_locations.items():
                polygon = [(p['x'], p['z']) for p in loc_data['corners']]
                if is_point_in_polygon(player_coords_tuple, polygon):
                    found_location_name = loc_name
                    break
            self.current_location_name = found_location_name
    
        if not engine_on and self.last_engine_state:
            self.handle_engine_off()
    
        self.last_engine_state = engine_on

    def handle_engine_off(self):
        if self.game_state == "WAITING_FOR_PICKUP":
            if self.current_order and self.current_location_name == self.current_order['restaurant_name']:
                self.show_order_menu()
        elif self.game_state == "WAITING_FOR_DELIVERY":
            if self.current_order and self.current_location_name == self.current_order['customer_name']:
                self.process_delivery()

    def show_order_menu(self):
        if self.order_menu_window and self.order_menu_window.window.winfo_exists():
            self.order_menu_window.show()
            return

        self.order_menu_window = OrderMenuOverlay(
            parent=self.phone.window,
            restaurant_name=self.current_order['restaurant_display_name'],
            required_items=self.current_order['items'],
            menu=self.locations_data['menu'][self.current_order['restaurant_name']],
            on_confirm_callback=self.process_pickup,
            on_cancel_callback=lambda: print("Bestellung abgebrochen.")
        )
        self.order_menu_window.show()

    def process_pickup(self, selected_items, total_cost):
        if selected_items != self.current_order['items']:
            messagebox.showerror("Falsche Bestellung", "Die Artikel stimmen nicht überein!", parent=self.order_menu_window.window)
            self.show_order_menu()
            return

        if self.player_wallet < total_cost:
            messagebox.showerror("Nicht genug Geld", f"Du hast nur {self.player_wallet:.2f}€.", parent=self.order_menu_window.window)
            self.show_order_menu()
            return

        self.player_wallet -= total_cost
        self.player_inventory = self.current_order['items']
        self.game_state = "WAITING_FOR_DELIVERY"
        
        self.phone.update_order_detail_view()
        
        customer_display_name = self.current_order['customer_display_name']
        send_message(customer_display_name, "Hab die Bestellung, bin auf dem Weg!", sent_by_me=True)
        
        def send_customer_reply():
            customer_data = self.all_locations[self.current_order['customer_name']]
            # Holt die Beschreibung aus der JSON oder nimmt einen Standardtext
            delivery_sms = customer_data.get("description", "Super, danke! Wir warten hier auf dich.")
            send_message(customer_display_name, delivery_sms)
        
        threading.Timer(2.0, send_customer_reply).start()

    def process_delivery(self):
        if not self.player_inventory: return

        payment = self.current_order['cost'] * PROFIT_MARGIN
        tip = payment * random.uniform(0.05, 0.15)
        total_paid = payment + tip
        profit = total_paid - self.current_order['cost']
        
        self.player_wallet += total_paid
        
        self.delivery_data['stats']['total_earnings'] += profit
        self.delivery_data['stats']['completed_deliveries'] += 1
        self.delivery_data['history'].append({
            "customer": self.current_order['customer_display_name'],
            "profit": round(profit, 2),
            "date": time.strftime("%Y-%m-%d %H:%M")
        })
        self.save_delivery_data()
        self.phone.update_dashboard_stats()
        
        send_message(self.current_order['customer_display_name'], f"Perfekt, danke dir! Haben dir {total_paid:.2f}€ (inkl. Trinkgeld) per App geschickt.")
        
        self.player_inventory = None
        self.current_order = None
        self.game_state = "IDLE"
        self.phone.show_screen("delivery_dashboard")

        delay = random.randint(20, 40)
        print(f"INFO: Nächster Auftrag in {delay} Sekunden...")
        threading.Timer(delay, self.generate_new_order).start()

    # NEU: Logik für die Hilfe-Anfrage
    def ask_for_help(self):
        if self.game_state != "WAITING_FOR_DELIVERY" or not self.current_order:
            return

        customer_display_name = self.current_order['customer_display_name']
        customer_data = self.all_locations[self.current_order['customer_name']]
        
        send_message(customer_display_name, "Hey, wo genau seid ihr?", sent_by_me=True)

        def send_customer_help():
            help_text = customer_data.get("help_response", "Sorry, hab grad schlechten Empfang.")
            image_path = customer_data.get("image_path")
            
            send_message(customer_display_name, help_text)
            
            if image_path:
                time.sleep(1) # Kurze Pause vor dem Bild
                send_message(customer_display_name, f"[Bild gesendet: {image_path}]")
        
        threading.Timer(2.5, send_customer_help).start()

class TelemetryPoller(threading.Thread):
    def __init__(self, manager):
        super().__init__(daemon=True)
        self.manager = manager
        self.running = True

    def run(self):
        print("📡 Telemetrie-Poller gestartet.")
        while self.running:
            try:
                response = requests.get(TELEMETRY_URL, timeout=0.8)
                response.raise_for_status()
                data = response.json()
                self.manager.update_from_telemetry(data)
            except (requests.exceptions.RequestException, json.JSONDecodeError):
                self.manager.update_from_telemetry(None)
            time.sleep(POLL_INTERVAL_S)

    def stop(self):
        self.running = False
        print("🛑 Telemetrie-Poller gestoppt.")

def main():
    create_sample_files_if_missing()
    start_telemetry_server()

    root = tk.Tk()
    root.withdraw()

    phone_ui = PhoneOverlayLieferdienst(root, None)
    manager = DeliveryManager(phone_ui)
    phone_ui.manager = manager
    
    # Wichtig: Nach der Initialisierung die Stats einmalig laden
    phone_ui.load_delivery_data()

    keyboard.on_press_key('up', lambda _: phone_ui.toggle_visibility())
    
    print("\n✅ Liefer-Modus v2 bereit. Steuerung:")
    print("  -> Pfeil HOCH: Handy öffnen/schließen")
    print("  -> Im Handy: Pfeiltasten, Enter, Backspace zur Navigation")
    
    poller = TelemetryPoller(manager)
    poller.start()

    print("INFO: Erster Auftrag wird in 10 Sekunden generiert...")
    root.after(10000, manager.generate_new_order)

    try:
        root.mainloop()
    finally:
        poller.stop()
        phone_ui.close()
        keyboard.unhook_all()
        print("Anwendung wird beendet.")

if __name__ == "__main__":
    main()