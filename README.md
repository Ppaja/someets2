# ETS2 Immersion Hub (Testprojekt)
**Hinweis:** Das sind einfach ein paar Ideen und Demos, KEIN fertiges Produkt.
Wenn ich mal weiß was was ich eigentlich genau machen will, dann muss ich das sowieso von Grund auf neu schreiben. Das ist wirklich nur ein Test.

# 1. Idee (main.py)
Aufträge anfordern, paar roleplay Ideenn, etc.
## Features
### 📱 Handy (Pfeiltaste Hoch)

*   **SMS:**
    *   Fordere neue Aufträge für deine eigene Zugmaschine an.
    *   Das Skript erkennt deine aktuelle Position/nächste Stadt
    *   Aktuell entscheidet eine KI (Gemini), welchen spezifischen Auftrag du erhältst, wobei längere Strecken bevorzugt werden. (theoretisch mal möglich: Filter nach Frachtart, Gewicht etc. Ein LLM ist hier zwar eigentlich noch unnötig, aber für später, mit eigenen Filtern, wahrscheinlich mal wichtig)
    *   Erhalte Benachrichtigungen bei besonderen Ereignissen per SMS

*   **Browser:**
    *   Greife auf deine "Polizeiakte" zu und sieh dir eine Historie deiner erhaltenen Strafen an.

### 💻 Laptop (Pfeiltaste Runter)

*   **Mail:**
    *   Empfange Informationen zu deinem nächsten Auftrag per E-Mail.
    *   Erhalte Mahnungen von deinem Unternehmen, wenn eine Fracht verspätet abgeliefert wird.

### Steuerung
*   **Pfeiltaste Hoch:** Handy öffnen/schließen
*   **Pfeiltaste Runter:** Laptop öffnen/schließen
*   **Pfeiltasten (Links/Rechts/Hoch/Runter):** Navigation in den Menüs
*   **Enter:** Auswahl bestätigen
*   **Zurück/Backspace:** Eine Ebene zurück / Gerät wegstecken

Im SMS Chat mit Dispo
*   **Enter:** Neuen Auftrag anfordern, Standort wählen (der nächste zum Spieler wird immer ganz oben angezeigt)
---

# 2. Idee (main2.py)
Baut auf vielen Modulen aus main.py auf, aber verfolgt eine völlig neue Idee: Lieferdienste ^^
Empfehlung: laden und nutzen einer car mod (z. B. https://ets2.lt/en/volkswagen-golf-4-1-9-tdi-1-54x/)

## Features
### 📱 Handy (Pfeiltaste Hoch)

*   **Lieferapp:**
    *   Du erhältst Bestellungen von Kunden, die du hier annimmst. 
    *   Mit erneutem drücken der **Enter**-Taste kannst du dir das GPS in der Lieferapp anzeigen lassen
    * Fahre zum korrekten Restaurant, kaufe die bestellte Ware und fahre zum Kunden.
    *   Nutzung des SMS Moduls für beispielsweise Rückfragen (Chat mit Kundem öffnen und enter drücken wenn du einen Kunden nicht findest beispielsweise)

### Steuerung
*   **Pfeiltaste Hoch:** Handy öffnen/schließen
*   **Pfeiltasten (Links/Rechts/Hoch/Runter):** Navigation in den Menüs
*   **Enter:** Auswahl bestätigen
*   **Zurück/Backspace:** Eine Ebene zurück / Gerät wegstecken

Im SMS Chat mit Kunden (nach Bestellkauf)
*   **Enter:** Ich finde den Kunden nicht und frage nach
---

## Installation & Einrichtung

### Einmalige Einrichtung
Diese Schritte müssen nur ein einziges Mal durchgeführt werden.

1.  **Download:** Lade das Skript-Paket über den link [hier](https://github.com/Ppaja/someets2/archive/refs/heads/main.zip) herunter und entpacke die ZIP-Datei.

2.  **Basisskript installieren:** Führe die Datei `install.bat` aus und folge den Anweisungen im Konsolenfenster.

3.  **ETS2 Telemetry Server:**
    *   Lade den ETS2 Telemetry Server von [dieser URL](https://github.com/Funbit/Funbit/ets2-telemetry-server/archive/refs/heads/main.zip) herunter.
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

1.  **Telemetry Server starten:** Gehe in den Ordner des Telemetry Servers und starte die `ets2-telemetry.exe`. Lass dieses Programm während des Spielens im Hintergrund laufen.
2.  **Entsprechendes Skript starten:** Führe die Datei `truck.bat` (main.py - truck/aufträge) oder `0_start_ddriver.bat` (main2.py - lieferdienst) aus dem Skript-Verzeichnis aus.

Starte die Skripte am besten erst wenn das Spiel bereits läuft. 

---

##  Bonus-Skript: `transfersettings.bat`

Eine Sache die mich ständig genervt hat: Ein neues Profil anzulegen und dann die Keybinds und Einstellungen einzeln einzutragen.

Deshalb:
*   **Funktion:** Kopiert Keybinds und Einstellungen von einem ETS2-Profil auf ein anderes.
*   **Nutzung:** Einfach die `transfersettings.bat` ausführen und den Anweisungen folgen, um Quell- und Zielprofil auszuwählen. Perfekt, wenn man ein neues Profil mit den gewohnten Einstellungen möchte ohne sich durch die Daten zu wühlen.


