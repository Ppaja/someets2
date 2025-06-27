#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETS2 Profile Transfer Tool
Ermöglicht einfaches Übertragen von Einstellungen zwischen ETS2 Profilen
"""

import tkinter as tk
from tkinter import ttk, messagebox
import shutil
import json
from pathlib import Path
from datetime import datetime
import re
import subprocess
import sys

class ProfileTransferTool:
    def __init__(self, parent=None):
        if parent:
            self.window = tk.Toplevel(parent)
            self.window.transient(parent)
            self.window.grab_set()
        else:
            self.window = tk.Tk()
        
        self.window.title("ETS2 Profile Transfer Tool")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        
        # Profile data
        self.profiles = {}
        self.backup_dir = Path("profile_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Transferable files with descriptions
        self.transferable_files = {
            'config.cfg': {
                'name': '⚙️ Spiel-Einstellungen',
                'description': 'Grafik, Audio, Gameplay-Einstellungen',
                'recommended': True,
                'category': 'essential'
            },
            'controls.sii': {
                'name': '🎮 Steuerung & Keybinds',
                'description': 'Tastenbelegung, Controller-Einstellungen',
                'recommended': True,
                'category': 'essential'
            },
            'profile.sii': {
                'name': '👤 Profil-Daten (VORSICHT!)',
                'description': 'Name, Firma, Erfahrung, Geld (!KANN SAVE ZERSTÖREN!)',
                'recommended': False,
                'category': 'gamedata'
            },
            'gearbox_layout_*.sii': {
                'name': '⚙️ Getriebe-Layouts',
                'description': 'Schaltmuster für verschiedene LKW-Getriebe',
                'recommended': False,
                'category': 'vehicle'
            }
        }
        
        self.create_widgets()
        self.scan_profiles()
    
    def create_widgets(self):
        """Erstellt die GUI"""
        # Hauptcontainer
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titel
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(title_frame, text="🔄 ETS2 Profile Transfer Tool", 
                 font=('Arial', 18, 'bold')).pack(side='left')
        
        ttk.Button(title_frame, text="🔍 Profile neu scannen", 
                  command=self.scan_profiles).pack(side='right')
        
        # Profile Auswahl
        profiles_frame = ttk.LabelFrame(main_frame, text="📁 Profile auswählen", padding=15)
        profiles_frame.pack(fill='x', pady=(0, 20))
        
        # Source Profile
        source_frame = ttk.Frame(profiles_frame)
        source_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(source_frame, text="Von (Quelle):", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(source_frame, textvariable=self.source_var, 
                                        width=70, state='readonly')
        self.source_combo.pack(fill='x', pady=(5, 0))
        self.source_combo.bind('<<ComboboxSelected>>', self.on_source_selected)
        
        # Target Profile
        target_frame = ttk.Frame(profiles_frame)
        target_frame.pack(fill='x')
        
        ttk.Label(target_frame, text="Nach (Ziel):", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(target_frame, textvariable=self.target_var, 
                                        width=70, state='readonly')
        self.target_combo.pack(fill='x', pady=(5, 0))
        self.target_combo.bind('<<ComboboxSelected>>', self.on_target_selected)
        
        # Transfer Optionen
        options_frame = ttk.LabelFrame(main_frame, text="📋 Was übertragen?", padding=15)
        options_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Scrollbarer Bereich für Optionen
        canvas = tk.Canvas(options_frame, height=200)
        scrollbar = ttk.Scrollbar(options_frame, orient="vertical", command=canvas.yview)
        self.options_scroll_frame = ttk.Frame(canvas)
        
        self.options_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.options_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.file_vars = {}
        self.create_file_options()
        
        # Quick Select Buttons
        quick_frame = ttk.Frame(options_frame)
        quick_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(quick_frame, text="✅ Empfohlene auswählen", 
                  command=self.select_recommended).pack(side='left', padx=(0, 10))
        ttk.Button(quick_frame, text="❌ Alle abwählen", 
                  command=self.deselect_all).pack(side='left', padx=(0, 10))
        ttk.Button(quick_frame, text="🎮 Nur Einstellungen", 
                  command=self.select_settings_only).pack(side='left')
        
        # Status und Aktionen
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill='x')
        
        # Status Label
        self.status_label = ttk.Label(action_frame, text="Bereit für Transfer", 
                                     foreground='green')
        self.status_label.pack(side='left')
        
        # Action Buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(side='right')
        
        ttk.Button(button_frame, text="💾 Backup erstellen", 
                  command=self.create_backup).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="🔄 Transfer starten", 
                  command=self.start_transfer, 
                  style='Accent.TButton').pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="📂 Backups verwalten", 
                  command=self.manage_backups).pack(side='left')
    
    def create_file_options(self):
        """Erstellt die Datei-Auswahl Optionen"""
        # Clear existing widgets
        for widget in self.options_scroll_frame.winfo_children():
            widget.destroy()
        
        self.file_vars = {}
        
        # Gruppiere nach Kategorien
        categories = {
            'essential': '🔧 Grundeinstellungen',
            'vehicle': '🚛 Fahrzeug-spezifisch',
            'gamedata': '💾 Spieldaten (Vorsicht!)'
        }
        
        for category, category_name in categories.items():
            # Category Header
            cat_frame = ttk.LabelFrame(self.options_scroll_frame, text=category_name, padding=10)
            cat_frame.pack(fill='x', pady=(0, 10))
            
            for file_pattern, file_info in self.transferable_files.items():
                if file_info['category'] == category:
                    self.create_file_option(cat_frame, file_pattern, file_info)
    
    def create_file_option(self, parent, file_pattern, file_info):
        """Erstellt eine einzelne Datei-Option"""
        option_frame = ttk.Frame(parent)
        option_frame.pack(fill='x', pady=2)
        
        # Checkbox
        var = tk.BooleanVar(value=file_info['recommended'])
        self.file_vars[file_pattern] = var
        
        checkbox = ttk.Checkbutton(option_frame, variable=var)
        checkbox.pack(side='left')
        
        # Info Frame
        info_frame = ttk.Frame(option_frame)
        info_frame.pack(side='left', fill='x', expand=True, padx=(10, 0))
        
        # Name
        name_label = ttk.Label(info_frame, text=file_info['name'], 
                              font=('Arial', 9, 'bold'))
        name_label.pack(anchor='w')
        
        # Description
        desc_label = ttk.Label(info_frame, text=file_info['description'], 
                              foreground='gray', font=('Arial', 8))
        desc_label.pack(anchor='w')
        
        # Status (wird später gefüllt)
        status_label = ttk.Label(info_frame, text="", font=('Arial', 8))
        status_label.pack(anchor='w')
        
        # Speichere Referenz für Updates
        setattr(checkbox, 'status_label', status_label)
        setattr(checkbox, 'file_pattern', file_pattern)
    
    def scan_profiles(self):
        """Scannt alle verfügbaren Profile"""
        try:
            profiles_base = Path.home() / "Documents" / "Euro Truck Simulator 2" / "profiles"
            
            if not profiles_base.exists():
                messagebox.showerror("Fehler", f"Profile-Verzeichnis nicht gefunden: {profiles_base}")
                return
            
            self.profiles = {}
            
            for profile_dir in profiles_base.iterdir():
                if profile_dir.is_dir():
                    profile_info = self.extract_profile_info(profile_dir)
                    if profile_info:
                        self.profiles[profile_dir.name] = profile_info
            
            # Update Dropdowns
            profile_names = []
            for profile_id, info in self.profiles.items():
                display_name = f"{info['name']} ({info['company']}) - {profile_id}"
                profile_names.append(display_name)
            
            self.source_combo['values'] = profile_names
            self.target_combo['values'] = profile_names
            
            self.status_label.config(text=f"{len(self.profiles)} Profile gefunden", 
                                   foreground='green')
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Scannen: {e}")
    
    def extract_profile_info(self, profile_dir):
        """Extrahiert Profil-Informationen"""
        profile_sii = profile_dir / "profile.sii"
        
        if not profile_sii.exists():
            return None
        
        try:
            # Versuche SII Decrypt zu verwenden
            try:
                sys.path.append(str(Path(__file__).parent))
                from src.config import SII_DECRYPT_EXE
                
                if SII_DECRYPT_EXE.exists():
                    temp_file = f"temp_profile_{profile_dir.name}.txt"
                    
                    result = subprocess.run(
                        [str(SII_DECRYPT_EXE), str(profile_sii), temp_file],
                        capture_output=True, text=True, encoding='utf-8'
                    )
                    
                    if result.returncode == 0 and Path(temp_file).exists():
                        with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        Path(temp_file).unlink()  # Cleanup
                    else:
                        # Fallback: Versuche direkt zu lesen
                        with open(profile_sii, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                else:
                    # Fallback: Versuche direkt zu lesen
                    with open(profile_sii, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
            except:
                # Fallback: Versuche direkt zu lesen
                with open(profile_sii, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            # Extrahiere Informationen
            name_match = re.search(r'profile_name:\s*"?([^"\n]+)"?', content)
            company_match = re.search(r'company_name:\s*"?([^"\n]+)"?', content)
            
            profile_name = name_match.group(1).strip() if name_match else "Unbekannt"
            company_name = company_match.group(1).strip() if company_match else "Keine Firma"
            
            return {
                'name': profile_name,
                'company': company_name,
                'path': profile_dir,
                'files': self.scan_profile_files(profile_dir)
            }
            
        except Exception as e:
            print(f"Fehler beim Extrahieren von Profil {profile_dir.name}: {e}")
            return {
                'name': f"Profil {profile_dir.name}",
                'company': "Unbekannt",
                'path': profile_dir,
                'files': self.scan_profile_files(profile_dir)
            }
    
    def scan_profile_files(self, profile_dir):
        """Scannt verfügbare Dateien in einem Profil"""
        files = {}
        
        for file_pattern in self.transferable_files.keys():
            if '*' in file_pattern:
                # Wildcard pattern
                base_pattern = file_pattern.replace('*', '')
                matching_files = []
                for file_path in profile_dir.glob(file_pattern):
                    if file_path.is_file():
                        matching_files.append(file_path)
                files[file_pattern] = matching_files
            else:
                # Exact file
                file_path = profile_dir / file_pattern
                files[file_pattern] = [file_path] if file_path.exists() else []
        
        return files
    
    def on_source_selected(self, event):
        """Wird aufgerufen wenn Quell-Profil ausgewählt wird"""
        self.update_file_status()
    
    def on_target_selected(self, event):
        """Wird aufgerufen wenn Ziel-Profil ausgewählt wird"""
        self.update_file_status()
    
    def update_file_status(self):
        """Aktualisiert den Status der Datei-Optionen"""
        source_idx = self.source_combo.current()
        target_idx = self.target_combo.current()
        
        if source_idx < 0 or target_idx < 0:
            return
        
        source_id = list(self.profiles.keys())[source_idx]
        target_id = list(self.profiles.keys())[target_idx]
        
        source_files = self.profiles[source_id]['files']
        target_files = self.profiles[target_id]['files']
        
        # Update Status Labels
        for widget in self.options_scroll_frame.winfo_children():
            for child in widget.winfo_children():
                for subchild in child.winfo_children():
                    if hasattr(subchild, 'winfo_children'):
                        for checkbox in subchild.winfo_children():
                            if hasattr(checkbox, 'status_label') and hasattr(checkbox, 'file_pattern'):
                                pattern = checkbox.file_pattern
                                source_count = len(source_files.get(pattern, []))
                                target_count = len(target_files.get(pattern, []))
                                
                                if source_count == 0:
                                    status_text = "❌ Nicht in Quelle vorhanden"
                                    status_color = "red"
                                    # Deaktiviere Checkbox
                                    checkbox.config(state='disabled')
                                    self.file_vars[pattern].set(False)
                                elif target_count > 0:
                                    status_text = f"⚠️ Überschreibt {target_count} Datei(en)"
                                    status_color = "orange"
                                    checkbox.config(state='normal')
                                else:
                                    status_text = f"✅ {source_count} Datei(en) verfügbar"
                                    status_color = "green"
                                    checkbox.config(state='normal')
                                
                                checkbox.status_label.config(text=status_text, foreground=status_color)
    
    def select_recommended(self):
        """Wählt alle empfohlenen Dateien aus"""
        for file_pattern, file_info in self.transferable_files.items():
            if file_info['recommended']:
                self.file_vars[file_pattern].set(True)
    
    def deselect_all(self):
        """Wählt alle Dateien ab"""
        for var in self.file_vars.values():
            var.set(False)
    
    def select_settings_only(self):
        """Wählt nur Einstellungen (keine Spieldaten)"""
        self.deselect_all()
        for file_pattern, file_info in self.transferable_files.items():
            if file_info['category'] in ['essential', 'vehicle']:
                self.file_vars[file_pattern].set(True)
    
    def create_backup(self):
        """Erstellt ein Backup des Ziel-Profils"""
        target_idx = self.target_combo.current()
        if target_idx < 0:
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Ziel-Profil aus!")
            return
        
        try:
            target_id = list(self.profiles.keys())[target_idx]
            target_profile = self.profiles[target_id]
            
            # Backup-Ordner erstellen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{target_profile['name']}_{target_id}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # Kopiere das gesamte Profil
            shutil.copytree(target_profile['path'], backup_path)
            
            # Speichere Backup-Info
            backup_info = {
                'profile_name': target_profile['name'],
                'profile_id': target_id,
                'company': target_profile['company'],
                'timestamp': timestamp,
                'backup_path': str(backup_path)
            }
            
            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Erfolg", f"Backup erstellt: {backup_name}")
            self.status_label.config(text="Backup erstellt", foreground='green')
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Backup-Erstellung fehlgeschlagen: {e}")
    
    def start_transfer(self):
        """Startet den Transfer-Prozess"""
        source_idx = self.source_combo.current()
        target_idx = self.target_combo.current()
        
        if source_idx < 0 or target_idx < 0:
            messagebox.showwarning("Warnung", "Bitte wählen Sie Quell- und Ziel-Profil aus!")
            return
        
        if source_idx == target_idx:
            messagebox.showwarning("Warnung", "Quell- und Ziel-Profil dürfen nicht identisch sein!")
            return
        
        # Prüfe ob Dateien ausgewählt sind
        selected_files = [pattern for pattern, var in self.file_vars.items() if var.get()]
        if not selected_files:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus!")
            return
        
        # Bestätigung
        source_id = list(self.profiles.keys())[source_idx]
        target_id = list(self.profiles.keys())[target_idx]
        source_name = self.profiles[source_id]['name']
        target_name = self.profiles[target_id]['name']
        
        confirm_msg = f"""Transfer bestätigen:

Von: {source_name} ({source_id})
Nach: {target_name} ({target_id})

Dateien: {len(selected_files)} ausgewählt

⚠️ WARNUNG: Bestehende Dateien werden überschrieben!
Möchten Sie vorher ein Backup erstellen?"""
        
        result = messagebox.askyesnocancel("Transfer bestätigen", confirm_msg)
        
        if result is None:  # Cancel
            return
        elif result:  # Yes - Create backup first
            self.create_backup()
        
        # Führe Transfer durch
        try:
            self.perform_transfer(source_id, target_id, selected_files)
        except Exception as e:
            messagebox.showerror("Fehler", f"Transfer fehlgeschlagen: {e}")
    
    def perform_transfer(self, source_id, target_id, selected_patterns):
        """Führt den eigentlichen Transfer durch"""
        source_profile = self.profiles[source_id]
        target_profile = self.profiles[target_id]
        
        transferred_files = []
        failed_files = []
        
        for pattern in selected_patterns:
            source_files = source_profile['files'].get(pattern, [])
            
            for source_file in source_files:
                if not source_file.exists():
                    continue
                
                try:
                    # Ziel-Datei bestimmen
                    relative_path = source_file.relative_to(source_profile['path'])
                    target_file = target_profile['path'] / relative_path
                    
                    # Erstelle Ziel-Verzeichnis falls nötig
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Kopiere Datei
                    shutil.copy2(source_file, target_file)
                    transferred_files.append(str(relative_path))
                    
                except Exception as e:
                    failed_files.append(f"{relative_path}: {e}")
        
        # Ergebnis anzeigen
        result_msg = f"Transfer abgeschlossen!\n\n"
        result_msg += f"✅ Erfolgreich: {len(transferred_files)} Dateien\n"
        
        if failed_files:
            result_msg += f"❌ Fehlgeschlagen: {len(failed_files)} Dateien\n\n"
            result_msg += "Fehler:\n" + "\n".join(failed_files[:5])
            if len(failed_files) > 5:
                result_msg += f"\n... und {len(failed_files) - 5} weitere"
        
        messagebox.showinfo("Transfer abgeschlossen", result_msg)
        self.status_label.config(text=f"Transfer abgeschlossen: {len(transferred_files)} Dateien", 
                               foreground='green')
    
    def manage_backups(self):
        """Öffnet das Backup-Management"""
        BackupManager(self.window, self.backup_dir, self.profiles)
    
    def run(self):
        """Startet das Tool (nur für Standalone)"""
        if isinstance(self.window, tk.Tk):
            self.window.mainloop()

class BackupManager:
    def __init__(self, parent, backup_dir, profiles):
        self.window = tk.Toplevel(parent)
        self.window.title("Backup Manager")
        self.window.geometry("800x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.backup_dir = backup_dir
        self.profiles = profiles
        
        self.create_widgets()
        self.load_backups()
    
    def create_widgets(self):
        """Erstellt die Backup-Manager GUI"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titel
        ttk.Label(main_frame, text="💾 Backup Manager", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Backup Liste
        list_frame = ttk.LabelFrame(main_frame, text="Verfügbare Backups", padding=10)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Treeview für Backups
        columns = ('name', 'profile', 'date', 'size')
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.backup_tree.heading('name', text='Backup Name')
        self.backup_tree.heading('profile', text='Profil')
        self.backup_tree.heading('date', text='Datum')
        self.backup_tree.heading('size', text='Größe')
        
        self.backup_tree.column('name', width=250)
        self.backup_tree.column('profile', width=200)
        self.backup_tree.column('date', width=150)
        self.backup_tree.column('size', width=100)
        
        # Scrollbar für Treeview
        tree_scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.backup_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="🔄 Wiederherstellen", 
                  command=self.restore_backup).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="📂 Ordner öffnen", 
                  command=self.open_backup_folder).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="🗑️ Löschen", 
                  command=self.delete_backup).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="❌ Schließen", 
                  command=self.window.destroy).pack(side='right')
    
    def load_backups(self):
        """Lädt alle verfügbaren Backups"""
        # Clear existing items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        if not self.backup_dir.exists():
            return
        
        for backup_path in self.backup_dir.iterdir():
            if backup_path.is_dir():
                try:
                    # Lade Backup-Info
                    info_file = backup_path / "backup_info.json"
                    if info_file.exists():
                        with open(info_file, 'r', encoding='utf-8') as f:
                            backup_info = json.load(f)
                        
                        profile_name = backup_info.get('profile_name', 'Unbekannt')
                        timestamp = backup_info.get('timestamp', '')
                        
                        # Formatiere Datum
                        try:
                            date_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                            date_str = date_obj.strftime("%d.%m.%Y %H:%M")
                        except:
                            date_str = timestamp
                    else:
                        # Fallback: Parse aus Ordnername
                        parts = backup_path.name.split('_')
                        profile_name = parts[0] if parts else 'Unbekannt'
                        date_str = backup_path.stat().st_mtime
                        date_str = datetime.fromtimestamp(date_str).strftime("%d.%m.%Y %H:%M")
                    
                    # Berechne Größe
                    size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                    size_str = self.format_size(size)
                    
                    # Füge zur Liste hinzu
                    self.backup_tree.insert('', 'end', values=(
                        backup_path.name,
                        profile_name,
                        date_str,
                        size_str
                    ), tags=(str(backup_path),))
                    
                except Exception as e:
                    print(f"Fehler beim Laden von Backup {backup_path.name}: {e}")
    
    def format_size(self, size_bytes):
        """Formatiert Dateigröße"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    
    def restore_backup(self):
        """Stellt ein Backup wieder her"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Backup aus!")
            return
        
        item = self.backup_tree.item(selection[0])
        backup_path = Path(item['tags'][0])
        backup_name = item['values'][0]
        profile_name = item['values'][1]
        
        # Bestätigung
        confirm_msg = f"""Backup wiederherstellen:

Backup: {backup_name}
Profil: {profile_name}

⚠️ WARNUNG: Das aktuelle Profil wird komplett überschrieben!
Möchten Sie vorher ein Backup des aktuellen Zustands erstellen?"""
        
        result = messagebox.askyesnocancel("Backup wiederherstellen", confirm_msg)
        
        if result is None:  # Cancel
            return
        
        try:
            # Finde Ziel-Profil
            info_file = backup_path / "backup_info.json"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                profile_id = backup_info.get('profile_id')
            else:
                # Parse aus Backup-Name
                parts = backup_name.split('_')
                profile_id = parts[1] if len(parts) > 1 else None
            
            if not profile_id or profile_id not in self.profiles:
                messagebox.showerror("Fehler", "Ziel-Profil nicht gefunden!")
                return
            
            target_profile_path = self.profiles[profile_id]['path']
            
            # Backup des aktuellen Zustands erstellen
            if result:  # Yes - Create backup first
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_backup_name = f"before_restore_{profile_id}_{timestamp}"
                current_backup_path = self.backup_dir / current_backup_name
                shutil.copytree(target_profile_path, current_backup_path)
            
            # Lösche aktuelles Profil
            shutil.rmtree(target_profile_path)
            
            # Stelle Backup wieder her (ohne backup_info.json)
            shutil.copytree(backup_path, target_profile_path)
            
            # Entferne backup_info.json aus wiederhergestelltem Profil
            restored_info = target_profile_path / "backup_info.json"
            if restored_info.exists():
                restored_info.unlink()
            
            messagebox.showinfo("Erfolg", f"Backup erfolgreich wiederhergestellt!")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Wiederherstellung fehlgeschlagen: {e}")
    
    def open_backup_folder(self):
        """Öffnet den Backup-Ordner"""
        selection = self.backup_tree.selection()
        if not selection:
            # Öffne Haupt-Backup-Ordner
            try:
                import os
                os.startfile(self.backup_dir)
            except:
                messagebox.showinfo("Info", f"Backup-Ordner: {self.backup_dir}")
        else:
            # Öffne spezifisches Backup
            item = self.backup_tree.item(selection[0])
            backup_path = Path(item['tags'][0])
            try:
                import os
                os.startfile(backup_path)
            except:
                messagebox.showinfo("Info", f"Backup-Pfad: {backup_path}")
    
    def delete_backup(self):
        """Löscht ein Backup"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Backup aus!")
            return
        
        item = self.backup_tree.item(selection[0])
        backup_path = Path(item['tags'][0])
        backup_name = item['values'][0]
        
        if messagebox.askyesno("Backup löschen", 
                              f"Backup '{backup_name}' wirklich löschen?\n\nDieser Vorgang kann nicht rückgängig gemacht werden!"):
            try:
                shutil.rmtree(backup_path)
                self.load_backups()  # Refresh list
                messagebox.showinfo("Erfolg", "Backup gelöscht!")
            except Exception as e:
                messagebox.showerror("Fehler", f"Löschen fehlgeschlagen: {e}")

# Integration in run_config.py
def add_profile_transfer_to_config(config_editor):
    """Fügt Profile Transfer Button zu run_config.py hinzu"""
    # Finde den Button-Frame
    for widget in config_editor.root.winfo_children():
        if isinstance(widget, ttk.Frame):
            for child in widget.winfo_children():
                if isinstance(child, ttk.Button) and "Profile neu scannen" in child.cget('text'):
                    # Füge Transfer-Button hinzu
                    ttk.Button(widget, text="🔄 Profile Transfer", 
                              command=lambda: ProfileTransferTool(config_editor.root)).pack(side='left', padx=(10, 0))
                    break

if __name__ == "__main__":
    try:
        app = ProfileTransferTool()
        app.run()
    except Exception as e:
        print(f"Fehler beim Starten: {e}")
        input("Drücken Sie Enter zum Beenden...")
