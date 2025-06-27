# src/device_manager.py
import tkinter as tk
import keyboard

from src.config import PROFILE_PATH
from src.ui.phone_ui import PhoneOverlay
from src.ui.laptop_ui import LaptopOverlay
from src.event_handler.event_handler import ETS2EventHandler
from src.career.career_manager import CareerManager 

class DeviceManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() 

        print("Initialisiere UI-Komponenten...")
        self.phone = PhoneOverlay(self.root)
        self.laptop = LaptopOverlay(self.root)
        
        print("Initialisiere Event-Handler...")
        self.ets2_event_handler = ETS2EventHandler(profile_path=PROFILE_PATH)
        
        print("Initialisiere Career-Manager...")
        self.career_manager = CareerManager(laptop_ui_instance=self.laptop)
        self.laptop.set_career_manager(self.career_manager)

        self.setup_keyboard_listener()

    def setup_keyboard_listener(self):
        """Setzt die globalen Keyboard Listener auf."""
        keyboard.on_press_key('up', self.show_phone_if_hidden, suppress=False)
        keyboard.on_press_key('down', self.toggle_laptop, suppress=False)
        
    def show_phone_if_hidden(self, e):
        """Öffnet das Handy, wenn es geschlossen ist und der Laptop auch."""
        if not self.phone.is_visible() and not self.laptop.is_visible():
            self.phone.toggle_visibility()
            return True # Event wurde verarbeitet
        return False

    def toggle_laptop(self, e):
        """Öffnet/schließt den Laptop, aber nur wenn das Handy nicht offen ist."""
        if not self.phone.is_visible():
            self.laptop.toggle_visibility()
            return True # Event wurde verarbeitet
        return False

    def run(self):
        """Startet die Hauptschleife und Hintergrund-Threads."""
        print("Starte Hintergrund-Dienste (ETS2 Event Handler, Career Manager)...")
        self.ets2_event_handler.start()
        self.career_manager.start() 

        print("\n✅ System bereit. Steuerung:")
        print("  -> Pfeil HOCH: Handy öffnen")
        print("  -> Pfeil RUNTER: Laptop öffnen/schließen")
        print("  -> BACKSPACE: Im Menü zurück / Gerät schließen")
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()

    def _on_closing(self):
        """Wird aufgerufen, wenn das Tkinter-Fenster geschlossen wird."""
        print("\nAufräumen und Beenden...")
        self.ets2_event_handler.stop()
        self.career_manager.stop() 
        self.phone.close()
        self.laptop.close()
        self.root.destroy()