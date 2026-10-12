#!/usr/bin/env python3
"""Reproducible, reversible Advanced Appearance v0.2.1 installer."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
MARKER = '// LIOX_ADVANCED_APPEARANCE_V01'
ORIGINAL = '''        ToggleRow {
            Layout.topMargin: Tokens.spacing.extraSmall / 2 - parent.spacing

            last: true
            text: Tr.tr("Dark theme")
            checked: !Colours.light
            onToggled: Colours.setMode(checked ? "dark" : "light")
        }'''
INSERTION = ORIGINAL + '\n\n        ' + MARKER + '\n        AdvancedAppearance {\n            Layout.fillWidth: true\n        }'
FILES = ('appearance.py', 'AdvancedAppearance.qml', 'install.py', 'README.md')

def plan(home, repo):
    page = home/'.config/quickshell/caelestia/modules/nexus/pages/WallpaperAndStyle.qml'
    qml = page.with_name('AdvancedAppearance.qml')
    ctrl = home/'.local/lib/liox-appearance/appearance.py'
    paths = { 'page':page, 'qml':qml, 'controller':ctrl }
    paths.update({ 'repo_'+name:repo/'extras/appearance'/name for name in FILES })
    return paths

def desired(paths):
    page = paths['page']
    if not page.is_file(): raise ValueError('No existe '+str(page))
    txt = page.read_text()
    if MARKER in txt:
        if txt.count(MARKER)!=1 or txt.count('AdvancedAppearance {')!=1:
            raise ValueError('Integración existente ambigua: revisar WallpaperAndStyle.qml')
    else:
        if txt.count(ORIGINAL)!=1:
            raise ValueError('WallpaperAndStyle.qml no coincide con la estructura esperada; no se modifica')
        txt=txt.replace(ORIGINAL,INSERTION,1)
    qml=(HERE/'AdvancedAppearance.qml').read_text()
    if qml.count('__CONTROLLER__')!=4: raise ValueError('Plantilla QML no coincide')
    qml=qml.replace('__CONTROLLER__',str(paths['controller']).replace('\\','\\\\').replace('"','\\"'))
    data={'page':txt.encode(), 'qml':qml.encode(), 'controller':(HERE/'appearance.py').read_bytes()}
    for name in FILES:
        data['repo_'+name]=(HERE/name).read_bytes()
    return data

def run(argv=None):
    parser=argparse.ArgumentParser()
    x=parser.add_mutually_exclusive_group(required=True)
    x.add_argument('--dry-run',action='store_true')
    x.add_argument('--install',action='store_true')
    x.add_argument('--restore',type=Path)
    parser.add_argument('--repo',type=Path,default=Path.cwd())
    parser.add_argument('--home',type=Path,default=Path.home(),help=argparse.SUPPRESS)
    args=parser.parse_args(argv)
    home=args.home.expanduser().resolve()
    repo=args.repo.expanduser().resolve()
    paths=plan(home,repo)
    if args.restore:
        folder=args.restore.expanduser().resolve()
        base=(home/'.local/share/liox-appearance/backups').resolve()
        if not folder.is_relative_to(base) or folder==base: raise ValueError('Ruta de respaldo no válida')
        manifest=json.loads((folder/'manifest.json').read_text())
        if manifest.get('targets')!={k:str(p) for k,p in paths.items()}: raise ValueError('El respaldo no corresponde a estos destinos')
        for key,path in paths.items():
            previous=folder/(key+'.old')
            if previous.is_file():
                path.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(previous,path)
            elif path.is_file(): path.unlink()
        print('Restauración completada. Reinicia Caelestia.')
        return
    content=desired(paths)
    changed={key:(not path.is_file() or path.read_bytes()!=content[key]) for key,path in paths.items()}
    for key,value in changed.items(): print(('Actualizar' if value else 'Sin cambios')+': '+str(paths[key]))
    if args.dry_run:
        print('Simulación OK. No se modificó ningún archivo.')
        return
    if not any(changed.values()):
        print('Ya está sincronizado. Sin cambios.')
        return
    backup=home/'.local/share/liox-appearance/backups'/f'repro-v022-{datetime.now():%Y%m%d-%H%M%S-%f}'
    backup.mkdir(parents=True,exist_ok=False)
    (backup/'manifest.json').write_text(json.dumps({'targets':{k:str(p) for k,p in paths.items()}},indent=2))
    for key,path in paths.items():
        if path.is_file(): shutil.copy2(path,backup/(key+'.old'))
    written=[]
    try:
        for key,path in paths.items():
            if changed[key]:
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(content[key]); written.append(key)
    except Exception:
        for key in reversed(written):
            path=paths[key]; old=backup/(key+'.old')
            if old.exists(): shutil.copy2(old,path)
            elif path.exists():path.unlink()
        raise
    print('Instalación OK. Respaldo:',backup)
    print('Restaurar: python3 '+str(HERE/'install.py')+' --restore "'+str(backup)+'" --repo "'+str(repo)+'"')
    print('No se modifica background.wallpaperEnabled, Waywallen ni Gaming Center.')
    print('Reinicia Caelestia para cargar la página actualizada.')

if __name__=='__main__':
    try: run()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr);sys.exit(1)
