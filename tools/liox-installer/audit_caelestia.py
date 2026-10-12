#!/usr/bin/env python3
"""Read-only compatibility audit and isolated staging of Liox Caelestia modules."""
import argparse, hashlib, json, os, re, shutil, sys
from pathlib import Path

MODULE_FILES = {
  'gaming': ('extras/gaming-center/dashboard/Gaming.qml', 'modules/dashboard/Content.qml'),
  'appearance': ('extras/appearance/AdvancedAppearance.qml', 'modules/nexus/pages/WallpaperAndStyle.qml'),
  'display': ('extras/display/DisplayManager.qml', 'modules/nexus/PageRegistry.qml'),
}
REQUIRED = ['modules/nexus/PageRegistry.qml','modules/nexus/PageCompRegistry.qml',
            'modules/nexus/pages/WallpaperAndStyle.qml', 'modules/dashboard/Content.qml']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def inside(p, base): return p == base or base in p.parents

def main():
 p=argparse.ArgumentParser(description='v0.9: inspección y stage, nunca instala en ~/.config')
 p.add_argument('--repo',type=Path,required=True)
 p.add_argument('--caelestia',type=Path,default=Path.home()/'.config/quickshell/caelestia')
 p.add_argument('--output-dir',type=Path)
 p.add_argument('--modules',nargs='+',choices=['gaming','appearance','display'],default=['gaming','appearance','display'])
 a=p.parse_args()
 repo=a.repo.expanduser().resolve(strict=True)
 shell=a.caelestia.expanduser().resolve(strict=True)
 selected=list(dict.fromkeys(a.modules))
 failures=[]; notes=[]; manifest={'version':'0.9','mode':'read_only_or_isolated_stage','modules':{},'compatibility_verified':False,'live_changes':False}
 if not (repo/'config/hypr/hyprland.lua').is_file():failures.append('Repositorio sin config/hypr/hyprland.lua')
 if not (shell/'modules').is_dir():failures.append('No hay árbol QML de Caelestia')
 for f in REQUIRED:
  if not (shell/f).is_file():failures.append('Falta QML: '+f)
  elif (shell/f).is_symlink():failures.append('QML de registro enlazado: '+f)
 for mod in selected:
  src_rel,_=MODULE_FILES[mod]; source=repo/src_rel
  manifest['modules'][mod]={'source':src_rel,'present':source.is_file(),'sha256':sha(source) if source.is_file() else None}
  if not source.is_file():failures.append('Falta fuente de módulo: '+src_rel)
  elif source.is_symlink():failures.append('Fuente enlazada no permitida: '+src_rel)
  if mod=='appearance':
   for file in ['extras/appearance/install.py','extras/appearance/appearance.py']:
    if not (repo/file).is_file():failures.append('Falta dependencia Appearance: '+file)
  if mod=='display':
   for file in ['extras/display/display.py','extras/display/install.py','modules/nexus/pages/DisplaySettingsPage.qml']:
    # DisplaySettingsPage source belongs to an earlier installed shell, not all repos.
    target=(shell/file if file.startswith('modules/') else repo/file)
    if not target.is_file():failures.append('Falta dependencia Displays: '+str(target))
 if not failures:
  regs=(shell/'modules/nexus/PageRegistry.qml').read_text(errors='replace')
  comp=(shell/'modules/nexus/PageCompRegistry.qml').read_text(errors='replace')
  wall=(shell/'modules/nexus/pages/WallpaperAndStyle.qml').read_text(errors='replace')
  dash=(shell/'modules/dashboard/Content.qml').read_text(errors='replace')
  if 'display' in selected and ('LIOX_DISPLAY_SETTINGS_V011' not in regs or 'LIOX_DISPLAY_SETTINGS_V011' not in comp):
   notes.append('Displays no está registrado: v0.2.2 por sí solo no añade la sección lateral')
  if 'appearance' in selected and 'AdvancedAppearance {' not in wall:
   notes.append('Advanced Appearance no registrado en WallpaperAndStyle.qml')
  if 'gaming' in selected and 'Gaming' not in dash:
   notes.append('Gaming no registrado en Content.qml')
  if 'display' in selected and (shell/'modules/nexus/pages/DisplayManager.qml').is_file():
   notes.append('La instalación existente de Displays puede diferir de la fuente; revisar diff antes de reinstalar')
 manifest['notes']=notes
 manifest['errors']=failures
 print('LIOX INSTALLER v0.9 — CAELESTIA (AUDITORÍA SIN APLICAR)')
 for mod,v in manifest['modules'].items(): print(f'{mod}: '+('fuente encontrada' if v['present'] else 'FALTA FUENTE'))
 for note in notes:print('AVISO:',note)
 for f in failures:print('ERROR:',f)
 print('Compatibilidad exacta Caelestia v2.5.0: NO VERIFICADA; no se modifica QML activo.')
 if failures: return 2
 if a.output_dir:
  target=a.output_dir.expanduser().absolute()
  if target.exists() or target.is_symlink():raise ValueError('La carpeta de salida debe ser nueva')
  if not inside(target,Path('/tmp').resolve()):raise ValueError('Solo se permite generar el stage en /tmp')
  if target == Path('/tmp'):raise ValueError('Salida inválida')
  target.mkdir(mode=0o700,parents=False)
  try:
   for mod in selected:
    paths=[MODULE_FILES[mod][0]]
    if mod=='appearance':paths += ['extras/appearance/install.py','extras/appearance/appearance.py']
    if mod=='display':paths += ['extras/display/install.py','extras/display/display.py']
    for rel in paths:
     original=repo/rel
     saved=target/'sources'/rel
     saved.parent.mkdir(parents=True,exist_ok=True)
     shutil.copyfile(original,saved)
   for rel in REQUIRED:
    original=shell/rel;saved=target/'baseline'/rel
    saved.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(original,saved)
   manifest['stage_only']=True
   (target/'audit.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
  except Exception:
   shutil.rmtree(target);raise
  print('Stage aislado:',target)
 else:print('Simulación sin escritura.')
 print('No se instaló ni modificó Caelestia, Waywallen, Matugen o Hyprland.')
 return 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as ex:print('ERROR:',ex,file=sys.stderr);sys.exit(1)
