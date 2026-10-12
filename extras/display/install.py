#!/usr/bin/env python3
"""Display Manager v0.2.1 overlay installer. Existing sidebar registry is not altered."""
import argparse,json,shutil,sys
from pathlib import Path
from datetime import datetime
HERE=Path(__file__).resolve().parent
NAMES=['DisplayManager.qml','display.py','install.py','README.md']
def paths(home,repo):
    return {'live_qml':home/'.config/quickshell/caelestia/modules/nexus/pages/DisplayManager.qml',
            'live_backend':home/'.local/lib/liox-display/display.py',
            **{'repo_'+s:repo/'extras/display'/s for s in NAMES}}
def run():
    p=argparse.ArgumentParser(); g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--dry-run',action='store_true');g.add_argument('--install',action='store_true');g.add_argument('--restore',type=Path)
    p.add_argument('--home',type=Path,default=Path.home());p.add_argument('--repo',type=Path,default=Path.cwd());a=p.parse_args()
    home=a.home.expanduser().resolve();repo=a.repo.expanduser().resolve(); destinations=paths(home,repo)
    base=home/'.local/share/liox-display/backups'
    if a.restore:
        folder=a.restore.expanduser().resolve()
        if not folder.is_relative_to(base.resolve()) or folder==base.resolve():raise ValueError('Ruta de respaldo inválida')
        manifest=json.loads((folder/'manifest.json').read_text())
        if manifest['targets']!={k:str(v) for k,v in destinations.items()}:raise ValueError('Respaldo no coincide')
        for key,target in destinations.items():
            saved=folder/(key+'.old')
            if saved.is_file():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(saved,target)
            elif target.exists():target.unlink()
        print('Restauración completada. Reinicia Caelestia.');return
    page=home/'.config/quickshell/caelestia/modules/nexus/pages/DisplaySettingsPage.qml'
    registry=home/'.config/quickshell/caelestia/modules/nexus/PageRegistry.qml'
    if not page.is_file() or not registry.is_file() or 'LIOX_DISPLAY_SETTINGS_V011' not in registry.read_text():
        raise ValueError('Instala primero Display Manager v0.1.1/v0.1.2 con la categoría Displays')
    raw=(HERE/'DisplayManager.qml').read_text()
    if raw.count('__BACKEND__')!=5:raise ValueError('Plantilla QML inesperada')
    desired={'live_qml':raw.replace('__BACKEND__',str(destinations['live_backend'])).encode(),
             'live_backend':(HERE/'display.py').read_bytes(),
             **{'repo_'+s:(HERE/s).read_bytes() for s in NAMES}}
    modified=[k for k,v in destinations.items() if not v.exists() or v.read_bytes()!=desired[k]]
    for k,v in destinations.items():print(('Actualizar' if k in modified else 'Sin cambios')+': '+str(v))
    if a.dry_run:print('Simulación OK. Ningún archivo modificado.');return
    if not modified:print('Ya está instalado.');return
    backup=base/('display-v021-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True,exist_ok=False)
    (backup/'manifest.json').write_text(json.dumps({'targets':{k:str(v) for k,v in destinations.items()}},indent=2))
    for k,v in destinations.items():
        if v.is_file():shutil.copy2(v,backup/(k+'.old'))
    try:
        for k in modified:
            v=destinations[k];v.parent.mkdir(parents=True,exist_ok=True);v.write_bytes(desired[k])
    except Exception:
        for k in modified:
            v=destinations[k];old=backup/(k+'.old')
            if old.exists():shutil.copy2(old,v)
            elif v.exists():v.unlink()
        raise
    print('Instalación OK. Respaldo:',backup)
    print(f'Restaurar: python3 {HERE}/install.py --restore "{backup}" --repo "{repo}"')
    print('Ningún monitor fue modificado durante la instalación.')
if __name__=='__main__':
    try:run()
    except Exception as ex:print('ERROR:',ex,file=sys.stderr);sys.exit(1)
