#!/usr/bin/env python3
"""Liox v0.3: offline, conservative staging of portable Hyprland Lua configuration.
No live config, package, service or compositor is ever changed.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

MONITOR_LINE = re.compile(r'^\s*hl\.monitor\s*\(\s*\{[^\n]*\}\s*\)\s*$', re.M)
LEGACY_LINE = re.compile(r'^\s*monitor\s*=.*$', re.M)
NAME_PATTERN = re.compile(r'^[A-Za-z0-9_.-]{1,80}$')
MODES = re.compile(r'^\d{2,5}x\d{2,5}@\d+(?:\.\d+)?$')

def valid_output(m):
    if not isinstance(m, dict): return None
    name = m.get('name')
    if not isinstance(name,str) or not NAME_PATTERN.fullmatch(name): return None
    try:
        w, h, hz, scale = int(m['width']), int(m['height']), float(m['refreshRate']), float(m.get('scale',1))
        x,y = int(m.get('x',0)),int(m.get('y',0))
        transform=int(m.get('transform',0))
    except (ValueError,TypeError,KeyError,OverflowError): return None
    if not (320<=w<=16384 and 200<=h<=8640 and 20<=hz<=500 and .5<=scale<=4 and 0<=transform<=7 and abs(x)<=100000 and abs(y)<=100000): return None
    return {'name':name,'width':w,'height':h,'hz':hz,'scale':scale,'x':x,'y':y,'transform':transform}

def monitors_from(report):
    src=report.get('monitors')
    if not isinstance(src,dict) or src.get('available') is not True: return []
    out=[]
    for item in src.get('outputs',[]):
        v=valid_output(item)
        if v and v['name'] not in [x['name'] for x in out]: out.append(v)
    return out

def lua_lines(monitors):
    lines=[]
    for m in monitors:
        mode=f"{m['width']}x{m['height']}@{m['hz']:.2f}"
        scale=f"{m['scale']:g}"
        lines.append('hl.monitor({ output = "%s", mode = "%s", position = "%sx%s", scale = %s, transform = %s })' % (m['name'], mode, m['x'],m['y'],scale,m['transform']))
    return '\n'.join(lines)

def generate(source,monitors):
    lines=list(MONITOR_LINE.finditer(source))
    if not lines: raise ValueError('No se encontraron declaraciones hl.monitor compatibles; revisar manualmente')
    if len(lines)>16: raise ValueError('Demasiadas declaraciones de monitor; abortando')
    # Replace entire contiguous monitor section only. Reject scattered statements to avoid moving other code.
    region=source[lines[0].start():lines[-1].end()]
    if region.strip()!='\n'.join(m.group().strip() for m in lines):
        raise ValueError('Declaraciones hl.monitor intercaladas con otro código; revisar manualmente')
    if monitors:
        new=lua_lines(monitors)
        warning='Se aplican salidas del informe; su validez puede cambiar al conectar otro monitor.'
    else:
        # Hyprland dynamic monitor output: choose safe auto mode and position via per-output wildcard.
        new='hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })'
        warning='Sin monitores detectados: se genera salida genérica; verificar soporte de wildcard Lua antes de activar.'
    result=source[:lines[0].start()]+new+source[lines[-1].end():]
    return result,warning

def run(argv=None):
    p=argparse.ArgumentParser(description='Generar vista previa de Hyprland Lua portable; nunca modifica ~/.config')
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--report',type=Path,help='diagnostic.json generado por diagnose.py; si falta, usa modo genérico')
    p.add_argument('--output',type=Path,help='Crear archivo generado fuera de ~/.config/hypr (opt-in)')
    a=p.parse_args(argv)
    repo=a.repo.expanduser().resolve()
    source_path=repo/'config/hypr/hyprland.lua'
    if not source_path.is_file() or source_path.is_symlink(): raise ValueError('Repositorio sin config/hypr/hyprland.lua regular')
    source=source_path.read_text()
    if a.report:
        report=json.loads(a.report.expanduser().read_text())
        mons=monitors_from(report)
    else: mons=[]
    generated,warning=generate(source,mons)
    print('LIOX INSTALLER v0.3 - HYPRLAND LUA PORTABLE (sin aplicar)')
    print('Repositorio:',repo)
    print('Monitores válidos:',len(mons))
    print('Aviso:',warning)
    print('Declaraciones resultantes:')
    for line in MONITOR_LINE.findall(generated): print(' ',line.strip())
    # Explicitly surface host-specific references, without modifying them implicitly.
    hardcoded=sorted(set(re.findall(r'/home/[A-Za-z0-9_.-]+/',generated)))
    if hardcoded: print('Rutas personales que requieren revisión:', ', '.join(hardcoded))
    if a.output:
        target=a.output.expanduser().absolute()
        home=Path.home().resolve()
        live=(home/'.config').resolve()
        if target.is_relative_to(live) or target.is_relative_to(repo) or target.exists() or target.is_symlink():
            raise ValueError('Destino inseguro, existente o dentro de ~/.config o repo; elige un archivo nuevo en /tmp o ~/.local/state')
        target.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:f.write(generated)
        print('Archivo generado (NO INSTALADO):',target)
    else: print('SIMULACIÓN: nada modificado. Con --output puedes generar un archivo para inspección.')
    print('IMPORTANTE: esto prepara SOLO las declaraciones de monitor. NO es una instalación automática de Hyprland ni garantiza compatibilidad entre versiones.')

if __name__=='__main__':
    try: run()
    except Exception as e:print('ERROR:',e,file=sys.stderr);sys.exit(1)
