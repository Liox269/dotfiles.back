#!/usr/bin/env python3
"""Non-destructive patch for Caelestia 2.5.0 dashboard; local files only."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
SHELL = Path.home()/'.config/quickshell/caelestia'
TARGET = SHELL/'modules/dashboard/Content.qml'
DEST = SHELL/'modules/dashboard/Gaming.qml'
HELPER = SHELL/'scripts/liox_gaming_status.py'
MARKER = 'lioxGamingComponent'


def fail(message):
    raise SystemExit('ERROR: ' + message)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if not TARGET.is_file(): fail(f'No existe {TARGET}')
    s = TARGET.read_text()
    if MARKER in s: fail('Gaming ya integrado; no se aplican cambios')
    tab = '''            {
                component: lioxGamingComponent,
                iconName: "sports_esports",
                text: "Gaming",
                enabled: true
            },
'''
    needle = '            {\n                component: weatherComponent,'
    if s.count(needle) != 1: fail('Content.qml no coincide con estructura v2.5.0 (weatherComponent)')
    s = s.replace(needle, tab + needle)
    component = '''            Component {
                id: lioxGamingComponent
                Gaming {}
            }

'''
    needle2 = '            Component {\n                id: weatherComponent'
    if s.count(needle2) != 1: fail('Content.qml no coincide con estructura v2.5.0 (Component weather)')
    s = s.replace(needle2, component + needle2)
    if not (HERE/'Gaming.qml').is_file() or not (HERE/'status.py').is_file(): fail('Archivos del módulo incompletos')
    if a.dry_run:
        print('OK: Estructura compatible; se modificaría Content.qml y se copiarían Gaming.qml y helper Python.')
        return
    backup = Path.home()/'.local/share/liox-gaming-center/backups'/datetime.now().strftime('%Y%m%d-%H%M%S')
    backup.mkdir(parents=True, exist_ok=False)
    for name, path in [('Content.qml',TARGET), ('Gaming.qml',DEST), ('status.py',HELPER)]:
        if path.exists(): shutil.copy2(path, backup/name)
    (backup/'manifest.txt').write_text('\n'.join(f'{p.name}: '+('existed' if (backup/p.name).exists() else 'absent') for p in (TARGET,DEST,HELPER))+'\n')
    try:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        HELPER.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE/'Gaming.qml', DEST)
        shutil.copy2(HERE/'status.py', HELPER)
        TARGET.write_text(s)
    except Exception:
        shutil.copy2(backup/'Content.qml', TARGET)
        if (backup/'Gaming.qml').exists(): shutil.copy2(backup/'Gaming.qml', DEST)
        elif DEST.exists(): DEST.unlink()
        if (backup/'status.py').exists(): shutil.copy2(backup/'status.py', HELPER)
        elif HELPER.exists(): HELPER.unlink()
        raise
    print('Gaming agregado al Dashboard (Caelestia local).')
    print('Respaldo:', backup)
    print('Restaurar con: python3 extras/gaming-center/dashboard/restore.py "'+str(backup)+'"')

if __name__ == '__main__': main()
