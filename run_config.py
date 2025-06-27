#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETS2 Immersion Hub - Konfigurations-Editor
Ermöglicht einfache Änderung der Einstellungen ohne Code-Editor
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Verfügbare Profile
        self.available_profiles = {}
        
        # Lade aktuelle Konfiguration
        self.load_current_config()
        
        # Erstelle GUI
        self.create_widgets()
        
        # Scanne Profile beim Start
        self.scan_profiles()
    
    def load_current_config(self):
        """Lädt die aktuelle Konfiguration aus config.py"""
        try:
            from src.config import (
                PROFILE_PATH, TELEMETRY_URL, 
                PHONE_WIDTH, PHONE_HEIGHT,
                LAPTOP_WIDTH, LAPTOP_HEIGHT, PHONE_MESSAGE_FILE,
                LAPTOP_MAIL_FILE, ETS2_LOG_FILE
            )
            
            self.config = {
                'profile_path': str(PROFILE_PATH),
                'telemetry_url': TELEMETRY_URL,
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
        # Hauptcontainer
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Titel
        title_label = ttk.Label(main_frame, text="ETS2 Immersion Hub - Konfiguration", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Scrollbarer Bereich
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Profile Sektion
        self.create_profile_section(scrollable_frame)
        
        # Datei Sektion
        self.create_file_section(scrollable_frame)
        
        # Netzwerk Sektion
        self.create_network_section(scrollable_frame)
        
        # UI Sektion
        self.create_ui_section(scrollable_frame)
        
        # Pack canvas und scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
# Buttons am unteren Rand
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=15, pady=(10, 15))

        ttk.Button(button_frame, text="💾 Speichern", command=self.save_config).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="🔄 Zurücksetzen", command=self.reset_config).pack(side='right')

        ttk.Button(button_frame, text="🔍 Profile neu scannen", command=self.scan_profiles).pack(side='left')

            # Links: Profile-bezogene Buttons
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side='left')

        ttk.Button(left_buttons, text="🔍 Profile neu scannen", command=self.scan_profiles).pack(side='left')

        if PROFILE_TRANSFER_AVAILABLE:
            ttk.Button(left_buttons, text="🔄 Profile Transfer", 
                      command=self.open_profile_transfer).pack(side='left', padx=(10, 0))
            
    def open_profile_transfer(self):
        try:
            ProfileTransferTool(self.root)
        except Exception as e:
            messagebox.showerror("Fehler", f"Profile Transfer Tool konnte nicht geöffnet werden: {e}")


    def create_profile_section(self, parent):
        """Erstellt die Profile-Sektion"""
        profile_frame = ttk.LabelFrame(parent, text="🎮 ETS2 Profil", padding=10)
        profile_frame.pack(fill='x', pady=(0, 15))
        
        # Profile-Dropdown
        ttk.Label(profile_frame, text="Aktives Profil:").pack(anchor='w')
        
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, 
                                         width=60, state='readonly')
        self.profile_combo.pack(fill='x', pady=(5, 10))
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_selected)
        
        # Profil-Info
        self.profile_info_label = ttk.Label(profile_frame, text="", foreground='gray')
        self.profile_info_label.pack(anchor='w')
    
    def create_file_section(self, parent):
        """Erstellt die Datei-Sektion"""
        file_frame = ttk.LabelFrame(parent, text="📁 Dateien", padding=10)
        file_frame.pack(fill='x', pady=(0, 15))
        
        files = [
            ("Handy Nachrichten:", "phone_message_file"),
            ("Laptop E-Mails:", "laptop_mail_file"),
            ("ETS2 Log:", "ets2_log_file")
        ]
        
        for label_text, config_key in files:
            row_frame = ttk.Frame(file_frame)
            row_frame.pack(fill='x', pady=2)
            
            ttk.Label(row_frame, text=label_text, width=20).pack(side='left')
            
            file_label = ttk.Label(row_frame, text=self.config.get(config_key, ""), 
                                  foreground='blue', cursor='hand2')
            file_label.pack(side='left', fill='x', expand=True, padx=(10, 0))
            
            # Klick zum Öffnen
            file_label.bind('<Button-1>', lambda e, path=self.config.get(config_key, ""): self.open_file(path))
    
    def create_network_section(self, parent):
        """Erstellt die Netzwerk-Sektion"""
        network_frame = ttk.LabelFrame(parent, text="🌐 Netzwerk", padding=10)
        network_frame.pack(fill='x', pady=(0, 15))
        
        # Telemetry URL
        ttk.Label(network_frame, text="Telemetrie URL:").pack(anchor='w')
        
        url_frame = ttk.Frame(network_frame)
        url_frame.pack(fill='x', pady=(5, 10))
        
        # Einfacher Modus (nur IP)
        self.simple_mode = tk.BooleanVar(value=True)
        self.advanced_check = ttk.Checkbutton(url_frame, text="Erweitert (ganze URL)", 
                                            variable=self.simple_mode, 
                                            command=self.toggle_url_mode)
        self.advanced_check.pack(anchor='w')
        
        # IP Eingabe (einfach)
        self.ip_frame = ttk.Frame(url_frame)
        self.ip_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(self.ip_frame, text="IP-Adresse:").pack(side='left')
        self.ip_var = tk.StringVar()
        self.ip_entry = ttk.Entry(self.ip_frame, textvariable=self.ip_var, width=20)
        self.ip_entry.pack(side='left', padx=(10, 0))
        
        # URL Eingabe (erweitert)
        self.url_frame = ttk.Frame(url_frame)
        
        ttk.Label(self.url_frame, text="Vollständige URL:").pack(anchor='w')
        self.url_var = tk.StringVar(value=self.config.get('telemetry_url', ''))
        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.url_var, width=60)
        self.url_entry.pack(fill='x', pady=(5, 0))
        
        # Initialisiere URL-Modus
        self.parse_telemetry_url()
    
    def create_ui_section(self, parent):
        """Erstellt die UI-Sektion"""
        ui_frame = ttk.LabelFrame(parent, text="🖥️ Benutzeroberfläche", padding=10)
        ui_frame.pack(fill='x', pady=(0, 15))
        
        # Handy Größe
        phone_frame = ttk.Frame(ui_frame)
        phone_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(phone_frame, text="📱 Handy Größe:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        phone_size_frame = ttk.Frame(phone_frame)
        phone_size_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(phone_size_frame, text="Breite:").pack(side='left')
        self.phone_width_var = tk.StringVar(value=str(self.config.get('phone_width', 320)))
        ttk.Entry(phone_size_frame, textvariable=self.phone_width_var, width=10).pack(side='left', padx=(5, 15))
        
        ttk.Label(phone_size_frame, text="Höhe:").pack(side='left')
        self.phone_height_var = tk.StringVar(value=str(self.config.get('phone_height', 550)))
        ttk.Entry(phone_size_frame, textvariable=self.phone_height_var, width=10).pack(side='left', padx=(5, 0))
        
        # Laptop Größe
        laptop_frame = ttk.Frame(ui_frame)
        laptop_frame.pack(fill='x')
        
        ttk.Label(laptop_frame, text="💻 Laptop Größe:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        laptop_size_frame = ttk.Frame(laptop_frame)
        laptop_size_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(laptop_size_frame, text="Breite:").pack(side='left')
        self.laptop_width_var = tk.StringVar(value=str(self.config.get('laptop_width', 800)))
        ttk.Entry(laptop_size_frame, textvariable=self.laptop_width_var, width=10).pack(side='left', padx=(5, 15))
        
        ttk.Label(laptop_size_frame, text="Höhe:").pack(side='left')
        self.laptop_height_var = tk.StringVar(value=str(self.config.get('laptop_height', 500)))
        ttk.Entry(laptop_size_frame, textvariable=self.laptop_height_var, width=10).pack(side='left', padx=(5, 0))
    
    def scan_profiles(self):
        """Scannt alle verfügbaren ETS2 Profile"""
        try:
            # Finde Profile-Verzeichnis
            profiles_base = Path.home() / "Documents" / "Euro Truck Simulator 2" / "profiles"
            
            if not profiles_base.exists():
                messagebox.showwarning("Warnung", f"Profile-Verzeichnis nicht gefunden: {profiles_base}")
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
                        break
            
            messagebox.showinfo("Erfolg", f"{len(self.available_profiles)} Profile gefunden!")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Scannen der Profile: {e}")
    
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
            self.simple_mode.set(True)
            self.toggle_url_mode()
        else:
            self.simple_mode.set(False)
            self.toggle_url_mode()
    
    def toggle_url_mode(self):
        """Wechselt zwischen einfachem und erweitertem URL-Modus"""
        if self.simple_mode.get():
            # Einfacher Modus - nur IP
            self.ip_frame.pack(fill='x', pady=(5, 0))
            self.url_frame.pack_forget()
            self.advanced_check.config(text="☑️ Erweitert (ganze URL)")
        else:
            # Erweiterter Modus - ganze URL
            self.url_frame.pack(fill='x', pady=(5, 0))
            self.ip_frame.pack_forget()
            self.advanced_check.config(text="☐ Erweitert (ganze URL)")
    
    def on_profile_selected(self, event):
        """Wird aufgerufen wenn ein Profil ausgewählt wird"""
        selection = self.profile_combo.current()
        if selection >= 0:
            profile_id = list(self.available_profiles.keys())[selection]
            profile_info = self.available_profiles[profile_id]
            
            # Update Info-Label
            info_text = f"Firma: {profile_info['company']} | Pfad: {profile_info['path']}"
            self.profile_info_label.config(text=info_text)
    
    def open_file(self, file_path):
        """Öffnet eine Datei mit dem Standard-Editor"""
        try:
            if Path(file_path).exists():
                os.startfile(file_path)  # Windows
            else:
                messagebox.showwarning("Warnung", f"Datei nicht gefunden: {file_path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Datei konnte nicht geöffnet werden: {e}")
    
    def save_config(self):
        """Speichert die Konfiguration in config.py"""
        try:
            # Sammle alle Werte
            new_config = {}
            
            # Profil
            selection = self.profile_combo.current()
            if selection >= 0:
                profile_id = list(self.available_profiles.keys())[selection]
                profile_path = self.available_profiles[profile_id]['path']
                new_config['PROFILE_PATH'] = f'Path(r"{profile_path}")'
            
            # Telemetrie URL
            if self.simple_mode.get():
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
                return
            
            # Schreibe config.py
            self.write_config_file(new_config)
            
            messagebox.showinfo("Erfolg", "Konfiguration erfolgreich gespeichert!")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
    
    def write_config_file(self, new_config):
        """Schreibt die neue Konfiguration in config.py"""
        config_path = Path("src/config.py")
        
        # Lese aktuelle config.py
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Ersetze Werte
        new_lines = []
        for line in lines:
            line_updated = False
            
            for key, value in new_config.items():
                if line.strip().startswith(f"{key} ="):
                    new_lines.append(f"{key} = {value}\n")
                    line_updated = True
                    break
            
            if not line_updated:
                new_lines.append(line)
        
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
            
            self.parse_telemetry_url()
    
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
