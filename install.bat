@echo off

:: Überprüfung, ob Python installiert ist
python --version
if %errorlevel% neq 0 (
    echo Python not found. Please install Python.
    start https://www.python.org/downloads/
    exit /b
) else (
    echo Python found.
)

if not exist venv (
    echo Virtuelle Umgebung nicht gefunden. Erstelle neue venv...
    python -m venv venv
    echo Virtuelle Umgebung erstellt!
)
echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate
echo Virtuelle Umgebung aktiviert!

:: Installieren der erforderlichen Pakete aus requirements.txt
pip install -r requirements.txt
@echo requirements installed

exit
