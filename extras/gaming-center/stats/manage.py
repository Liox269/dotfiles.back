#!/usr/bin/env python3
"""Install/remove the local session tracker service without touching Caelestia."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

NAME = 'liox-gaming-stats.service'
SOURCE = Path(__file__).resolve().parent / 'tracker.py'
BACKEND = SOURCE.parents[1] / 'status.py'
UNIT = Path.home() / '.config/systemd/user' / NAME

def run(*args):
    return subprocess.run(args,check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('action', choices=['--install','--remove','--status','--dry-run','install','remove','status','dry-run'])
    args=ap.parse_args()
    action=args.action.lstrip('-')
    if action in ('install','dry-run'):
        if not SOURCE.is_file() or not BACKEND.is_file():
            ap.error('Falta tracker.py o status.py; copia todo el paquete al repositorio primero')
        unit=f'''[Unit]
Description=Liox Gaming Center - local session tracker
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart={sys.executable} {SOURCE} watch
Restart=on-failure
RestartSec=8
NoNewPrivileges=true

[Install]
WantedBy=default.target
'''
        if action=='dry-run':
            print('Simulación OK. No se modificó ningún archivo.')
            print('Unidad:',UNIT)
            print('Backend:',BACKEND)
            return
        UNIT.parent.mkdir(parents=True,exist_ok=True)
        if UNIT.exists() and UNIT.read_text()!=unit:
            backup=UNIT.with_suffix('.service.bak')
            backup.write_bytes(UNIT.read_bytes())
            print('Unidad anterior respaldada en',backup)
        UNIT.write_text(unit)
        print('Servicio escrito:', UNIT)
        print('Importando entorno actual de Hyprland a systemd --user...')
        env_names=[s for s in ['HYPRLAND_INSTANCE_SIGNATURE','WAYLAND_DISPLAY','XDG_CURRENT_DESKTOP','XDG_RUNTIME_DIR','PATH'] if os.environ.get(s)]
        if env_names:
            run('systemctl','--user','import-environment',*env_names)
        run('systemctl','--user','daemon-reload')
        run('systemctl','--user','enable','--now',NAME)
        print('Instalación completada. Consulta: systemctl --user status',NAME)
    elif action=='remove':
        subprocess.run(['systemctl','--user','disable','--now',NAME],check=False)
        if UNIT.exists():
            UNIT.unlink()
        subprocess.run(['systemctl','--user','daemon-reload'],check=False)
        print('Servicio desinstalado. Los datos históricos locales NO se han borrado.')
    else:
        subprocess.run(['systemctl','--user','status',NAME,'--no-pager'],check=False)

if __name__=='__main__':
    main()
