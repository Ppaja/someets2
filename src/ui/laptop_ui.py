# src/ui/laptop_ui.py
import tkinter as tk
from tkinter import messagebox, ttk
import time
import keyboard
import json
import os
import threading
from datetime import datetime
import requests

try:
    import cv2
    VIDEO_LIBS_AVAILABLE = True
except ImportError:
    VIDEO_LIBS_AVAILABLE = False


from src.config import LAPTOP_WIDTH, LAPTOP_HEIGHT, LAPTOP_MAIL_FILE, DATA_DIR, TELEMETRY_URL

class LaptopOverlay:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.overrideredirect(True)
        self.window.wm_attributes('-topmost', True)
        
        self.visible = False
        self.animation_running = False
        self.current_screen = "desktop"
        self.emails = []
        self.selected_email_index = -1
        self.last_mail_check = 0
        self.last_ingame_time_str = "00:00"


        
        self.career_manager = None # Wird vom DeviceManager gesetzt
        self.career_data = {}

        self.setup_window()
        self.create_ui()

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_files, daemon=True)
        self.monitor_thread.start()

        # TEMPORÄRER TEST - Video nach 10 Sekunden abspielen
        # self.window.after(10000, self.test_video_playback)

    def test_video_playback(self):
        print("Starte Test-Video Wiedergabe...")
        def video_finished():
            print("Test-Video beendet!")

        self.play_fullscreen_video("bewerbung.mp4", video_finished)


    
    def set_career_manager(self, manager):
        self.career_manager = manager

    def setup_window(self):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.target_x = (screen_width - LAPTOP_WIDTH) // 2
        self.target_y = (screen_height - LAPTOP_HEIGHT) // 2
        self.hidden_y = screen_height + 50
        self.window.geometry(f"{LAPTOP_WIDTH}x{LAPTOP_HEIGHT}+{self.target_x}+{self.hidden_y}")
        self.window.configure(bg='#2c2c2c')

    def create_ui(self):
        self.laptop_frame = tk.Frame(self.window, bg='#2c2c2c', padx=20, pady=15)
        self.laptop_frame.pack(fill='both', expand=True)
        
        self.screen_frame = tk.Frame(self.laptop_frame, bg='#000000', padx=3, pady=3)
        self.screen_frame.pack(fill='both', expand=True)
        
        self.main_frame = tk.Frame(self.screen_frame, bg='#1a1a1a')
        self.main_frame.pack(fill='both', expand=True)
        
        self.create_taskbar()
        
        # UI-Elemente für die Screens erstellen
        self.create_desktop_screen()
        self.create_mail_screen()
        self.create_browser_screen()
        self.create_netto_career_screen()
        self.create_netto_intranet_screen()
        
        self.show_screen("desktop")
        self.create_laptop_bottom()

    def create_taskbar(self):
        self.taskbar = tk.Frame(self.main_frame, bg='#333333', height=35)
        self.taskbar.pack(side='bottom', fill='x')
        self.taskbar.pack_propagate(False)
        
        start_btn = tk.Button(self.taskbar, text="⊞", font=("Segoe UI", 14), 
                             bg='#404040', fg='white', relief='flat', padx=10,
                             activebackground='#505050')
        start_btn.pack(side='left', padx=5, pady=3)
        
        self.time_label = tk.Label(self.taskbar, text="", font=("Segoe UI", 10), 
                                  bg='#333333', fg='white')
        self.time_label.pack(side='right', padx=10, pady=5)
        self.update_time()

    def create_laptop_bottom(self):
        bottom_frame = tk.Frame(self.laptop_frame, bg='#2c2c2c', height=60)
        bottom_frame.pack(side='bottom', fill='x', pady=(5, 0))
        bottom_frame.pack_propagate(False)
        
        keyboard_frame = tk.Frame(bottom_frame, bg='#1a1a1a', height=35)
        keyboard_frame.pack(fill='x', padx=10, pady=5)
        keyboard_frame.pack_propagate(False)
        
        for i in range(12):
            key = tk.Frame(keyboard_frame, bg='#404040', width=25, height=15)
            key.pack(side='left', padx=1, pady=5)
            key.pack_propagate(False)
        
        trackpad = tk.Frame(bottom_frame, bg='#1a1a1a', width=80, height=50)
        trackpad.pack(pady=2)
        trackpad.pack_propagate(False)

    def update_time(self):
        try:
            import requests
            response = requests.get(TELEMETRY_URL, timeout=0.5)
            if response.ok and (time_str := response.json().get("game", {}).get("time")):
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                self.last_ingame_time_str = f"{dt.hour:02d}:{dt.minute:02d}"
        except requests.RequestException: 
            pass
        self.time_label.config(text=self.last_ingame_time_str)
        self.window.after(60000, self.update_time)


    def show_screen(self, screen_name):
        all_screen_widgets = [
            self.desktop_screen,
            self.mail_screen,
            self.browser_screen,
            self.netto_career_screen,
            self.netto_intranet_screen
        ]
        for widget in all_screen_widgets:
            widget.pack_forget()
            
        # Logik zum Anzeigen des richtigen Screens
        if screen_name == "desktop":
            self.desktop_screen.pack(fill='both', expand=True, before=self.taskbar)
        elif screen_name == "mail":
            self.mail_screen.pack(fill='both', expand=True, before=self.taskbar)
            self.load_emails()
        elif screen_name == "browser":
            self.browser_screen.pack(fill='both', expand=True, before=self.taskbar)
        elif screen_name == "netto_career":
            self.netto_career_screen.pack(fill='both', expand=True, before=self.taskbar)
        elif screen_name == "netto_intranet":
            self.netto_intranet_screen.pack(fill='both', expand=True, before=self.taskbar)
            
        self.current_screen = screen_name

    def create_desktop_screen(self):
        self.desktop_screen = tk.Frame(self.main_frame, bg='#0f1419')
        
        canvas = tk.Canvas(self.desktop_screen, bg='#0f1419', highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        icons_frame = tk.Frame(canvas, bg='#0f1419')
        canvas.create_window(30, 30, window=icons_frame, anchor='nw')
        
        # Icons in 2x2 Grid anordnen
        self.create_desktop_icon(icons_frame, "📧", "E-Mail", lambda: self.show_screen("mail"), row=0, col=0)
        self.create_desktop_icon(icons_frame, "🌐", "Browser", lambda: self.show_screen("browser"), row=0, col=1)
        self.create_desktop_icon(icons_frame, "⚙️", "Einstellungen", None, state='disabled', row=0, col=2)
        self.create_desktop_icon(icons_frame, "📊", "Berichte", None, state='disabled', row=0, col=3)

    def create_desktop_icon(self, parent, icon_text, label_text, command, row=0, col=0, state='normal'):
        icon_frame = tk.Frame(parent, bg='#0f1419')
        icon_frame.grid(row=row, column=col, padx=20, pady=20, sticky='n')
        
        button = tk.Button(icon_frame, text=icon_text, font=("Segoe UI Emoji", 32), 
                           bg='#2d3748', fg='white', relief='flat', borderwidth=0,
                           activebackground='#4a5568', activeforeground='white',
                           command=command, padx=15, pady=12, state=state,
                           width=4, height=2)
        button.pack()
        
        label = tk.Label(icon_frame, text=label_text, font=("Segoe UI", 9), 
                         bg='#0f1419', fg='white')
        label.pack(pady=(8, 0))

    def create_mail_screen(self):
        self.mail_screen = tk.Frame(self.main_frame, bg='#ffffff')
        header = tk.Frame(self.mail_screen, bg='#f8f9fa', height=60)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        back_btn = tk.Button(header, text="←", font=("Segoe UI", 16), bg='#e9ecef', fg='#495057', relief='flat', activebackground='#dee2e6', padx=15, pady=5, command=lambda: self.show_screen("desktop"))
        back_btn.pack(side='left', padx=10, pady=10)
        title_label = tk.Label(header, text="📧 Posteingang", font=("Segoe UI", 18, "bold"), bg='#f8f9fa', fg='#212529')
        title_label.pack(side='left', padx=10, pady=15)
        separator = tk.Frame(self.mail_screen, height=1, bg='#dee2e6')
        separator.pack(fill='x')
        content_frame = tk.Frame(self.mail_screen, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        inbox_frame = tk.Frame(content_frame, bg='#f8f9fa', width=280, relief='solid', bd=1)
        inbox_frame.pack(side='left', fill='y', padx=(0, 10))
        inbox_frame.pack_propagate(False)
        inbox_header = tk.Label(inbox_frame, text="Nachrichten", font=("Segoe UI", 12, "bold"), bg='#e9ecef', fg='#495057', pady=8)
        inbox_header.pack(fill='x')
        self.inbox_listbox = tk.Listbox(inbox_frame, bg='#ffffff', fg='#212529', font=("Segoe UI", 11), selectbackground='#007bff', selectforeground='white', borderwidth=0, highlightthickness=0, activestyle='none')
        self.inbox_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.inbox_listbox.bind('<<ListboxSelect>>', self.on_email_select)
        view_frame = tk.Frame(content_frame, bg='#ffffff', relief='solid', bd=1)
        view_frame.pack(side='right', fill='both', expand=True)
        email_header = tk.Frame(view_frame, bg='#f8f9fa', height=80)
        email_header.pack(fill='x')
        email_header.pack_propagate(False)
        self.email_subject_label = tk.Label(email_header, text="Wählen Sie eine E-Mail aus", font=("Segoe UI", 14, "bold"), bg='#f8f9fa', fg='#212529', anchor='w')
        self.email_subject_label.pack(fill='x', padx=15, pady=(10, 0))
        self.email_sender_label = tk.Label(email_header, text="", font=("Segoe UI", 10), bg='#f8f9fa', fg='#6c757d', anchor='w')
        self.email_sender_label.pack(fill='x', padx=15, pady=(0, 10))
        tk.Frame(view_frame, height=1, bg='#dee2e6').pack(fill='x')
        self.email_body_text = tk.Text(view_frame, wrap="word", font=("Segoe UI", 11), bg='#ffffff', fg='#212529', borderwidth=0, highlightthickness=0, state='disabled', padx=15, pady=15)
        self.email_body_text.pack(fill='both', expand=True)

    def on_email_select(self, event=None):
        if not (selection := self.inbox_listbox.curselection()): return
        self.selected_email_index = selection[0]
        email = self.emails[self.selected_email_index]
        self.email_subject_label.config(text=email['subject'])
        self.email_sender_label.config(text=f"Von: {email['sender']} • {datetime.fromtimestamp(email['timestamp']).strftime('%d.%m.%Y %H:%M')}")
        self.email_body_text.config(state='normal')
        self.email_body_text.delete('1.0', tk.END)
        self.email_body_text.insert('1.0', email['body'])
        self.email_body_text.config(state='disabled')

    def load_emails(self):
        try:
            if LAPTOP_MAIL_FILE.exists():
                with open(LAPTOP_MAIL_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.emails = sorted(data.get('emails', []), key=lambda e: e['timestamp'], reverse=True)
                self.inbox_listbox.delete(0, tk.END)
                for email in self.emails:
                    sender_short = email['sender'][:15] + "..." if len(email['sender']) > 15 else email['sender']
                    subject_short = email['subject'][:25] + "..." if len(email['subject']) > 25 else email['subject']
                    self.inbox_listbox.insert(tk.END, f"{sender_short}\n{subject_short}")
                if self.emails:
                    self.inbox_listbox.selection_set(self.selected_email_index if self.selected_email_index < len(self.emails) else 0)
                    self.on_email_select()
        except Exception as e:
            print(f"Fehler beim Laden der E-Mails: {e}")

    def create_browser_screen(self):
        self.browser_screen = tk.Frame(self.main_frame, bg='#ffffff')
        
        # Browser Header mit URL-Bar
        header = tk.Frame(self.browser_screen, bg='#f0f0f0', height=70)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        
        # Navigation Buttons
        nav_frame = tk.Frame(header, bg='#f0f0f0')
        nav_frame.pack(side='left', padx=10, pady=10)
        
        back_btn = tk.Button(nav_frame, text="←", font=("Segoe UI", 12), 
                            bg='#e0e0e0', fg='#333', relief='flat', padx=8, pady=4,
                            command=lambda: self.show_screen("desktop"))
        back_btn.pack(side='left', padx=2)
        
        forward_btn = tk.Button(nav_frame, text="→", font=("Segoe UI", 12), 
                               bg='#e0e0e0', fg='#333', relief='flat', padx=8, pady=4, state='disabled')
        forward_btn.pack(side='left', padx=2)
        
        refresh_btn = tk.Button(nav_frame, text="⟳", font=("Segoe UI", 12), 
                               bg='#e0e0e0', fg='#333', relief='flat', padx=8, pady=4)
        refresh_btn.pack(side='left', padx=2)
        
        # URL Bar
        url_frame = tk.Frame(header, bg='#f0f0f0')
        url_frame.pack(side='left', fill='x', expand=True, padx=10, pady=15)
        
        self.url_entry = tk.Entry(url_frame, font=("Segoe UI", 11), bg='white', 
                                 relief='solid', bd=1, state='readonly')
        self.url_entry.pack(fill='x', ipady=5)
        self.url_entry.insert(0, "https://www.netto-online.de/karriere")
        
        # Browser Content
        content = tk.Frame(self.browser_screen, bg='#ffffff', padx=20, pady=20)
        content.pack(fill='both', expand=True)
        
        # Startseite mit Favoriten
        tk.Label(content, text="🔖 Favoriten", font=("Segoe UI", 16, "bold"), 
                bg='#ffffff', fg='#333').pack(anchor='w', pady=(0, 15))
        
        # Netto Favorit als Card
        netto_card = tk.Frame(content, bg='#f8f9fa', relief='solid', bd=1)
        netto_card.pack(fill='x', pady=5)
        
        card_content = tk.Frame(netto_card, bg='#f8f9fa')
        card_content.pack(fill='x', padx=15, pady=12)
        
        tk.Label(card_content, text="🛒 Netto Karriereportal", font=("Segoe UI", 14, "bold"), 
                bg='#f8f9fa', fg='#d32f2f').pack(anchor='w')
        tk.Label(card_content, text="Finden Sie Ihren Traumjob bei Deutschlands bestem Discounter", 
                font=("Segoe UI", 10), bg='#f8f9fa', fg='#666').pack(anchor='w', pady=(2, 8))
        
        netto_btn = tk.Button(card_content, text="Zur Website →", font=("Segoe UI", 11, "bold"), 
                             bg='#d32f2f', fg='white', relief='flat', padx=20, pady=8,
                             activebackground='#b71c1c', command=self.open_netto_page)
        netto_btn.pack(anchor='w')

    def open_netto_page(self):
        if self.career_data.get("status") == "employed" and self.career_data.get("company") == "netto":
            self.show_screen("netto_intranet")
        else:
            self.show_screen("netto_career")

    def create_netto_career_screen(self):
        self.netto_career_screen = tk.Frame(self.main_frame, bg='#ffffff')
        
        # Header mit Netto Branding
        header = tk.Frame(self.netto_career_screen, bg='#d32f2f', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#d32f2f')
        header_content.pack(expand=True, fill='both')
        
        # Logo und Navigation
        nav_frame = tk.Frame(header_content, bg='#d32f2f')
        nav_frame.pack(fill='x', padx=20, pady=15)
        
        tk.Label(nav_frame, text="NETTO", font=("Arial", 24, "bold"), 
                bg='#d32f2f', fg='white').pack(side='left')
        
        # Navigation Items
        nav_items = ["Karriere", "Über uns", "Standorte", "Kontakt"]
        for item in nav_items:
            style = ("Arial", 11, "bold") if item == "Karriere" else ("Arial", 11)
            color = '#ffeb3b' if item == "Karriere" else 'white'
            tk.Label(nav_frame, text=item, font=style, bg='#d32f2f', fg=color).pack(side='right', padx=15)
        
        # SCROLLBARER CONTENT BEREICH
        canvas = tk.Canvas(self.netto_career_screen, bg='#ffffff', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.netto_career_screen, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ffffff')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Main Content (jetzt im scrollbaren Bereich)
        main_content = tk.Frame(scrollable_frame, bg='#ffffff')
        main_content.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Hero Section
        hero_frame = tk.Frame(main_content, bg='#ffffff')
        hero_frame.pack(fill='x', pady=(0, 30))
        
        tk.Label(hero_frame, text="Starten Sie Ihre Karriere bei NETTO", 
                font=("Arial", 28, "bold"), bg='#ffffff', fg='#333').pack(anchor='w')
        tk.Label(hero_frame, text="Werden Sie Teil unseres erfolgreichen Teams und gestalten Sie die Zukunft des Handels mit.", 
                font=("Arial", 14), bg='#ffffff', fg='#666', wraplength=600).pack(anchor='w', pady=(10, 20))
        
        # Benefits Section
        benefits_frame = tk.Frame(main_content, bg='#f8f9fa', relief='solid', bd=1)
        benefits_frame.pack(fill='x', pady=(0, 20))
        
        benefits_content = tk.Frame(benefits_frame, bg='#f8f9fa')
        benefits_content.pack(fill='x', padx=25, pady=20)
        
        tk.Label(benefits_content, text="Ihre Vorteile bei NETTO", 
                font=("Arial", 18, "bold"), bg='#f8f9fa', fg='#333').pack(anchor='w', pady=(0, 15))
        
        benefits = [
            "✓ Attraktive Vergütung und Sozialleistungen",
            "✓ Flexible Arbeitszeiten und Work-Life-Balance", 
            "✓ Umfangreiche Weiterbildungsmöglichkeiten",
            "✓ Moderne Arbeitsplätze und Technologien",
            "✓ Kollegiales Arbeitsklima in einem starken Team"
        ]
        
        for benefit in benefits:
            tk.Label(benefits_content, text=benefit, font=("Arial", 12), 
                    bg='#f8f9fa', fg='#333').pack(anchor='w', pady=2)
        
        # Application Section
        app_frame = tk.Frame(main_content, bg='#ffffff')
        app_frame.pack(fill='x', pady=20)
        
        tk.Label(app_frame, text="Bereit für den nächsten Schritt?", 
                font=("Arial", 20, "bold"), bg='#ffffff', fg='#333').pack(anchor='w', pady=(0, 10))
        tk.Label(app_frame, text="Bewerben Sie sich jetzt und starten Sie Ihre Karriere bei Deutschlands führendem Discounter.", 
                font=("Arial", 12), bg='#ffffff', fg='#666').pack(anchor='w', pady=(0, 20))
        
        self.apply_button = tk.Button(app_frame, text="JETZT BEWERBEN", 
                                     font=("Arial", 14, "bold"), bg='#4caf50', fg='white', 
                                     relief='flat', padx=30, pady=12,
                                     activebackground='#45a049', command=self.handle_apply_netto)
        self.apply_button.pack(anchor='w')
        
        # Canvas und Scrollbar packen
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Footer (bleibt fix unten)
        footer_frame = tk.Frame(self.netto_career_screen, bg='#333333', height=60)
        footer_frame.pack(side='bottom', fill='x')
        footer_frame.pack_propagate(False)
        
        back_btn = tk.Button(footer_frame, text="← Zurück zum Browser", 
                            font=("Arial", 11), bg='#555', fg='white', relief='flat',
                            padx=15, pady=8, command=lambda: self.show_screen("browser"))
        back_btn.pack(side='left', padx=20, pady=15)
        
        # Mausrad-Scrolling aktivieren
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)


    def handle_apply_netto(self):
        if self.career_manager:
            self.career_manager.apply_for_job("netto")
            self.apply_button.config(text="BEWERBUNG EINGEGANGEN ✓", state="disabled", 
                                   bg="#cccccc", fg="#666")

    def create_netto_intranet_screen(self):
        self.netto_intranet_screen = tk.Frame(self.main_frame, bg='#f5f5f5')
        
        # Header mit Netto Corporate Design
        header = tk.Frame(self.netto_intranet_screen, bg='#1565c0', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#1565c0')
        header_content.pack(expand=True, fill='both')
        
        nav_frame = tk.Frame(header_content, bg='#1565c0')
        nav_frame.pack(fill='x', padx=20, pady=15)
        
        tk.Label(nav_frame, text="NETTO", font=("Arial", 20, "bold"), 
                bg='#1565c0', fg='white').pack(side='left')
        tk.Label(nav_frame, text="Mitarbeiterportal", font=("Arial", 12), 
                bg='#1565c0', fg='#bbdefb').pack(side='left', padx=(10, 0))
        
        # User Info
        user_frame = tk.Frame(nav_frame, bg='#1565c0')
        user_frame.pack(side='right')
        tk.Label(user_frame, text="👤 Fahrer", font=("Arial", 11), 
                bg='#1565c0', fg='white').pack(side='right', padx=10)
        
        # Main Dashboard
        main_content = tk.Frame(self.netto_intranet_screen, bg='#f5f5f5')
        main_content.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Welcome Section
        welcome_frame = tk.Frame(main_content, bg='white', relief='solid', bd=1)
        welcome_frame.pack(fill='x', pady=(0, 20))
        
        welcome_content = tk.Frame(welcome_frame, bg='white')
        welcome_content.pack(fill='x', padx=25, pady=20)
        
        tk.Label(welcome_content, text="Willkommen im Mitarbeiterportal", 
                font=("Arial", 22, "bold"), bg='white', fg='#333').pack(anchor='w')
        tk.Label(welcome_content, text=f"Heute ist {datetime.now().strftime('%A, %d. %B %Y')}", 
                font=("Arial", 12), bg='white', fg='#666').pack(anchor='w', pady=(5, 0))
        
        # Quick Actions
        actions_frame = tk.Frame(main_content, bg='white', relief='solid', bd=1)
        actions_frame.pack(fill='x', pady=(0, 20))
        
        actions_content = tk.Frame(actions_frame, bg='white')
        actions_content.pack(fill='x', padx=25, pady=20)
        
        tk.Label(actions_content, text="Schnellzugriff", 
                font=("Arial", 16, "bold"), bg='white', fg='#333').pack(anchor='w', pady=(0, 15))
        
        # Action Buttons Grid
        buttons_frame = tk.Frame(actions_content, bg='white')
        buttons_frame.pack(fill='x')
        
        self.job_request_button = tk.Button(buttons_frame, text="🚛 Neuen Auftrag anfordern", 
                                           font=("Arial", 12, "bold"), bg='#4caf50', fg='white',
                                           relief='flat', padx=20, pady=12, width=25,
                                           activebackground='#45a049', command=self.request_netto_job)
        self.job_request_button.grid(row=0, column=0, padx=(0, 10), pady=5, sticky='w')
        
        stats_btn = tk.Button(buttons_frame, text="📊 Leistungsübersicht", 
                             font=("Arial", 12), bg='#e0e0e0', fg='#666',
                             relief='flat', padx=20, pady=12, width=25, state='disabled')
        stats_btn.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        schedule_btn = tk.Button(buttons_frame, text="📅 Dienstplan", 
                                font=("Arial", 12), bg='#e0e0e0', fg='#666',
                                relief='flat', padx=20, pady=12, width=25, state='disabled')
        schedule_btn.grid(row=1, column=0, padx=(0, 10), pady=5, sticky='w')
        
        messages_btn = tk.Button(buttons_frame, text="💬 Nachrichten", 
                                font=("Arial", 12), bg='#e0e0e0', fg='#666',
                                relief='flat', padx=20, pady=12, width=25, state='disabled')
        messages_btn.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        
        # Status Section
        status_frame = tk.Frame(main_content, bg='white', relief='solid', bd=1)
        status_frame.pack(fill='x', pady=(0, 20))
        
        status_content = tk.Frame(status_frame, bg='white')
        status_content.pack(fill='x', padx=25, pady=20)
        
        tk.Label(status_content, text="Auftragsstatus", 
                font=("Arial", 16, "bold"), bg='white', fg='#333').pack(anchor='w', pady=(0, 10))
        
        self.intranet_status_label = tk
        self.intranet_status_label = tk.Label(status_content, text="Bereit für Ihren nächsten Auftrag.", 
                                             font=("Arial", 12), bg='white', fg='#666')
        self.intranet_status_label.pack(anchor='w')
        
        # News Section
        news_frame = tk.Frame(main_content, bg='white', relief='solid', bd=1)
        news_frame.pack(fill='x')
        
        news_content = tk.Frame(news_frame, bg='white')
        news_content.pack(fill='x', padx=25, pady=20)
        
        tk.Label(news_content, text="Aktuelle Informationen", 
                font=("Arial", 16, "bold"), bg='white', fg='#333').pack(anchor='w', pady=(0, 15))
        
        news_items = [
            "📢 Neue Sicherheitsrichtlinien für Lieferfahrzeuge ab nächster Woche",
            "🎉 Mitarbeiter des Monats: Herzlichen Glückwunsch an das Team Hamburg!",
            "⚠️ Baustelle auf A7: Bitte alternative Routen nutzen"
        ]
        
        for news in news_items:
            news_item = tk.Frame(news_content, bg='#f8f9fa', relief='solid', bd=1)
            news_item.pack(fill='x', pady=2)
            tk.Label(news_item, text=news, font=("Arial", 10), bg='#f8f9fa', fg='#333',
                    anchor='w').pack(fill='x', padx=15, pady=8)
        
        # Footer
        footer_frame = tk.Frame(self.netto_intranet_screen, bg='#333333', height=50)
        footer_frame.pack(side='bottom', fill='x')
        footer_frame.pack_propagate(False)
        
        back_btn = tk.Button(footer_frame, text="← Browser schließen", 
                            font=("Arial", 11), bg='#555', fg='white', relief='flat',
                            padx=15, pady=8, command=lambda: self.show_screen("desktop"))
        back_btn.pack(side='left', padx=20, pady=10)

    def request_netto_job(self):
        if self.career_manager:
            self.job_request_button.config(state="disabled", bg="#cccccc", fg="#666")
            self.intranet_status_label.config(text="🔄 Suche nach verfügbaren Aufträgen...")
            threading.Thread(target=self.career_manager.find_company_job, daemon=True).start()
            
    def update_intranet_status(self, message):
        def _update():
            self.intranet_status_label.config(text=message)
            # Re-enable button when search is finished
            if "gefunden" in message or "verfügbar" in message or "Fehler" in message:
                self.job_request_button.config(state="normal", bg="#4caf50", fg="white")
        self.window.after(0, _update)

    def monitor_files(self):
       career_data_path = DATA_DIR / "career_data.json"
       last_career_check = 0
       while self.monitoring:
           try:
               if LAPTOP_MAIL_FILE.exists():
                   stat = os.path.getmtime(LAPTOP_MAIL_FILE)
                   if stat != self.last_mail_check:
                       self.last_mail_check = stat
                       if self.visible and self.current_screen == "mail":
                           self.window.after(0, self.load_emails)
               
               if career_data_path.exists():
                   stat = os.path.getmtime(career_data_path)
                   if stat != last_career_check:
                       last_career_check = stat
                       with open(career_data_path, 'r', encoding='utf-8') as f:
                           self.career_data = json.load(f)
           except Exception as e:
               print(f"File monitoring Fehler: {e}")
           time.sleep(1)

    def setup_keyboard_hooks(self, enable):
        if enable: 
            keyboard.on_press_key('backspace', self.go_back, suppress=True)
        else: 
            keyboard.unhook_key('backspace')

    def go_back(self, e=None):
        back_map = {
            "mail": "desktop",
            "browser": "desktop",
            "netto_career": "browser",
            "netto_intranet": "browser"
        }
        if target := back_map.get(self.current_screen):
            self.show_screen(target)
        else:
            self.toggle_visibility()

    def toggle_visibility(self):
        if self.animation_running: return
        self.visible = not self.visible
        self.setup_keyboard_hooks(self.visible)
        start_y, end_y = (self.target_y, self.hidden_y) if not self.visible else (self.hidden_y, self.target_y)
        self.animate_slide(start_y, end_y)

    def is_visible(self): return self.visible

    def animate_slide(self, start_y, end_y):
        self.animation_running = True
        start_time = time.time()
        duration = 0.5
        def animate():
            progress = min((time.time() - start_time) / duration, 1.0)
            eased = 1 - (1 - progress) ** 3
            current_y = start_y + (end_y - start_y) * eased
            self.window.geometry(f"{LAPTOP_WIDTH}x{LAPTOP_HEIGHT}+{self.target_x}+{int(current_y)}")
            if progress < 1.0: self.window.after(16, animate)
            else: self.animation_running = False
        animate()

    def play_fullscreen_video(self, video_path, on_complete_callback):
        if not VIDEO_LIBS_AVAILABLE:
            print("FEHLER: OpenCV nicht installiert. Video kann nicht abgespielt werden.")
            messagebox.showerror("Video Fehler", "OpenCV ist nicht installiert.")
            if on_complete_callback: on_complete_callback()
            return

        video_path_full = str(DATA_DIR.parent / video_path)
        if not os.path.exists(video_path_full):
            print(f"FEHLER: Videodatei nicht gefunden: {video_path_full}")
            if on_complete_callback: on_complete_callback()
            return

        video_window = tk.Toplevel(self.window)
        video_window.overrideredirect(True)

        screen_width = video_window.winfo_screenwidth()
        screen_height = video_window.winfo_screenheight()
        video_window.geometry(f"{screen_width}x{screen_height}+0+0")
        video_window.wm_attributes('-topmost', True)
        video_window.focus_force()
        video_window.configure(bg='black')

        canvas = tk.Canvas(video_window, bg='black', highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        # Video-Steuerung
        self.video_playing = True

        def close_video(event=None):
            nonlocal on_complete_callback
            self.video_playing = False
            if on_complete_callback:
                callback = on_complete_callback
                on_complete_callback = None
                callback()

            if 'cap' in locals() and cap.isOpened():
                cap.release()
            video_window.destroy()

        video_window.bind("<Escape>", close_video)

        try:
            cap = cv2.VideoCapture(video_path_full)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30
            frame_delay = 1.0 / fps  # Sekunden zwischen Frames

            print(f"Video FPS: {fps}, Frame Delay: {frame_delay:.3f}s")

        except Exception as e:
            print(f"Fehler beim Öffnen des Videos: {e}")
            close_video()
            return

        def video_thread():
            """Separater Thread für präzise Video-Wiedergabe"""
            import time

            while self.video_playing:
                start_time = time.time()

                ret, frame = cap.read()
                if not ret:
                    # Video zu Ende
                    video_window.after(0, close_video)
                    break
                
                # Frame verarbeiten
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_h, frame_w, _ = frame.shape

                ratio = min(screen_width / frame_w, screen_height / frame_h)
                new_w, new_h = int(frame_w * ratio), int(frame_h * ratio)
                resized_frame = cv2.resize(frame, (new_w, new_h))

                from PIL import Image, ImageTk
                img = Image.fromarray(resized_frame)
                imgtk = ImageTk.PhotoImage(image=img)

                # Frame im Hauptthread anzeigen
                def update_canvas():
                    if video_window.winfo_exists():
                        canvas.delete("all")
                        canvas.create_image(screen_width // 2, screen_height // 2, anchor='center', image=imgtk)
                        canvas.imgtk = imgtk

                try:
                    video_window.after(0, update_canvas)
                except:
                    break
                
                # Präzises Timing
                elapsed = time.time() - start_time
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        # Video-Thread starten
        threading.Thread(target=video_thread, daemon=True).start()


    def close(self):
        self.monitoring = False
        try: keyboard.unhook_all()
        except: pass
