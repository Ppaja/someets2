# # readVehicleData_v3_FINAL.py
# import re
# import subprocess
# from pathlib import Path

# # --- Konfiguration ---
# # Passe diese Pfade an, falls sie nicht mit deinem Hauptskript übereinstimmen
# from src.config import PROFILE_PATH, SII_DECRYPT_EXE

# def extract_vehicle_data():
#     """
#     Liest das letzte Quicksave, entschlüsselt es und extrahiert den kompletten
#     'vehicle'-Block und ALLE zugehörigen Definitionsblöcke, egal wie sie heißen.
#     """
#     print("--- Vehicle Data Extractor v3 (Bombensichere Suche) ---")
#     save_path = PROFILE_PATH / "save" / "quicksave" / "game.sii"
#     decrypted_path = Path("decrypted_save_for_reading.sii")

#     if not save_path.exists():
#         print(f"FEHLER: Quicksave nicht gefunden unter {save_path}")
#         return

#     try:
#         print(f"1. Entschlüssele '{save_path}'...")
#         subprocess.run([str(SII_DECRYPT_EXE), str(save_path), str(decrypted_path)], check=True, capture_output=True, text=True, encoding='utf-8')
#         print("   -> Entschlüsselung erfolgreich.")
#     except Exception as e:
#         print(f"   -> FEHLER bei der Entschlüsselung: {e}")
#         return

#     try:
#         with open(decrypted_path, 'r', encoding='utf-8', errors='ignore') as f:
#             content = f.read()

#         # Schritt 1: Finde die Truck-ID
#         economy_block_match = re.search(r"^economy\s*:\s*\S+\s*\{.*?^\}", content, re.DOTALL | re.MULTILINE)
#         economy_block = economy_block_match.group(0)
#         player_id_match = re.search(r"player:\s*(\S+)", economy_block)
#         player_id = player_id_match.group(1)
#         player_block_match = re.search(r"^player\s*:\s*" + re.escape(player_id) + r"\s*\{.*?^\}", content, re.DOTALL | re.MULTILINE)
#         truck_id_match = re.search(r'assigned_truck:\s*(\S+)', player_block_match.group(0))
#         truck_id = truck_id_match.group(1)
#         print(f"2. Truck-ID gefunden: {truck_id}")

#         # Schritt 2: Extrahiere den kompletten vehicle-Block
#         vehicle_block_pattern = re.compile(r"^vehicle\s*:\s*" + re.escape(truck_id) + r"\s*\{.*?^\}", re.DOTALL | re.MULTILINE)
#         vehicle_match = vehicle_block_pattern.search(content)
#         if not vehicle_match:
#             print("   -> FEHLER: Konnte den vehicle-Block nicht finden.")
#             return
#         vehicle_block = vehicle_match.group(0)
#         print("3. 'vehicle'-Block erfolgreich extrahiert.")

#         # Schritt 3: Extrahiere alle Accessory-IDs aus dem vehicle-Block
#         accessory_ids = re.findall(r"accessories\[\d+\]:\s*(\S+)", vehicle_block)
#         print(f"4. {len(accessory_ids)} Accessory-IDs im Block gefunden.")

#         # Schritt 4: Finde zu jeder ID die passende Definition (mit der bombensicheren Suche)
#         accessory_definitions = []
#         missing_defs_count = 0
#         for acc_id in accessory_ids:
#             # <<< DER FINALE FIX HIER: \w+ passt auf JEDEN Definitionstyp >>>
#             def_pattern = re.compile(r"^\w+\s*:\s*" + re.escape(acc_id) + r"\s*\{.*?^\}", re.DOTALL | re.MULTILINE)
#             def_match = def_pattern.search(content)
#             if def_match:
#                 accessory_definitions.append(def_match.group(0))
#             else:
#                 print(f"   -> WARNUNG: Konnte keine Definition für {acc_id} finden!")
#                 missing_defs_count += 1
        
#         print(f"5. {len(accessory_definitions)} zugehörige Accessory-Definitionen extrahiert.")
#         if missing_defs_count > 0:
#             print(f"   -> {missing_defs_count} Definitionen wurden NICHT gefunden. Dies könnte ein Problem sein, wenn sie nicht im Ziel-Savegame existieren.")

#         # Schritt 5: Gib alles sauber formatiert aus
#         output_filename = "extracted_data.txt"
#         with open(output_filename, 'w', encoding='utf-8') as f:
#             f.write("### VEHICLE_BLOCK ###\n")
#             f.write(vehicle_block)
#             f.write("\n\n### ACCESSORY_DEFINITIONS ###\n")
#             f.write("\n".join(accessory_definitions))
        
#         print("\n----------------- ERGEBNIS -----------------")
#         print(f"Daten wurden erfolgreich in die Datei '{output_filename}' geschrieben.")
#         print("Bitte benenne diese Datei um (z.B. 'empty_data.txt' oder 'bricks_data.txt').")
#         print("--------------------------------------------")


#     except Exception as e:
#         print(f"Ein Fehler ist aufgetreten: {e}")
#         import traceback
#         traceback.print_exc()
#     finally:
#         if decrypted_path.exists():
#             decrypted_path.unlink()


# if __name__ == "__main__":
#     extract_vehicle_data()


