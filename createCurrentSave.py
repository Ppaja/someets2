#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfaches Skript zum Auslesen der rohen Savegame-Daten
"""

import sys
from pathlib import Path

# Füge src-Pfad hinzu
sys.path.append(str(Path(__file__).parent))

def read_raw_savegame():
    """Liest den aktuellsten Savegame aus und gibt die rohen Daten aus"""
    try:
        from src.config import PROFILE_PATH
        from src.game_integration.ets2_savegame_parser import SavegameParser
        
        print("🔍 Suche nach aktuellem Savegame...")
        parser = SavegameParser(profile_path=PROFILE_PATH)
        
        # Finde neuesten Save
        latest_save = parser._find_latest_save()
        if not latest_save:
            print("❌ Kein Savegame gefunden!")
            return
            
        print(f"📁 Gefunden: {latest_save}")
        
        # Entschlüssele Save
        print("🔓 Entschlüssele Savegame...")
        decrypted_file = parser._decrypt_save(latest_save)
        
        if not decrypted_file:
            print("❌ Entschlüsselung fehlgeschlagen!")
            return
            
        # Lese rohe Daten
        print("📖 Lese rohe Daten...")
        with open(decrypted_file, 'r', encoding='utf-8', errors='ignore') as f:
            raw_data = f.read()
        
        # Ausgabe in Datei
        output_file = "raw_savegame_data.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(raw_data)
        
        print(f"✅ Rohe Savegame-Daten gespeichert in: {output_file}")
        print(f"📊 Dateigröße: {len(raw_data):,} Zeichen")
        
        # Zeige ersten Teil der Daten
        print("\n" + "="*60)
        print("ERSTE 2000 ZEICHEN DER ROHEN DATEN:")
        print("="*60)
        print(raw_data[:2000])
        print("="*60)
        print(f"... und {len(raw_data)-2000:,} weitere Zeichen")
        
        # Cleanup
        parser._cleanup()
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    read_raw_savegame()
