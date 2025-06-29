ignore



### Einmalige Einrichtung
Diese Schritte müssen nur ein einziges Mal durchgeführt werden.

0.  **Python installieren:** Lade [Python 3.10.0](https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe) herunter und installiere es. 

    <sup>**Wichtig**: Haken setzen bei **"Add Python 3.10 to PATH"**<sup>
1.  **Download:** Lade das Skript-Paket über den link [hier](https://github.com/Ppaja/someets2/archive/refs/heads/main.zip) herunter und entpacke die ZIP-Datei.

2.  **Basisskript installieren:** Führe die Datei `install.bat` aus und folge den Anweisungen im Konsolenfenster.

3.  **ETS2 Telemetry Server:**
    *   Lade den ETS2 Telemetry Server von [dieser URL](https://github.com/Funbit/ets2-telemetry-server/archive/refs/heads/master.zip) herunter.
    *   Entpacke in einen beliebigen Ordner auf deinem PC (z.B. Desktop).
    *   Starte den server im Ordner "server" mit der Datei "Ets2Telemetry.exe". Merke dir schon mal dass hier die URL angezeigt wird für später (z.B. `http://127.0.0.1:25555`).

4.  **Tool um Spieldaten entschlüsseln installieren:**
    *   Öffne den Ordner `tools` von diesem Projekt
    *   Lade den SII Decrypt CLI von [dieser URL](https://github.com/Stearells/SII_Decrypt/releases/download/0.7/Release.7z) herunter. 
    *   Entpacke die ZIP-Datei im Ordner `tools` (einfach drag & drop).
    *   Jetzt sollten direkt im tools die SII_Decrypt Dateien liegen

5.  **Google API Key eintragen:**
    *   Öffne die Datei `.env` mit einem Texteditor (z.B. Notepad).
    *   Trage dort deinen persönlichen Google API Key ein. Diesen benötigst du, damit die KI-Funktionen für Aufträge funktionieren.
    *   Hinweis: Geh auf https://aistudio.google.com/ und erstelle einen API Key.
    ```
    GEMINI_API_KEY=DEIN_API_KEY_HIER
    ```

    Es wird gemini-2.5-flash verwendet, welches kostenfrei mit 15 RPM 500 req/day genutzt werden kann. Das reicht weeeeit über das was das skript braucht.

6.  **Skript konfigurieren:**
    *   Führe die Datei `config_bearbeiten.bat` aus.
    *   Wähle das ETS2-Profil aus, mit dem du das Skript verwenden möchtest.
    *   Trage unter  `[Telemetry]` die URL des Telemetry Servers ein (den siehst du im ETS2 Telemetry Server bei "Server IP:" wie "127.0.0.1")
    *   Speichern

Hinweis: Wenn du das Skript mit einem anderen Profil nutzen willst, musst du die Datei `config_bearbeiten.bat` erneut ausführen und das neue Profil auswählen.


### Vor jedem Spielstart
Diese beiden Schritte müssen **vor jeder Spielsession** ausgeführt werden.

1.  **Telemetry Server starten:** Gehe in den Ordner des Telemetry Servers und starte die `ets2-telemetry.exe`. Lass dieses Programm während des Spielens im Hintergrund laufen. (oder trage den Pfad des ets2-telemetry.exe in die config ein, dann startet es automatisch)
2.  **Entsprechendes Skript starten:** Führe die Datei `0_start_truck.bat` (main.py - truck/aufträge) oder `0_start_ddriver.bat` (main2.py - lieferdienst) aus dem Skript-Verzeichnis aus.

Starte die Skripte am besten erst wenn das Spiel bereits läuft. 

### Steuerung
*   **Pfeiltaste Hoch:** Handy öffnen/schließen
*   **Pfeiltaste Runter:** Laptop öffnen/schließen
*   **Pfeiltasten (Links/Rechts/Hoch/Runter):** Navigation in den Menüs
*   **Enter:** Auswahl bestätigen
*   **Zurück/Backspace:** Eine Ebene zurück / Gerät wegstecken

Im Dispo Chat Enter drücken um Liste der Städte aufzurufen und Auftrag anzufordern.

Für Lieferdienst Skript:
- Wenn Auftrag verfügbar wird in der Lieferapp Enter drücken für mehr Details + Karte
- Halte innerhalb des Lokals/Discounters, schalte den Motor aus und das Kaufmenü öffnet sich. 
- Im SMS Chat mit Kunden (nach Bestellkauf) Enter drücken für "Ich finde den Kunden nicht und frage nach" feature
---