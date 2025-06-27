@echo off
if not exist venv (
    echo Virtuelle Umgebung nicht gefunden. Erstelle neue venv...
    python -m venv venv
    echo Virtuelle Umgebung erstellt!
)
echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate
echo Virtuelle Umgebung aktiviert!