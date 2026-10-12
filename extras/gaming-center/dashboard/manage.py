#!/usr/bin/env python3
"""Gaming Dashboard 0.5.1: atomic, reversible, no shell restart."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

SOURCE = Path(__file__).resolve().parent / 'Gaming.qml'
TARGET = Path.home() / '.config/quickshell/caelestia/modules/dashboard/Gaming.qml'
CONTENT = TARGET.with_name('Content.qml')
BACKUPS = Path.home() / '.local/share/liox-gaming-center/backups'
MARKERS = ('property var gamingData', 'function refresh()', 'root.pad', 'Colours.palette')

def fail(msg):
    raise RuntimeError(msg)

def recognized(data):
    return all(token in data for token in MARKERS)

def check():
    if not SOURCE.is_file() or not TARGET.is_file() or not CONTENT.is_file():
        fail('Faltan Gaming.qml o Content.qml de Caelestia (la integración v0.3 debe existir).')
    if 'lioxGamingComponent' not in CONTENT.read_text():
        fail('No se reconoció la integración de Gaming en Content.qml.')
    old, new = TARGET.read_bytes(), SOURCE.read_bytes()
    if not recognized(old.decode('utf-8')) or not recognized(new.decode('utf-8')):
        fail('Gaming.qml no coincide con la familia compatible; no se sobrescribirá.')
    if (b'onAccent' in new or new.count(b'{') != new.count(b'}')
            or b'color heading: Colours.palette.m3onSurface' in new
            or b'color cardBg: Colours.palette.m3surfaceContainer' in new):
        fail('Comprobación estática de Gaming.qml fallida.')
    return old, new

def atomic_write(destination, content):
    fd, temp = tempfile.mkstemp(prefix='.gaming-', dir=destination.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, destination.stat().st_mode & 0o777)
        os.replace(temp, destination)
    finally:
        if os.path.exists(temp): os.unlink(temp)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode', nargs='?', choices=['--dummy'], help=argparse.SUPPRESS)
    actions=p.add_mutually_exclusive_group()
    actions.add_argument('--dry-run', action='store_true')
    actions.add_argument('--install', action='store_true')
    actions.add_argument('--status', action='store_true')
    actions.add_argument('--restore', metavar='DIRECTORIO_RESGUARDO')
    args=p.parse_args()
    if args.restore:
        folder = Path(args.restore).expanduser().resolve()
        if not folder.is_relative_to(BACKUPS.resolve()) or folder == BACKUPS.resolve():
            fail('El respaldo debe estar dentro de ~/.local/share/liox-gaming-center/backups/')
        saved=folder/'Gaming.active.qml'
        if not saved.is_file() or not TARGET.is_file(): fail('No existe el respaldo o Gaming.qml instalado.')
        if not recognized(TARGET.read_text()): fail('El archivo actual no es un Gaming.qml reconocido.')
        atomic_write(TARGET, saved.read_bytes())
        print('Restaurado el Gaming.qml activo. Reinicia Caelestia manualmente.')
        return
    old,new=check()
    if args.status:
        print('Gaming integrado:', CONTENT)
        print('Destino:', TARGET)
        print('Versión instalada igual a v0.5.1:', old == new)
        return
    print('Destino confirmado:', TARGET)
    print('Archivo fuente:', SOURCE)
    print('Se cambiará SOLO Gaming.qml; no Content.qml, RGB ni scripts del mando.')
    if args.dry_run or not args.install:
        print('Simulación OK: no se modificó ningún archivo.')
        return
    BACKUPS.mkdir(parents=True, exist_ok=True)
    os.chmod(BACKUPS,0o700)
    backup=Path(tempfile.mkdtemp(prefix=datetime.now().strftime('v051-%Y%m%d-%H%M%S-'),dir=BACKUPS))
    os.chmod(backup,0o700)
    (backup/'Gaming.active.qml').write_bytes(old)
    (backup/'Gaming.new.qml').write_bytes(new)
    (backup/'restore.txt').write_text('python3 extras/gaming-center/dashboard/manage.py --restore "'+str(backup)+'"\n')
    try:
        atomic_write(TARGET,new)
    except BaseException:
        atomic_write(TARGET,old)
        raise
    print('Gaming v0.5.1 instalado. Respaldo:',backup)
    print('Restaurar: python3 extras/gaming-center/dashboard/manage.py --restore "'+str(backup)+'"')
    print('Reiniciar manualmente: caelestia shell --kill; sleep 1; caelestia shell -d')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(1)
