#!/usr/bin/env python3
"""Liox v0.4: prepare portable configuration drafts; NEVER install live files."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

from portable_hypr import generate, monitors_from

ENV_PATTERN = re.compile(r'^\s*hl\.env\("(CAELESTIA_SCREENSHOTS_DIR|CAELESTIA_RECORDINGS_DIR)",\s*"[^"]*"\)\s*$', re.M)
REQUIRED_KEYS = ('CAELESTIA_SCREENSHOTS_DIR', 'CAELESTIA_RECORDINGS_DIR')

def portable_env(source):
    lines = ENV_PATTERN.findall(source)
    if sorted(lines) != sorted(REQUIRED_KEYS):
        raise ValueError('env.lua no coincide con el formato esperado; revisar manualmente')
    def substitute(m):
        key = 'CAELESTIA_SCREENSHOTS_DIR' if 'SCREENSHOTS' in m.group() else 'CAELESTIA_RECORDINGS_DIR'
        suffix = '/Pictures/Screenshots' if key == REQUIRED_KEYS[0] else '/Videos/Recordings'
        return f'hl.env("{key}", os.getenv("HOME") .. "{suffix}")'
    return ENV_PATTERN.sub(substitute, source)

def check_caelestia(repo, home, report):
    shell_file = repo / 'config/caelestia/shell.json'
    shell = json.loads(shell_file.read_text())
    actual = home / '.config/quickshell/caelestia'
    pages = actual / 'modules/nexus/pages'
    qml = pages / 'WallpaperAndStyle.qml'
    registries = [actual / 'modules/nexus/PageRegistry.qml', actual / 'modules/nexus/PageCompRegistry.qml']
    r = {
        'quickshell_tree_exists': actual.is_dir(),
        'wallpaper_and_style_exists': qml.is_file(),
        'page_registries_exist': all(p.is_file() for p in registries),
        'repo_wallpaper_enabled': shell.get('background',{}).get('wallpaperEnabled'),
        'gpu_vendors': report.get('gpu',{}).get('vendors',[]),
        'repo_gpu_type': shell.get('services',{}).get('gpuType'),
        'can_install_custom_qml': False,
        'status': 'inspection_only',
        'notes': ['Caelestia v2.5.0 is the integration target; exact installed version is not verified.',
                  'Custom QML installation is disabled until compatibility and backups are validated.',
                  'Do not enable Caelestia wallpaper when Waywallen manages wallpaper.']
    }
    if r['repo_wallpaper_enabled'] is not False:
        r['notes'].append('WARNING: repository wallpaper setting is not false.')
    if 'NVIDIA' not in r['gpu_vendors'] and r['repo_gpu_type'] == 'Nvidia':
        r['notes'].append('GPU type Nvidia is machine-specific; select the appropriate Caelestia setting on the destination PC.')
    if not actual.is_dir():
        r['notes'].append('No local Caelestia QML tree; install official compatible shell first.')
    return r

def safe_out(target, repo, home):
    target = target.expanduser().absolute()
    for base in (repo, home / '.config'):
        if target == base or target.is_relative_to(base):
            raise ValueError('Salida no permitida en repositorio ni ~/.config')
    if target.exists() or target.is_symlink():
        raise ValueError('Directorio de salida ya existe; elige un destino nuevo')
    current = target.parent
    while True:
        if current.is_symlink(): raise ValueError('Ruta padre con enlace simbólico')
        if current == current.parent: break
        current = current.parent
    return target

def run(argv=None):
    parser = argparse.ArgumentParser(description='Genera borradores portátiles, sin modificar configuraciones activas')
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, help='Directorio nuevo para el resultado, fuera del repositorio y ~/.config')
    args = parser.parse_args(argv)
    repo = args.repo.expanduser().resolve()
    home = Path.home().resolve()
    report = json.loads(args.report.expanduser().read_text())
    monitor_source = repo / 'config/hypr/hyprland.lua'
    env_source = repo / 'config/hypr/hyprland/env.lua'
    for src in (monitor_source, env_source, repo/'config/caelestia/shell.json'):
        if not src.is_file() or src.is_symlink() or not src.resolve().is_relative_to(repo):
            raise ValueError('Fuente inexistente, symlink o fuera de repo: '+str(src))
    mons = monitors_from(report)
    lua, warning = generate(monitor_source.read_text(), mons)
    env = portable_env(env_source.read_text())
    scan = {}
    for name, content in [('hyprland.lua',lua), ('env.lua',env)]:
        scan[name] = sorted(set(re.findall(r'/home/[A-Za-z0-9_.-]+(?:/[^\s"\']*)?',content)))
    cael = check_caelestia(repo, home, report)
    result = {'version':'0.4', 'mode':'preview_only', 'monitors':len(mons), 'monitor_warning':warning,
              'paths_generated':{'screenshots':'$HOME/Pictures/Screenshots','recordings':'$HOME/Videos/Recordings'},
              'remaining_user_paths':scan, 'caelestia':cael, 'live_changes':False}
    print('LIOX INSTALLER v0.4 — VISTA PREVIA (SIN APLICAR)')
    print('Monitores:',len(mons),'—',warning)
    print('Rutas personales: generadas desde HOME; directorios NO creados')
    print('Caelestia QML:', 'detectado' if cael['quickshell_tree_exists'] else 'no detectado')
    print('Registros de páginas:', 'detectados' if cael['page_registries_exist'] else 'no detectados')
    print('GPU en repo:',cael['repo_gpu_type'],'| GPU detectadas:',', '.join(cael['gpu_vendors']) or 'desconocidas')
    for note in cael['notes']: print('Nota:',note)
    for name, paths in scan.items():
        if paths: print('Rutas restantes a revisar',name,paths)
    if args.output_dir:
        target = safe_out(args.output_dir, repo, home)
        target.mkdir(parents=True,mode=0o700)
        try:
            (target/'hyprland').mkdir(mode=0o700)
            for path, body in [('hyprland.lua',lua),('hyprland/env.lua',env),('compatibility.json',json.dumps(result,indent=2,ensure_ascii=False)+'\n')]:
                out=target/path
                with out.open('x') as f: f.write(body)
                out.chmod(stat.S_IRUSR|stat.S_IWUSR)
        except BaseException:
            import shutil
            shutil.rmtree(target)
            raise
        print('Borradores creados en:', target)
    else:
        print('Simulación: ningún archivo creado ni modificado.')
    print('NO se instalan paquetes, QML, servicios ni Hyprland; no ejecutar estos archivos sin revisión.')

if __name__ == '__main__':
    try: run()
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(1)
