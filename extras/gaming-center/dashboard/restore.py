#!/usr/bin/env python3
import sys
from pathlib import Path
import shutil

if len(sys.argv) != 2: raise SystemExit('Uso: python3 restore.py RUTA_DEL_RESPALDO')
b = Path(sys.argv[1]).expanduser().resolve()
base = (Path.home()/'.local/share/liox-gaming-center/backups').resolve()
if b.parent != base or not (b/'manifest.txt').is_file(): raise SystemExit('Respaldo no reconocido')
root = Path.home()/'.config/quickshell/caelestia'
for name, dest in [('Content.qml',root/'modules/dashboard/Content.qml'),('Gaming.qml',root/'modules/dashboard/Gaming.qml'),('status.py',root/'scripts/liox_gaming_status.py')]:
    previous = b/name
    if previous.is_file(): shutil.copy2(previous,dest)
    elif dest.exists(): dest.unlink()
print('Restaurado. Reinicia Caelestia solo cuando lo necesites.')
