import os
import json

def reset_files_to_initial_state():
    """
    Setzt die Projektdateien in ihren ursprünglichen Zustand zurück.
    - Löscht ets2_log.json
    - Setzt den Inhalt von vier spezifischen JSON-Dateien zurück.
    """
    print("🔄 Starte den Reset-Vorgang...")

    # 1. ets2_log.json löschen, falls vorhanden
    log_file = "ets2_log.json"
    try:
        os.remove(log_file)
        print(f"🗑️  Datei '{log_file}' wurde erfolgreich gelöscht.")
    except FileNotFoundError:
        print(f"ℹ️  Datei '{log_file}' war nicht vorhanden, nichts zu tun.")
    except Exception as e:
        print(f"❌ Fehler beim Löschen von '{log_file}': {e}")

    # 2. Inhalte für die JSON-Dateien definieren
    initial_data = {
        "data/delivery_data.json": {
            "stats": {
                "total_earnings": 0.0,
                "completed_deliveries": 0
            },
            "history": []
        },
        "data/laptop_mail.json": {
            "emails": []
        },
        "data/phone_messages.json": {
            "conversations": [
                {
                    "sender": "Dispo",
                    "messages": [
                        {
                            "text": "Willkommen an Bord! Melde dich hier, wenn du einen neuen Auftrag brauchst.",
                            "timestamp": 1715888888.888,
                            "sent_by_me": False,
                            "read": False
                        }
                    ]
                }
            ]
        },
        "data/career_data.json": {
            "status": "employed",
            "company": "netto",
            "application_pending": None  # JSON 'null' wird in Python zu 'None'
        }
    }

    # 3. Die vier JSON-Dateien zurücksetzen
    for filename, data in initial_data.items():
        try:
            # 'w' öffnet die Datei zum Schreiben (überschreibt den alten Inhalt)
            # encoding='utf-8' ist wichtig für Sonderzeichen wie Umlaute
            with open(filename, 'w', encoding='utf-8') as f:
                # json.dump schreibt die Python-Datenstruktur als JSON in die Datei
                # indent=2 sorgt für eine saubere, lesbare Formatierung
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Datei '{filename}' wurde zurückgesetzt.")
        except Exception as e:
            print(f"❌ Fehler beim Zurücksetzen von '{filename}': {e}")

    print("\n🎉 Reset abgeschlossen! Alle Dateien sind im Ursprungszustand.")

# Dieser Block sorgt dafür, dass die Funktion nur ausgeführt wird,
# wenn das Skript direkt gestartet wird.
if __name__ == "__main__":
    reset_files_to_initial_state()
