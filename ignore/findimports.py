#!/usr/bin/env python3
import os
import re
from pathlib import Path

def extract_imports_from_file(file_path):
    """Extrahiert alle Import-Statements aus einer Python-Datei."""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Regex-Patterns für verschiedene Import-Arten
        patterns = [
            # import module
            r'^import\s+([^\s#]+)',
            # from module import ...
            r'^from\s+([^\s#]+)\s+import',
            # import module as alias
            r'^import\s+([^\s#]+)\s+as\s+',
            # Mehrzeilige Imports mit Klammern
            r'^from\s+([^\s#]+)\s+import\s*\(',
        ]
        
        lines = content.split('\n')
        
        for line in lines:
            # Entferne führende Whitespaces
            stripped_line = line.strip()
            
            # Überspringe Kommentare und leere Zeilen
            if not stripped_line or stripped_line.startswith('#'):
                continue
                
            # Überspringe Docstrings (einfache Erkennung)
            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                continue
            
            # Prüfe alle Import-Patterns
            for pattern in patterns:
                match = re.match(pattern, stripped_line)
                if match:
                    # Bereinige das Import-Statement
                    import_line = stripped_line.split('#')[0].strip()  # Entferne Inline-Kommentare
                    imports.add(import_line)
                    break
                    
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"Fehler beim Lesen der Datei {file_path}: {e}")
    
    return imports

def should_ignore_directory(dir_name):
    """Prüft, ob ein Verzeichnis ignoriert werden soll."""
    ignore_dirs = {
        'venv',           # Virtual environment
        'env',            # Alternative venv name
        '.venv',          # Hidden venv
        '.env',           # Hidden env
        'virtualenv',     # Virtualenv
        '__pycache__',    # Python cache
        '.git',           # Git repository
        '.svn',           # SVN repository
        'node_modules',   # Node.js modules
        '.pytest_cache',  # Pytest cache
        '.mypy_cache',    # MyPy cache
        'build',          # Build directory
        'dist',           # Distribution directory
        '.tox',           # Tox testing
        'site-packages',  # Python packages
    }
    return dir_name in ignore_dirs

def find_all_python_files(directory):
    """Findet alle Python-Dateien rekursiv in einem Verzeichnis."""
    python_files = []
    ignored_dirs = []
    
    for root, dirs, files in os.walk(directory):
        # Filtere Verzeichnisse, die ignoriert werden sollen
        dirs_to_remove = []
        for dir_name in dirs:
            if should_ignore_directory(dir_name):
                dirs_to_remove.append(dir_name)
                ignored_dirs.append(os.path.join(root, dir_name))
        
        # Entferne ignorierte Verzeichnisse aus der Liste
        # (verhindert, dass os.walk in diese Verzeichnisse geht)
        for dir_name in dirs_to_remove:
            dirs.remove(dir_name)
        
        # Sammle Python-Dateien
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files, ignored_dirs

def main():
    # Aktuelles Verzeichnis als Startpunkt
    current_dir = os.getcwd()
    print(f"Durchsuche Verzeichnis: {current_dir}")
    print("-" * 50)
    
    # Alle Python-Dateien finden
    python_files, ignored_dirs = find_all_python_files(current_dir)
    
    # Zeige ignorierte Verzeichnisse an
    if ignored_dirs:
        print("Ignorierte Verzeichnisse:")
        for ignored_dir in ignored_dirs:
            print(f"  - {ignored_dir}")
        print("-" * 50)
    
    if not python_files:
        print("Keine Python-Dateien gefunden!")
        return
    
    print(f"Gefundene Python-Dateien: {len(python_files)}")
    print("-" * 50)
    
    # Alle einzigartigen Imports sammeln
    all_imports = set()
    
    for file_path in python_files:
        print(f"Analysiere: {file_path}")
        file_imports = extract_imports_from_file(file_path)
        all_imports.update(file_imports)
    
    print("\n" + "=" * 50)
    print("ALLE EINZIGARTIGEN IMPORT-STATEMENTS:")
    print("=" * 50)
    
    # Sortiere die Imports für bessere Lesbarkeit
    sorted_imports = sorted(all_imports)
    
    if sorted_imports:
        for import_statement in sorted_imports:
            print(import_statement)
        print(f"\nGesamt: {len(sorted_imports)} einzigartige Import-Statements gefunden.")
    else:
        print("Keine Import-Statements gefunden!")

if __name__ == "__main__":
    main()
