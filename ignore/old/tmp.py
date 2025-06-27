import subprocess
from pathlib import Path

# Entschlüssele profile.sii
profile_path = Path('C:/Users/Anwender/Documents/Euro Truck Simulator 2/profiles/505031/profile.sii')
sii_decrypt = Path('tools/SII_Decrypt.exe')

subprocess.run([str(sii_decrypt), str(profile_path), 'temp_profile.txt'])

# Gib Inhalt aus
with open('temp_profile.txt', 'r', encoding='utf-8', errors='ignore') as f:
    print(f.read())