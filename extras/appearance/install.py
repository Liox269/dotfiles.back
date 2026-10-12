#!/usr/bin/env python3
"""Reversible installer for Advanced Appearance in Caelestia v2.5.0."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from datetime import datetime

PACKAGE = Path(__file__).resolve().parent
MARKER = '// LIOX_ADVANCED_APPEARANCE_V01'
ORIGINAL = '''        ToggleRow {
            Layout.topMargin: Tokens.spacing.extraSmall / 2 - parent.spacing

            last: true
            text: Tr.tr("Dark theme")
            checked: !Colours.light
            onToggled: Colours.setMode(checked ? "dark" : "light")
        }'''
INSERTION = ORIGINAL + '\n\n        ' + MARKER + '\n        AdvancedAppearance {\n            Layout.fillWidth: true\n        }'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.lixo-appearance-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        if path.exists():
            os.chmod(tmp, path.stat().st_mode & 0o777)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--restore', type=Path)
    ap.add_argument('--shell', type=Path, default=Path.home() / '.config/quickshell/caelestia')
    ap.add_argument('--repo', type=Path, default=Path.cwd())
    args = ap.parse_args()
    page = args.shell.expanduser() / 'modules/nexus/pages/WallpaperAndStyle.qml'
    component = page.parent / 'AdvancedAppearance.qml'
    controller = Path.home() / '.local/lib/liox-appearance/appearance.py'
    repo_dest = args.repo.expanduser() / 'extras/appearance'
    backup_base = Path.home() / '.local/share/liox-appearance/backups'
    if args.restore:
        backup = args.restore.expanduser().resolve()
        if not backup.is_relative_to(backup_base.resolve()) or backup == backup_base.resolve():
            raise ValueError('Ruta de respaldo fuera del directorio permitido')
        manifest = json.loads((backup / 'manifest.json').read_text())
        if manifest['targets'] != [str(page), str(component), str(controller)]:
            raise ValueError('El respaldo no corresponde a esta instalación')
        for index, target in enumerate([page, component, controller]):
            old = backup / f'{index}.old'
            if old.exists():
                write(target, old.read_bytes())
            elif target.exists():
                target.unlink()
        print('Restaurado. Reinicia Caelestia manualmente.')
        return
    if not page.is_file():
        raise FileNotFoundError(page)
    original = page.read_text()
    if MARKER in original:
        raise ValueError('Advanced Appearance ya está instalado; no aplicar dos veces')
    if original.count(ORIGINAL) != 1:
        raise ValueError('QML distinto del esperado. No se ha modificado nada.')
    revised = original.replace(ORIGINAL, INSERTION, 1)
    content = (PACKAGE / 'AdvancedAppearance.qml').read_text()
    if '__CONTROLLER__' not in content:
        raise ValueError('Plantilla QML incompleta')
    content = content.replace('__CONTROLLER__', str(controller).replace('\\', '\\\\').replace('"', '\\"'))
    lua = Path.home() / '.config/hypr/variables.lua'
    if not lua.is_file():
        raise FileNotFoundError(lua)
    sys.path.insert(0, str(PACKAGE))
    from appearance import snapshot
    print('Configuración actual:', snapshot(lua.read_text()))
    print('Archivos afectados:', page, component, controller, repo_dest, sep='\n  ')
    print('No se modifican: Hyprland Lua durante la instalación, wallpaper, Waywallen, Matugen, Gaming o DualSense.')
    if args.dry_run:
        print('Simulación OK. No se ha modificado ningún archivo.')
        return
    backup = backup_base / datetime.now().strftime('appearance-%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True)
    targets = [page, component, controller]
    (backup / 'manifest.json').write_text(json.dumps({'targets': [str(p) for p in targets]}, indent=2))
    for i, target in enumerate(targets):
        if target.is_file():
            (backup / f'{i}.old').write_bytes(target.read_bytes())
    try:
        write(page, revised.encode())
        write(component, content.encode())
        write(controller, (PACKAGE / 'appearance.py').read_bytes())
        repo_dest.mkdir(parents=True, exist_ok=True)
        for name in ('AdvancedAppearance.qml', 'appearance.py', 'install.py', 'README.md'):
            shutil.copy2(PACKAGE / name, repo_dest / name)
    except Exception:
        for i, target in enumerate(targets):
            old = backup / f'{i}.old'
            if old.exists():
                write(target, old.read_bytes())
            elif target.exists():
                target.unlink()
        raise
    print('Instalación OK. Respaldo:', backup)
    print('Restaurar: python3 install.py --restore "' + str(backup) + '"')
    print('Reinicia Caelestia: caelestia shell --kill; sleep 1; caelestia shell -d')

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print('ERROR:', err, file=sys.stderr)
        sys.exit(1)
