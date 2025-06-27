# src/ui/phone_ui.py
import tkinter as tk
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


from src.config import (
    PHONE_WIDTH, PHONE_HEIGHT, PHONE_MESSAGE_FILE, PROFILE_PATH, TELEMETRY_URL
)
from src.actions.communication import send_message
from src.actions.job_actions import process_job_request_async
from src.game_integration.ets2_savegame_parser import SavegameParser
from src.utils.location import get_current_coordinates, get_nearest_city_from_db, load_city_database
from src.utils.translation import get_pretty_city_name

class PhoneOverlay:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.overrideredirect(True)
        self.window.wm_attributes('-topmost', True)
        
        self.visible = False
        self.animation_running = False
        self.current_screen = "home"
        self.selected_index = 0
        
        self.messages = []
        self.current_conversation = None
        self.last_message_check = 0
        self.last_ingame_time_str = "00:00"
        
        self.chat_scroll_position = 0
        self.image_references = []
        
        self.setup_window()
        self.city_database = load_city_database()
        self.create_ui()
        self.load_messages()
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_messages, daemon=True)
        self.monitor_thread.start()
        
        self.update_loop()

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
        
        self.screens = {
            "home": self._create_home_screen(),
            "messages": self._create_messages_screen(),
            "message_detail": self._create_message_detail_screen(),
            "city_selection": self._create_city_selection_screen(),
            "browser_home": self._create_browser_home_screen(),
            "police_login": self._create_police_login_screen(),
            "police_database": self._create_police_database_screen(),
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
            {"name": "Browser", "icon": "🌐", "color": "#007aff", "screen": "browser_home"},
            {"name": "Phone", "icon": "📞", "color": "#34c759", "screen": None},
            {"name": "Settings", "icon": "⚙️", "color": "#8e8e93", "screen": None}
        ]
        self.app_buttons = []
        for i, app in enumerate(self.apps):
            row, col = divmod(i, 2)
            container = tk.Frame(apps_frame, bg='#1a1a2e')
            container.grid(row=row, column=col, padx=25, pady=25, sticky='nsew')
            shadow = tk.Frame(container, bg='#0a0a0a', width=68, height=68)
            shadow.pack()
            shadow.place(x=2, y=2)
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

    def show_screen(self, screen_name):
        for screen in self.screens.values():
            screen.pack_forget()
        
        self.screens[screen_name].pack(fill='both', expand=True)
        self.current_screen = screen_name
        self.selected_index = 0
        
        if screen_name == "messages": self.update_messages_list()
        elif screen_name == "message_detail":
            self.chat_scroll_position = 1.0
            self.show_conversation()
        elif screen_name == "city_selection": self.update_city_list()
        elif screen_name == "police_login": 
            self.animate_loading_dots()
            self.window.after(2500, self.load_and_show_police_data)
        
        self.update_selection_highlight()

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

    def update_selection_highlight(self):
        if self.current_screen == "home":
            for i, btn in enumerate(self.app_buttons):
                if i == self.selected_index:
                    btn["frame"].config(bg='#2c2c2e')
                    for child in btn["frame"].winfo_children():
                        if isinstance(child, tk.Frame) and child.cget('bg') != '#0a0a0a':
                            child.config(highlightbackground='#007aff', highlightthickness=2)
                else:
                    btn["frame"].config(bg='#1a1a2e')
                    for child in btn["frame"].winfo_children():
                        if isinstance(child, tk.Frame) and child.cget('bg') != '#0a0a0a':
                            child.config(highlightthickness=0)
                            
        elif self.current_screen == "messages" and hasattr(self, 'message_items'):
            for i, item in enumerate(self.message_items):
                bg_color = '#1c1c1e' if i == self.selected_index else '#000000'
                item["frame"].config(bg=bg_color, highlightbackground='#007aff', highlightthickness=(1 if i == self.selected_index else 0))
                for child in item["frame"].winfo_children():
                    if child.cget('bg') not in ['#3a3a3c', '#007aff']: child.config(bg=bg_color)
                        
        elif self.current_screen == "city_selection":
            for i, item_frame in enumerate(self.city_list_items):
                bg_color = '#1c1c1e' if i == self.selected_index else '#000000'
                item_frame.config(bg=bg_color, highlightbackground='#007aff', highlightthickness=(1 if i == self.selected_index else 0))
                for child in item_frame.winfo_children(): child.config(bg=bg_color)
            
            if self.city_list_items:
                self.city_list_canvas.update_idletasks()
                item_y = self.city_list_items[self.selected_index].winfo_y()
                canvas_height = self.city_list_canvas.winfo_height()
                scroll_region = self.city_list_canvas.bbox("all")
                if scroll_region:
                    total_height = scroll_region[3]
                    if total_height > canvas_height:
                        scroll_pos = item_y / total_height
                        self.city_list_canvas.yview_moveto(scroll_pos)

        elif self.current_screen == "browser_home":
            for i, item in enumerate(self.bookmark_buttons):
                bg_color = '#e8f4ff' if i == self.selected_index else '#ffffff'
                item["frame"].config(bg=bg_color, highlightbackground='#007aff', highlightthickness=(2 if i == self.selected_index else 0))
                for child in item["frame"].winfo_children(): child.config(bg=bg_color)
                    
        elif self.current_screen == "police_database":
            for i, item in enumerate(self.police_record_items):
                bg_color = '#e8f4ff' if i == self.selected_index else '#ffffff'
                item['frame'].config(bg=bg_color, highlightbackground='#007aff', highlightthickness=(2 if i == self.selected_index else 0))
                for child in item['frame'].winfo_children(): child.config(bg=bg_color)
            if self.police_record_items:
                self.police_records_canvas.yview_moveto(self.selected_index / len(self.police_record_items))

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
            items_len = len(getattr(self, 'message_items', [])) if self.current_screen == 'messages' else \
                        len(self.city_list_items) if self.current_screen == 'city_selection' else \
                        len(self.bookmark_buttons) if self.current_screen == 'browser_home' else \
                        len(self.police_record_items) if self.current_screen == 'police_database' else 0
            if items_len > 0: self.selected_index = (self.selected_index + direction) % items_len
        self.update_selection_highlight()

    def on_key_enter(self, e):
        if self.current_screen == "home":
            if (screen := self.apps[self.selected_index]["screen"]): self.show_screen(screen)
        elif self.current_screen == "messages" and self.selected_index < len(self.messages):
            self.current_conversation = self.messages[self.selected_index]
            self.show_screen("message_detail")
        elif self.current_screen == "message_detail" and self.current_conversation.get("sender") == "Dispo":
            self.show_screen("city_selection")
        elif self.current_screen == "city_selection" and self.selected_index < len(self.available_cities):
            # HIER wird der "schöne" Name verwendet
            city = self.available_cities[self.selected_index]
            send_message("Dispo", f"Bin in {city.capitalize()}, brauche neuen Auftrag.", sent_by_me=True)
            process_job_request_async(city)
            self.show_screen("message_detail")
        elif self.current_screen == "browser_home" and self.selected_index < len(self.bookmarks):
            self.bookmarks[self.selected_index]['action']()

    def on_key_backspace(self, e):
        back_map = {
            "police_database": "browser_home", "police_login": "browser_home",
            "browser_home": "home", "city_selection": "message_detail",
            "message_detail": "messages", "messages": "home"
        }
        if target_screen := back_map.get(self.current_screen): self.show_screen(target_screen)
        else: self.toggle_visibility()

    def load_messages(self):
        try:
            if PHONE_MESSAGE_FILE.exists():
                with open(PHONE_MESSAGE_FILE, 'r', encoding='utf-8') as f:
                    self.messages = json.load(f).get('conversations', [])
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
        
        # Alte Widgets und Bild-Referenzen löschen
        for w in self.messages_frame.winfo_children(): w.destroy()
        self.image_references.clear()
    
        for i, msg in enumerate(self.current_conversation["messages"]):
            is_sent = msg.get("sent_by_me", False)
            msg_container = tk.Frame(self.messages_frame, bg='#000000')
            msg_container.pack(fill='x', pady=3)
            max_width = int(PHONE_WIDTH * 0.7)
    
            # NEUE LOGIK: Prüfen, ob die Nachricht ein Bild ist
            image_match = re.match(r"\[Bild gesendet: (.*?)\]", msg["text"])
    
            if image_match:
                image_path = image_match.group(1).strip()
                try:
                    # Bild laden und für die Anzeige vorbereiten
                    img = Image.open(image_path)
                    img.thumbnail((180, 180)) # Bild auf eine vernünftige Größe verkleinern
                    photo = ImageTk.PhotoImage(img)
                    
                    # Bild in einem Label anzeigen
                    img_label = tk.Label(msg_container, image=photo, bg='#000000', bd=0)
                    img_label.image = photo # WICHTIG: Referenz speichern!
                    self.image_references.append(photo) # Zusätzliche Referenz in der Liste speichern
    
                    if is_sent:
                        img_label.pack(side='right', padx=(50, 15))
                    else:
                        img_label.pack(side='left', padx=(15, 50))
    
                except FileNotFoundError:
                    # Fallback, wenn das Bild nicht gefunden wird
                    error_text = f"Bild nicht gefunden:\n{os.path.basename(image_path)}"
                    bubble = tk.Label(msg_container, text=error_text, bg="#ff3b30", fg='white', font=('SF Pro Display', 14), wraplength=max_width, justify='left', padx=16, pady=12, bd=0)
                    if is_sent: bubble.pack(side='right', padx=(50, 15))
                    else: bubble.pack(side='left', padx=(15, 50))
            else:
                # ALTE LOGIK: Wenn es kein Bild ist, zeige eine normale Textblase an
                bubble_bg = '#007aff' if is_sent else '#3a3a3c'
                bubble = tk.Label(msg_container, text=msg["text"], bg=bubble_bg, fg='#ffffff', font=('SF Pro Display', 16), wraplength=max_width, justify='left', padx=16, pady=12, bd=0)
                if is_sent: bubble.pack(side='right', padx=(50, 15))
                else: bubble.pack(side='left', padx=(15, 50))
    
            # Zeitstempel für die letzte Nachricht (unverändert)
            if i == len(self.current_conversation["messages"]) - 1 and (time_text := msg.get("ingame_time", "")):
                time_label = tk.Label(msg_container, text=time_text, bg='#000000', fg='#8e8e93', font=('SF Pro Display', 12))
                if is_sent: time_label.pack(side='right', padx=(0, 20), pady=(2, 0))
                else: time_label.pack(side='left', padx=(20, 0), pady=(2, 0))
                
        self.messages_frame.update_idletasks()
        self.messages_container.config(scrollregion=self.messages_container.bbox("all"))
        self.messages_container.yview_moveto(1.0)

    def _get_pretty_city_name(self, savegame_city_name):
        """Findet den schönen Namen aus der DB für einen Savegame-Namen."""
        if not self.city_database: return savegame_city_name.capitalize()
        
        # Nutze difflib, um den besten Match zu finden (z.B. 'Hinterw' -> 'hinterweidenthal')
        match = difflib.get_close_matches(savegame_city_name.lower(), self.city_database.keys(), n=1, cutoff=0.5)
        return match[0] if match else savegame_city_name.capitalize()

    def update_city_list(self):
        """Zeigt eine saubere, einzigartige Liste von Städten mit verfügbaren Jobs an."""
        for item in self.city_list_items: item.destroy()
        self.city_list_items.clear()
        
        # 1. Hole alle rohen Städtenamen mit verfügbaren Jobs aus dem Savegame
        try:
            parser = SavegameParser(profile_path=PROFILE_PATH)
            cities_with_jobs_raw = parser.get_available_cities() or []
        except Exception as e:
            # Zeige einen Fehler an, wenn das Parsen fehlschlägt
            self.available_cities = [f"Fehler: {e}"]
            # (Hier könnte man die UI-Erstellung für den Fehlerfall noch verbessern)
            return

        # 2. Übersetze die rohen Namen in schöne Namen und mache die Liste einzigartig und sortiert
        pretty_cities_with_jobs = sorted(list(set([get_pretty_city_name(raw_name) for raw_name in cities_with_jobs_raw])))

        # 3. Finde die tatsächlich nächste Stadt basierend auf Koordinaten
        player_coords = get_current_coordinates()
        # nearest_city_name ist der "schöne" Name aus der city_database.json (z.B. "hoeheinoed")
        nearest_city_name = get_nearest_city_from_db(player_coords, self.city_database)
        
        # 4. Erstelle die finale, sortierte Liste
        # Die nächste Stadt kommt immer zuerst, falls sie auch Jobs hat.
        final_city_list = []
        if nearest_city_name:
            # Finde den passenden Namen in unserer Job-Liste (ignoriere Groß/Kleinschreibung)
            # z.B. vergleiche "hoeheinoed" (von GPS) mit "Höheinöd" (aus Jobliste)
            matching_city_in_list = next((city for city in pretty_cities_with_jobs if city.lower() == nearest_city_name.lower()), None)
            
            if matching_city_in_list:
                final_city_list.append(matching_city_in_list)
                pretty_cities_with_jobs.remove(matching_city_in_list)
        
        # Füge die restlichen Städte (alphabetisch sortiert) hinzu
        final_city_list.extend(pretty_cities_with_jobs)
        self.available_cities = final_city_list

        # 5. Erstelle die UI-Elemente
        for city_name in self.available_cities:
            city_frame = tk.Frame(self.city_list_frame, bg='#000000', height=50)
            city_frame.pack(fill='x', pady=1)
            city_frame.pack_propagate(False)
            
            # Highlight für die nächstgelegene Stadt
            icon_text = "📍"
            if nearest_city_name and city_name.lower() == nearest_city_name.lower():
                icon_text = "🛰️" # Anderes Icon für die GPS-Position

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

    def close(self):
        self.monitoring = False
        try:
            self.setup_keyboard_hooks(False)
        except:
            pass