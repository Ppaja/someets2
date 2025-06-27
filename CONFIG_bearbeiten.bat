@echo off
title Immersion Hub
echo Starte Config GUI...
:: Aktiviere die virtuelle Umgebung und starte das Hauptskript
call venv\Scripts\activate.bat
python run_config.py
echo.
echo Das Programm wurde beendet. Du kannst das Fenster jetzt schliessen.
pause