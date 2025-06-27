#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETS2 Immersion Hub - Konfigurations-Editor
Ermöglicht einfache Änderung der Einstellungen ohne Code-Editor
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import re
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

try:
    from getMyProfileDone import ProfileTransferTool
    PROFILE_TRANSFER_AVAILABLE = True
except ImportError:
    PROFILE_TRANSFER_AVAILABLE = False

class ConfigEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ETS2 Immersion Hub - Konfiguration")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Style konfigurieren
        self.setup_styles()
        
        # Verfügbare Profile
        self.available_profiles = {}
        
        # Lade aktuelle Konfiguration
        self.load_current_config()
        
        # Erstelle GUI
        self.create_widgets()
        
        # Scanne Profile beim Start
        self.scan_profiles()
    
    def setup_styles(self):
        """Konfiguriert das Aussehen der GUI"""
        style = ttk.Style()
        
        # Moderne Farben
        self.colors = {
            'primary': '#2563eb',
            'secondary': '#64748b',
            'success': '#059669',
            'warning': '#d97706',
            'danger': '#dc2626',
            'light': '#f8fafc',
            'dark': '#1e293b'
        }
        
        # Button Styles
        style.configure('Primary.TButton', foreground='black', background=self.colors['primary'])
        style.configure('Success.TButton', foreground='black', background=self.colors['success'])
        style.configure('Warning.TButton', foreground='black', background=self.colors['warning'])        # Map styles to themes
        style.map('Primary.TButton',
                 background=[('active', '#1d4ed8'), ('pressed', '#1e40af')])
        style.map('Success.TButton',
                 background=[('active', '#047857'), ('pressed', '#065f46')])
        
        # LabelFrame Style
        style.configure('Card.TLabelframe', relief='solid', borderwidth=1)
        style.configure('Card.TLabelframe.Label', font=('Segoe UI', 10, 'bold'))
    
    def load_current_config(self):
        """Lädt die aktuelle Konfiguration aus config.py"""
        try:
            from src.config import (
                PROFILE_PATH, TELEMETRY_URL, 
                PHONE_WIDTH, PHONE_HEIGHT,
                LAPTOP_WIDTH, LAPTOP_HEIGHT, PHONE_MESSAGE_FILE,
                LAPTOP_MAIL_FILE, ETS2_LOG_FILE
            )
            
            # Versuche TELEMETRY_SERVER_EXE zu laden, falls vorhanden
            try:
                from src.config import TELEMETRY_SERVER_EXE
                telemetry_server_exe = str(TELEMETRY_SERVER_EXE)
            except ImportError:
                telemetry_server_exe = ""
            
            self.config = {
                'profile_path': str(PROFILE_PATH),
                'telemetry_url': TELEMETRY_URL,
                'telemetry_server_exe': telemetry_server_exe,
                'phone_width': PHONE_WIDTH,
                'phone_height': PHONE_HEIGHT,
                'laptop_width': LAPTOP_WIDTH,
                'laptop_height': LAPTOP_HEIGHT,
                'phone_message_file': str(PHONE_MESSAGE_FILE),
                'laptop_mail_file': str(LAPTOP_MAIL_FILE),
                'ets2_log_file': str(ETS2_LOG_FILE)
            }
            
        except ImportError as e:
            messagebox.showerror("Fehler", f"Konfiguration konnte nicht geladen werden: {e}")
            self.config = {}
    
    def create_widgets(self):
        """Erstellt die GUI-Elemente"""
        # Hauptcontainer mit Padding
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(main_frame)
        
        # Scrollbarer Bereich
        self.create_scrollable_area(main_frame)
        
        # Footer mit Buttons
        self.create_footer(main_frame)
    
    def create_header(self, parent):
        """Erstellt den Header-Bereich"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Titel
        title_label = ttk.Label(header_frame, text="🎮 ETS2 Immersion Hub", 
                               font=('Segoe UI', 18, 'bold'))
        title_label.pack(side='left')
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Konfiguration", 
                                  font=('Segoe UI', 12), foreground=self.colors['secondary'])
        subtitle_label.pack(side='left', padx=(10, 0))
        
        # Status
        self.status_label = ttk.Label(header_frame, text="", 
                                     font=('Segoe UI', 9), foreground=self.colors['success'])
        self.status_label.pack(side='right')
    
    def create_scrollable_area(self, parent):
        """Erstellt den scrollbaren Hauptbereich"""
        # Container für Canvas und Scrollbar
        scroll_container = ttk.Frame(parent)
        scroll_container.pack(fill='both', expand=True)
        
        # Canvas und Scrollbar
        canvas = tk.Canvas(scroll_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        # Scrolling konfigurieren
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mausrad-Scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Pack canvas und scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Erstelle Sektionen
        self.create_profile_section()
        self.create_telemetry_section()
        self.create_file_section()
        self.create_ui_section()
    
    def create_footer(self, parent):
        """Erstellt den Footer mit Buttons"""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill='x', pady=(20, 0))
        
        # Separator
        separator = ttk.Separator(footer_frame, orient='horizontal')
        separator.pack(fill='x', pady=(0, 15))
        
        # Button Container
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack(fill='x')
        
        # Links: Aktions-Buttons
        left_frame = ttk.Frame(button_frame)
        left_frame.pack(side='left')
        
        scan_btn = ttk.Button(left_frame, text="🔍 Profile scannen", 
                             command=self.scan_profiles, style='Primary.TButton')
        scan_btn.pack(side='left', padx=(0, 10))        
        if PROFILE_TRANSFER_AVAILABLE:
            ttk.Button(left_frame, text="🔄 Profile Transfer", 
                      command=self.open_profile_transfer).pack(side='left')
        
        # Rechts: Speichern/Zurücksetzen
        right_frame = ttk.Frame(button_frame)
        right_frame.pack(side='right')
        
        save_btn = ttk.Button(right_frame, text="💾 Speichern", 
                             command=self.save_config, style='Success.TButton')
        save_btn.pack(side='right')
    
    def create_profile_section(self):
        """Erstellt die Profile-Sektion"""
        profile_frame = ttk.LabelFrame(self.scrollable_frame, text="🎮 ETS2 Profil", 
                                      padding=15, style='Card.TLabelframe')
        profile_frame.pack(fill='x', pady=(0, 15))
        
        # Profile-Dropdown
        profile_select_frame = ttk.Frame(profile_frame)
        profile_select_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(profile_select_frame, text="Aktives Profil:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_select_frame, textvariable=self.profile_var, 
                                         font=('Segoe UI', 9), state='readonly')
        self.profile_combo.pack(fill='x', pady=(5, 0))
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_selected)
        
        # Profil-Info
        self.profile_info_frame = ttk.Frame(profile_frame)
        self.profile_info_frame.pack(fill='x', pady=(10, 0))
        
        self.profile_info_label = ttk.Label(self.profile_info_frame, text="", 
                                           font=('Segoe UI', 9), foreground=self.colors['secondary'])
        self.profile_info_label.pack(anchor='w')
    
    def create_telemetry_section(self):
        """Erstellt die Telemetrie-Sektion"""
        telemetry_frame = ttk.LabelFrame(self.scrollable_frame, text="🌐 Telemetrie", 
                                        padding=15, style='Card.TLabelframe')
        telemetry_frame.pack(fill='x', pady=(0, 15))
        
        # Telemetry Server EXE
        exe_frame = ttk.Frame(telemetry_frame)
        exe_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(exe_frame, text="Telemetry Server EXE:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        exe_path_frame = ttk.Frame(exe_frame)
        exe_path_frame.pack(fill='x', pady=(5, 0))
        
        self.telemetry_exe_var = tk.StringVar(value=self.config.get('telemetry_server_exe', ''))
        self.telemetry_exe_entry = ttk.Entry(exe_path_frame, textvariable=self.telemetry_exe_var, 
                                            font=('Segoe UI', 9), state='readonly')
        self.telemetry_exe_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(exe_path_frame, text="📁 Durchsuchen", 
                  command=self.browse_telemetry_exe).pack(side='right', padx=(10, 0))
        
        # Hinweis
        hint_label = ttk.Label(exe_frame, 
                              text="💡 Hinweis: Normalerweise unter ets2-telemetry-server\\server\\Ets2Telemetry.exe",
                              font=('Segoe UI', 8), foreground=self.colors['secondary'])
        hint_label.pack(anchor='w', pady=(5, 0))
        
        # Separator
        ttk.Separator(telemetry_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # Telemetry URL
        url_frame = ttk.Frame(telemetry_frame)
        url_frame.pack(fill='x')
        
        ttk.Label(url_frame, text="Telemetrie URL:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        # URL-Modus Toggle
        mode_frame = ttk.Frame(url_frame)
        mode_frame.pack(fill='x', pady=(5, 10))
        
        self.simple_mode = tk.BooleanVar(value=True)
        self.mode_check = ttk.Checkbutton(mode_frame, text="Erweiterte URL-Eingabe", 
                                         variable=self.simple_mode, 
                                         command=self.toggle_url_mode)
        self.mode_check.pack(anchor='w')
        
        # IP Eingabe (einfach)
        self.ip_frame = ttk.Frame(url_frame)
        
        ip_label_frame = ttk.Frame(self.ip_frame)
        ip_label_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(ip_label_frame, text="IP-Adresse:", font=('Segoe UI', 9)).pack(side='left')
        
        self.ip_var = tk.StringVar()
        self.ip_entry = ttk.Entry(self.ip_frame, textvariable=self.ip_var, 
                                 font=('Segoe UI', 9), width=20)
        self.ip_entry.pack(anchor='w')
        
        # URL Eingabe (erweitert)
        self.url_frame = ttk.Frame(url_frame)
        
        url_label_frame = ttk.Frame(self.url_frame)
        url_label_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(url_label_frame, text="Vollständige URL:", font=('Segoe UI', 9)).pack(anchor='w')
        
        self.url_var = tk.StringVar(value=self.config.get('telemetry_url', ''))
        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.url_var, 
                                  font=('Segoe UI', 9))
        self.url_entry.pack(fill='x')
        
        # Initialisiere URL-Modus
        self.parse_telemetry_url()
    
    def create_file_section(self):
        """Erstellt die Datei-Sektion"""
        file_frame = ttk.LabelFrame(self.scrollable_frame, text="📁 Dateien", 
                                   padding=15, style='Card.TLabelframe')
        file_frame.pack(fill='x', pady=(0, 15))
        
        files = [
            ("📱 Handy Nachrichten:", "phone_message_file"),
            ("💻 Laptop E-Mails:", "laptop_mail_file"),
            ("📋 ETS2 Log:", "ets2_log_file")
        ]
        
        for i, (label_text, config_key) in enumerate(files):
            row_frame = ttk.Frame(file_frame)
            row_frame.pack(fill='x', pady=(0 if i == 0 else 8, 0))
            
            # Label
            label_frame = ttk.Frame(row_frame)
            label_frame.pack(fill='x', pady=(0, 3))
            ttk.Label(label_frame, text=label_text, font=('Segoe UI', 9, 'bold')).pack(anchor='w')
            
            # Dateipfad
            path_frame = ttk.Frame(row_frame)
            path_frame.pack(fill='x')
            
            file_path = self.config.get(config_key, "")
            file_label = ttk.Label(path_frame, text=file_path, 
                                  font=('Segoe UI', 8), foreground=self.colors['primary'], 
                                  cursor='hand2')
            file_label.pack(side='left', fill='x', expand=True)
            
            # Status Icon
            status_icon = "✅" if Path(file_path).exists() else "❌"
            ttk.Label(path_frame, text=status_icon, font=('Segoe UI', 10)).pack(side='right')
            
            # Klick zum Öffnen
            file_label.bind('<Button-1>', lambda e, path=file_path: self.open_file(path))
    
    def create_ui_section(self):
        """Erstellt die UI-Sektion"""
        ui_frame = ttk.LabelFrame(self.scrollable_frame, text="🖥️ Benutzeroberfläche", 
                                 padding=15, style='Card.TLabelframe')
        ui_frame.pack(fill='x')
        
        # Grid Layout für bessere Organisation
        ui_frame.columnconfigure(1, weight=1)
        
        # Handy Größe
        phone_label = ttk.Label(ui_frame, text="📱 Handy Größe", 
                               font=('Segoe UI', 10, 'bold'))
        phone_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        phone_frame = ttk.Frame(ui_frame)
        phone_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        # Breite
        ttk.Label(phone_frame, text="Breite:", font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w')
        self.phone_width_var = tk.StringVar(value=str(self.config.get('phone_width', 320)))
        width_entry = ttk.Entry(phone_frame, textvariable=self.phone_width_var, width=10, font=('Segoe UI', 9))
        width_entry.grid(row=0, column=1, padx=(10, 20), sticky='w')
        
        # Höhe
        ttk.Label(phone_frame, text="Höhe:", font=('Segoe UI', 9)).grid(row=0, column=2, sticky='w')
        self.phone_height_var = tk.StringVar(value=str(self.config.get('phone_height', 550)))
        height_entry = ttk.Entry(phone_frame, textvariable=self.phone_height_var, width=10, font=('Segoe UI', 9))
        height_entry.grid(row=0, column=3, padx=(10, 0), sticky='w')
        
        # Laptop Größe
        laptop_label = ttk.Label(ui_frame, text="💻 Laptop Größe", 
                                font=('Segoe UI', 10, 'bold'))
        laptop_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        laptop_frame = ttk.Frame(ui_frame)
        laptop_frame.grid(row=3, column=0, columnspan=2, sticky='ew')
        
        # Breite
        ttk.Label(laptop_frame, text="Breite:", font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w')
        self.laptop_width_var = tk.StringVar(value=str(self.config.get('laptop_width', 800)))
        laptop_width_entry = ttk.Entry(laptop_frame, textvariable=self.laptop_width_var, width=10, font=('Segoe UI', 9))
        laptop_width_entry.grid(row=0, column=1, padx=(10, 20), sticky='w')
        
        # Höhe
        ttk.Label(laptop_frame, text="Höhe:", font=('Segoe UI', 9)).grid(row=0, column=2, sticky='w')
        self.laptop_height_var = tk.StringVar(value=str(self.config.get('laptop_height', 500)))
        laptop_height_entry = ttk.Entry(laptop_frame, textvariable=self.laptop_height_var, width=10, font=('Segoe UI', 9))
        laptop_height_entry.grid(row=0, column=3, padx=(10, 0), sticky='w')
    
    def browse_telemetry_exe(self):
        """Öffnet Datei-Dialog für Telemetry Server EXE"""
        file_path = filedialog.askopenfilename(
            title="Telemetry Server EXE auswählen",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ],
            initialdir=str(Path.home())
        )
        
        if file_path:
            self.telemetry_exe_var.set(file_path)
            self.update_status("Telemetry Server EXE ausgewählt", "success")
    
    def scan_profiles(self):
        """Scannt alle verfügbaren ETS2 Profile"""
        try:
            self.update_status("Scanne Profile...", "info")
            
            # Finde Profile-Verzeichnis
            profiles_base = Path.home() / "Documents" / "Euro Truck Simulator 2" / "profiles"
            
            if not profiles_base.exists():
                messagebox.showwarning("Warnung", f"Profile-Verzeichnis nicht gefunden: {profiles_base}")
                self.update_status("Profile-Verzeichnis nicht gefunden", "warning")
                return
            
            self.available_profiles = {}
            
            for profile_dir in profiles_base.iterdir():
                if profile_dir.is_dir():
                    profile_info = self.extract_profile_info(profile_dir)
                    if profile_info:
                        self.available_profiles[profile_dir.name] = profile_info
            
            # Update Dropdown
            profile_names = []
            for profile_id, info in self.available_profiles.items():
                display_name = f"{info['name']} ({info['company']}) - ID: {profile_id}"
                profile_names.append(display_name)
            
            self.profile_combo['values'] = profile_names
            
            # Setze aktuelles Profil
            current_path = Path(self.config.get('profile_path', ''))
            current_id = current_path.name if current_path.exists() else None
            
            if current_id and current_id in self.available_profiles:
                for i, (profile_id, _) in enumerate(self.available_profiles.items()):
                    if profile_id == current_id:
                        self.profile_combo.current(i)
                        self.on_profile_selected(None)
                        break
            
            self.update_status(f"{len(self.available_profiles)} Profile gefunden", "success")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Scannen der Profile: {e}")
            self.update_status("Fehler beim Scannen", "error")
    
    def extract_profile_info(self, profile_dir):
        """Extrahiert Profilinformationen aus profile.sii"""
        profile_sii = profile_dir / "profile.sii"
        
        if not profile_sii.exists():
            return None
        
        try:
            # Entschlüssele profile.sii
            from src.config import SII_DECRYPT_EXE
            
            if not SII_DECRYPT_EXE.exists():
                return None
            
            temp_file = "temp_profile_decrypt.txt"
            
            result = subprocess.run(
                [str(SII_DECRYPT_EXE), str(profile_sii), temp_file],
                capture_output=True, text=True, encoding='utf-8'
            )
            
            if result.returncode != 0:
                return None
            
            # Parse entschlüsselte Datei
            with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extrahiere Informationen
            name_match = re.search(r'profile_name:\s*([^\s\n]+)', content)
            company_match = re.search(r'company_name:\s*([^\s\n]+)', content)
            
            profile_name = name_match.group(1) if name_match else "Unbekannt"
            company_name = company_match.group(1) if company_match else "Keine Firma"
            
            # Cleanup
            if Path(temp_file).exists():
                os.remove(temp_file)
            
            return {
                'name': profile_name,
                'company': company_name,
                'path': profile_dir
            }
            
        except Exception as e:
            print(f"Fehler beim Extrahieren von Profil {profile_dir.name}: {e}")
            return None
    
    def parse_telemetry_url(self):
        """Parst die Telemetrie-URL und setzt den entsprechenden Modus"""
        url = self.config.get('telemetry_url', '')
        
        # Versuche IP zu extrahieren
        ip_match = re.search(r'http://([^:]+):', url)
        
        if ip_match:
            ip = ip_match.group(1)
            self.ip_var.set(ip)
            self.simple_mode.set(False)  # Einfacher Modus als Standard
        else:
            self.simple_mode.set(True)  # Erweitert wenn keine IP erkannt
        
        self.toggle_url_mode()
    
    def toggle_url_mode(self):
        """Wechselt zwischen einfachem und erweitertem URL-Modus"""
        if not self.simple_mode.get():
            # Einfacher Modus - nur IP
            self.ip_frame.pack(fill='x', pady=(5, 0))
            self.url_frame.pack_forget()
        else:
            # Erweiterter Modus - ganze URL
            self.url_frame.pack(fill='x', pady=(5, 0))
            self.ip_frame.pack_forget()
    
    def on_profile_selected(self, event):
        """Wird aufgerufen wenn ein Profil ausgewählt wird"""
        selection = self.profile_combo.current()
        if selection >= 0:
            profile_id = list(self.available_profiles.keys())[selection]
            profile_info = self.available_profiles[profile_id]
            
            # Update Info-Label
            info_text = f"Firma: {profile_info['company']} | Pfad: {profile_info['path']}"
            self.profile_info_label.config(text=info_text)
            self.update_status("Profil ausgewählt", "success")
    
    def open_file(self, file_path):
        """Öffnet eine Datei mit dem Standard-Editor"""
        try:
            if Path(file_path).exists():
                os.startfile(file_path)  # Windows
                self.update_status("Datei geöffnet", "success")
            else:
                messagebox.showwarning("Warnung", f"Datei nicht gefunden: {file_path}")
                self.update_status("Datei nicht gefunden", "warning")
        except Exception as e:
            messagebox.showerror("Fehler", f"Datei konnte nicht geöffnet werden: {e}")
            self.update_status("Fehler beim Öffnen", "error")
    
    def open_profile_transfer(self):
        """Öffnet das Profile Transfer Tool"""
        try:
            ProfileTransferTool(self.root)
        except Exception as e:
            messagebox.showerror("Fehler", f"Profile Transfer Tool konnte nicht geöffnet werden: {e}")
            self.update_status("Fehler beim Öffnen des Transfer Tools", "error")
    
    def update_status(self, message, status_type="info"):
        """Aktualisiert die Statusanzeige"""
        colors = {
            "info": self.colors['secondary'],
            "success": self.colors['success'],
            "warning": self.colors['warning'],
            "error": self.colors['danger']
        }
        
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        self.status_label.config(
            text=f"{icons.get(status_type, '')} {message}",
            foreground=colors.get(status_type, self.colors['secondary'])
        )
        
        # Auto-clear nach 3 Sekunden
        self.root.after(3000, lambda: self.status_label.config(text=""))
    
    def save_config(self):
        """Speichert die Konfiguration in config.py"""
        try:
            self.update_status("Speichere Konfiguration...", "info")
            
            # Sammle alle Werte
            new_config = {}
            
            # Profil
            selection = self.profile_combo.current()
            if selection >= 0:
                profile_id = list(self.available_profiles.keys())[selection]
                profile_path = self.available_profiles[profile_id]['path']
                new_config['PROFILE_PATH'] = f'Path(r"{profile_path}")'
            
            # Telemetry Server EXE
            telemetry_exe = self.telemetry_exe_var.get().strip()
            if telemetry_exe:
                new_config['TELEMETRY_SERVER_EXE'] = f'Path(r"{telemetry_exe}")'
            
            # Telemetrie URL
            if not self.simple_mode.get():
                ip = self.ip_var.get().strip()
                if ip:
                    new_config['TELEMETRY_URL'] = f'"http://{ip}:25555/api/ets2/telemetry"'
            else:
                url = self.url_var.get().strip()
                if url:
                    new_config['TELEMETRY_URL'] = f'"{url}"'
            
            # UI Größen
            try:
                phone_width = int(self.phone_width_var.get())
                phone_height = int(self.phone_height_var.get())
                laptop_width = int(self.laptop_width_var.get())
                laptop_height = int(self.laptop_height_var.get())
                
                new_config['PHONE_WIDTH'] = str(phone_width)
                new_config['PHONE_HEIGHT'] = str(phone_height)
                new_config['LAPTOP_WIDTH'] = str(laptop_width)
                new_config['LAPTOP_HEIGHT'] = str(laptop_height)
                
            except ValueError:
                messagebox.showerror("Fehler", "UI-Größen müssen Zahlen sein!")
                self.update_status("Ungültige UI-Größen", "error")
                return
            
            # Schreibe config.py
            self.write_config_file(new_config)
            
            self.update_status("Konfiguration gespeichert!", "success")
            messagebox.showinfo("Erfolg", "Konfiguration erfolgreich gespeichert!")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
            self.update_status("Fehler beim Speichern", "error")
    
    def write_config_file(self, new_config):
        """Schreibt die neue Konfiguration in config.py"""
        config_path = Path("src/config.py")
        
        # Lese aktuelle config.py
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Ersetze Werte oder füge neue hinzu
        new_lines = []
        updated_keys = set()
        
        for line in lines:
            line_updated = False
            
            for key, value in new_config.items():
                if line.strip().startswith(f"{key} ="):
                    new_lines.append(f"{key} = {value}\n")
                    updated_keys.add(key)
                    line_updated = True
                    break
            
            if not line_updated:
                new_lines.append(line)
        
        # Füge neue Konfigurationsschlüssel hinzu, die noch nicht existieren
        for key, value in new_config.items():
            if key not in updated_keys:
                # Füge vor dem OFFENCE_TYPE_MAP ein
                insert_index = len(new_lines)
                for i, line in enumerate(new_lines):
                    if line.strip().startswith("OFFENCE_TYPE_MAP"):
                        insert_index = i
                        break
                
                new_lines.insert(insert_index, f"{key} = {value}\n")
                new_lines.insert(insert_index + 1, "\n")
        
        # Schreibe zurück
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    def reset_config(self):
        """Setzt die Konfiguration zurück"""
        if messagebox.askyesno("Bestätigung", "Möchten Sie alle Änderungen zurücksetzen?"):
            self.load_current_config()
            
            # Reset GUI-Elemente
            self.phone_width_var.set(str(self.config.get('phone_width', 320)))
            self.phone_height_var.set(str(self.config.get('phone_height', 550)))
            self.laptop_width_var.set(str(self.config.get('laptop_width', 800)))
            self.laptop_height_var.set(str(self.config.get('laptop_height', 500)))
            self.telemetry_exe_var.set(self.config.get('telemetry_server_exe', ''))
            
            self.parse_telemetry_url()
            self.scan_profiles()
            
            self.update_status("Konfiguration zurückgesetzt", "success")
    
    def run(self):
        """Startet die GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = ConfigEditor()
        app.run()
    except Exception as e:
        print(f"Fehler beim Starten der Anwendung: {e}")
        input("Drücken Sie Enter zum Beenden...")
