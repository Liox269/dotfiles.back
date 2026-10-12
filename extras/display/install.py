#!/usr/bin/env python3
"""Move Liox Display Manager v0.1 into its own Caelestia Settings sidebar page."""
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARKER = '// LIOX_DISPLAY_MANAGER_V01'
PAGE_MARKER = '// LIOX_DISPLAY_SETTINGS_V011'
OLD_BLOCK = '''        // LIOX_DISPLAY_MANAGER_V01
        DisplayManager {
            Layout.fillWidth: true
        }'''
REG_ENTRY = '''        // LIOX_DISPLAY_SETTINGS_V011
        {
            label: Tr.tr("Displays"),
            icon: "monitor",
            description: Tr.tr("Resolution, refresh rate and scale"),
            category: "connectivity"
        },

'''
COMP_ENTRY = '''        // LIOX_DISPLAY_SETTINGS_V011
        Component {
            StackPage {
                Component {
                    DisplaySettingsPage {}
                }
            }
        },

'''

def destinations(home, repo):
    nexus = home/'.config/quickshell/caelestia/modules/nexus'
    pages = nexus/'pages'
    return {
        'wall':pages/'WallpaperAndStyle.qml',
        'registry':nexus/'PageRegistry.qml',
        'components':nexus/'PageCompRegistry.qml',
        'qml':pages/'DisplayManager.qml',
        'page':pages/'DisplaySettingsPage.qml',
        'backend':home/'.local/lib/liox-display/display.py',
        **{'repo_'+f:repo/'extras/display'/f for f in ('DisplayManager.qml','DisplaySettingsPage.qml','display.py','install.py','README.md')},
    }

def desired(targets):
    for key in ('wall','registry','components'):
        if not targets[key].exists():
            raise ValueError(f'No existe {targets[key]}')
    wall=targets['wall'].read_text()
    if wall.count(OLD_BLOCK) == 1:
        wall=wall.replace('\n'+OLD_BLOCK,'',1)
    elif MARKER in wall or 'DisplayManager {' in wall:
        raise ValueError('Integración anterior inesperada en WallpaperAndStyle.qml. No se modificó nada.')
    if 'AdvancedAppearance {' not in wall:
        raise ValueError('No se encuentra Advanced Appearance; revisión manual antes de continuar.')
    registry=targets['registry'].read_text()
    comps=targets['components'].read_text()
    for label,source,entry in [('PageRegistry',registry,REG_ENTRY),('PageCompRegistry',comps,COMP_ENTRY)]:
        if PAGE_MARKER in source:
            if source.count(PAGE_MARKER)!=1 or entry not in source:
                raise ValueError(f'{label} contiene un registro Display inesperado')
        elif source.count('        // Connectivity')!=1:
            raise ValueError(f'{label}: punto de inserción no encontrado')
    if PAGE_MARKER not in registry:
        registry=registry.replace('        // Connectivity',REG_ENTRY+'        // Connectivity',1)
    if PAGE_MARKER not in comps:
        comps=comps.replace('        // Connectivity',COMP_ENTRY+'        // Connectivity',1)
    qml=(HERE/'DisplayManager.qml').read_text()
    if qml.count('__BACKEND__')!=2:
        raise ValueError('DisplayManager.qml no corresponde a la plantilla prevista')
    qml=qml.replace('__BACKEND__',str(targets['backend']))
    result={'wall':wall.encode(), 'registry':registry.encode(), 'components':comps.encode(),
            'qml':qml.encode(), 'page':(HERE/'DisplaySettingsPage.qml').read_bytes(),
            'backend':(HERE/'display.py').read_bytes()}
    for f in ('DisplayManager.qml','DisplaySettingsPage.qml','display.py','install.py','README.md'):
        result['repo_'+f]=(HERE/f).read_bytes()
    return result

def main():
    p=argparse.ArgumentParser()
    a=p.add_mutually_exclusive_group(required=True)
    a.add_argument('--dry-run',action='store_true')
    a.add_argument('--install',action='store_true')
    a.add_argument('--restore',type=Path)
    p.add_argument('--home',type=Path,default=Path.home())
    p.add_argument('--repo',type=Path,default=Path.cwd())
    opts=p.parse_args()
    home=opts.home.expanduser().resolve(); repo=opts.repo.expanduser().resolve()
    target=destinations(home,repo)
    if opts.restore:
        folder=opts.restore.expanduser().resolve()
        base=(home/'.local/share/liox-display/backups').resolve()
        if folder==base or not folder.is_relative_to(base): raise ValueError('Respaldo fuera del directorio permitido')
        manifest=json.loads((folder/'manifest.json').read_text())
        if manifest['targets']!={k:str(v) for k,v in target.items()}:
            raise ValueError('El manifiesto no coincide con los destinos')
        for k,v in target.items():
            old=folder/(k+'.old')
            if old.is_file():
                v.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,v)
            elif v.is_file():v.unlink()
        print('Restauración completada. Reinicia Caelestia.')
        return
    content=desired(target)
    modified=[k for k,v in target.items() if not v.is_file() or v.read_bytes()!=content[k]]
    for k,v in target.items():print(('Actualizar' if k in modified else 'Sin cambios')+': '+str(v))
    if opts.dry_run:
        print('Simulación OK; sin cambios escritos.')
        return
    if not modified:
        print('Ya instalado. Sin cambios.')
        return
    backup=home/'.local/share/liox-display/backups'/('display-v011-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    (backup/'manifest.json').write_text(json.dumps({'targets':{k:str(v) for k,v in target.items()}},indent=2))
    for k,v in target.items():
        if v.is_file():shutil.copy2(v,backup/(k+'.old'))
    written=[]
    try:
        for k in modified:
            v=target[k];v.parent.mkdir(parents=True,exist_ok=True);v.write_bytes(content[k]);written.append(k)
    except Exception:
        for k in reversed(written):
            v=target[k];old=backup/(k+'.old')
            if old.is_file():shutil.copy2(old,v)
            elif v.is_file():v.unlink()
        raise
    print('Instalación OK. Respaldo:',backup)
    print(f'Restaurar: python3 {HERE/"install.py"} --restore "{backup}" --repo "{repo}"')
    print('No se modificaron Hyprland, Waywallen, Gaming, DualSense ni Advanced Appearance.')

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr);sys.exit(1)
