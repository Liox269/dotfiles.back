#!/usr/bin/env python3
"""Liox v1.0 preview. Orchestrates read-only checks and isolated staging only."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
STEPS={
 'hypr': [('diagnose.py',[]),('portable_setup.py',[])],
 'visual': [('prepare_visual.py',[])],
 'caelestia': [('audit_caelestia.py',[])],
}

def run(name,*args):
 cmd=[sys.executable,str(HERE/name),*map(str,args)]
 print('\n$ '+ ' '.join(cmd),flush=True)
 ret=subprocess.run(cmd,check=False)
 if ret.returncode:raise RuntimeError(f'{name} terminó con código {ret.returncode}')

def main():
 p=argparse.ArgumentParser(description='Asistente Liox v1.0 preview: inspección y pruebas limitadas a /tmp')
 p.add_argument('--repo',type=Path,default=Path.home()/'dotfiles-clean')
 p.add_argument('--modules',nargs='+',choices=['hypr','visual','caelestia'],default=['hypr','visual','caelestia'])
 p.add_argument('--workspace',type=Path,default=Path('/tmp/liox-v10-preview'))
 p.add_argument('--stage',action='store_true',help='Generar borradores en un workspace NUEVO bajo /tmp')
 p.add_argument('--apply-temp',action='store_true',help='Instalar los borradores SOLO en nuevos directorios /tmp; requiere --stage')
 p.add_argument('--caelestia',type=Path,default=Path.home()/'.config/quickshell/caelestia')
 a=p.parse_args()
 selected=list(dict.fromkeys(a.modules))
 repo=a.repo.expanduser().resolve(strict=True)
 work=a.workspace.expanduser().absolute()
 if a.apply_temp and not a.stage: p.error('--apply-temp requiere --stage')
 if work==Path('/tmp') or not work.is_relative_to(Path('/tmp')):p.error('El workspace debe estar bajo /tmp')
 if work.is_symlink() or work.exists():p.error('El workspace debe ser nuevo, no existente ni enlace')
 for parent in (work,*work.parents):
  if parent == Path('/tmp'):break
  if parent.is_symlink():p.error('Un directorio padre es un enlace simbólico')
 print('LIOX v1.0 PREVIEW — NO ES INSTALADOR DE PRODUCCIÓN')
 print('Repositorio:',repo)
 print('Módulos:',', '.join(selected))
 print('Modo:', 'INSTALACIÓN TEMPORAL' if a.apply_temp else 'STAGE' if a.stage else 'SOLO INSPECCIÓN')
 if not a.stage:
  if 'hypr' in selected: run('diagnose.py')
  if 'visual' in selected:run('prepare_visual.py','--repo',repo)
  if 'caelestia' in selected:run('audit_caelestia.py','--repo',repo,'--caelestia',a.caelestia)
  print('\nINSPECCIÓN COMPLETA. Ningún archivo activo modificado.')
  return
 work.mkdir(mode=0o700,parents=False)
 try:
  if 'hypr' in selected:
   diag=work/'diagnostic.json'
   run('diagnose.py','--output',diag)
   run('portable_setup.py','--repo',repo,'--report',diag,'--output-dir',work/'hypr-stage')
  if 'visual' in selected:run('prepare_visual.py','--repo',repo,'--output-dir',work/'visual-stage')
  if 'caelestia' in selected:run('audit_caelestia.py','--repo',repo,'--caelestia',a.caelestia,'--output-dir',work/'caelestia-stage')
  if a.apply_temp:
   if 'hypr' in selected:run('install_hypr_tree.py','--repo',repo,'--from-dir',work/'hypr-stage','--target',work/'installed-hypr','--apply')
   if 'visual' in selected:run('install_visual.py','--from-dir',work/'visual-stage','--target-root',work/'installed-visual','--apply')
   if 'caelestia' in selected:run('install_caelestia_stage.py','--stage',work/'caelestia-stage','--target-root',work/'installed-caelestia','--apply')
 except Exception:
  print('\nETAPA INCOMPLETA: revisa el mensaje anterior. El workspace temporal se conserva para inspección.',file=sys.stderr)
  raise
 print('\nPREPARACIÓN COMPLETADA:',work)
 print('No se modificó ~/.config, no se activó Hyprland ni se inició Caelestia.')
 if a.apply_temp:print('Los comandos de restauración y sus recibos están impresos arriba; restaura cada etapa por separado.')
 print('PENDIENTE: compatibilidad QML 2.5.0, árbol limpio y políticas de rollback global antes de instalación real.')

if __name__=='__main__':
 try:main()
 except Exception as e:print('ERROR:',e,file=sys.stderr);sys.exit(1)
