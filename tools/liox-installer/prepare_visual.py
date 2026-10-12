#!/usr/bin/env python3
"""Liox v0.7: read-only compatibility audit and optional isolated staged config.
Never writes to ~/.config, services or the source repository.
"""
import argparse, hashlib, json, os, pathlib, re, shutil, stat, sys, tomllib
from datetime import datetime, timezone

HOME=pathlib.Path.home()
FILES={
 'waywallen/config.toml':'config/waywallen/config.toml',
 'matugen/config.toml':'config/matugen/config.toml',
 'caelestia/shell.json':'config/caelestia/shell.json',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def regular(p,base):
 if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(base):raise ValueError('Fuente no regular o fuera de repo: '+str(p))
 b=p.read_bytes()
 if len(b)>2_000_000 or b'\0' in b:raise ValueError('Archivo fuente inválido o grande: '+str(p))
 return b

def waywallen_clean(s):
 # Retain user's renderer/layout settings, discard hardware display IDs and last selected wallpaper.
 lines=s.splitlines(keepends=True);out=[];skip=False;removed=0
 for line in lines:
  head=re.match(r'^\s*\[([^\]]+)\]\s*(?:#.*)?$',line)
  if head:skip=head.group(1).startswith('display.');removed+=int(skip)
  if skip:continue
  if re.match(r'^\s*last_wallpaper\s*=',line):removed+=1;continue
  out.append(line)
 cleaned=''.join(out)
 tomllib.loads(cleaned)
 return cleaned,removed

def safe_target(path,repo):
 p=path.expanduser().absolute()
 if p.exists() or p.is_symlink():raise ValueError('Destino ya existe; usa uno nuevo')
 if p==repo or p.is_relative_to(repo) or p==HOME/'.config' or p.is_relative_to(HOME/'.config'):
  raise ValueError('Destino no permitido dentro del repo o ~/.config')
 for ancestor in (p,*p.parents):
  if ancestor.is_symlink():raise ValueError('Enlace simbólico en ruta destino: '+str(ancestor))
 if not p.parent.is_dir():raise ValueError('El directorio padre debe existir: '+str(p.parent))
 return p

def inspect(repo,home):
 repo=repo.resolve(); original={}
 for rel,src in FILES.items():original[rel]=regular(repo/src,repo)
 way,removed=waywallen_clean(original['waywallen/config.toml'].decode())
 mat=original['matugen/config.toml'].decode();tomllib.loads(mat)
 shell=json.loads(original['caelestia/shell.json']);wallpaper=shell.get('background',{}).get('wallpaperEnabled')
 if wallpaper is not False:raise ValueError('Caelestia wallpaperEnabled debe ser false; revisar manualmente')
 # Only minimal safe config; never import users' app favourites, ID-based monitor config, or Nvidia GPU setting.
 minimal={'background':{'wallpaperEnabled':False}}
 out={ 'waywallen/config.toml':way.encode(), 'matugen/config.toml':mat.encode(),
       'caelestia/shell.json':(json.dumps(minimal,indent=2,ensure_ascii=False)+'\n').encode() }
 qml=home/'.config/quickshell/caelestia'
 pages=qml/'modules/nexus/pages/WallpaperAndStyle.qml'
 registry=[qml/'modules/nexus/PageRegistry.qml',qml/'modules/nexus/PageCompRegistry.qml']
 checks={k:bool(shutil.which(k)) for k in ('hyprctl','caelestia','quickshell','qs','waywallen','matugen')}
 report={
  'version':'0.7','mode':'inspection_and_isolated_stage_only',
  'source_repo':str(repo),
  'checks':checks,
  'caelestia':{'qml_tree_exists':qml.is_dir(),'wallpaper_page_exists':pages.is_file(),
               'registries_exist':all(p.is_file() for p in registry),
               'qml_version_verified':False,'custom_qml_install_allowed':False,
               'repo_gpu_type':shell.get('services',{}).get('gpuType'),
               'staged_shell_settings':['background.wallpaperEnabled'],
               'other_user_shell_settings_omitted':True},
  'waywallen':{'removed_machine_state_entries':removed,'toml_valid':True},
  'matugen':{'toml_valid':True,'template_paths_checked':False},
  'notes':['No installers, packages, services, live QML or monitor settings are changed.',
           'Staged Caelestia shell.json is intentionally minimal, not a full configuration.',
           'Caelestia 2.5.0 API compatibility is NOT confirmed by file presence.',
           'Waywallen/Matugen dependencies and template paths require per-machine validation.',
           'Do not enable Caelestia wallpaper while Waywallen draws wallpaper.'],
  'live_changes':False,
 }
 return out,report

def prepare(argv=None):
 parser=argparse.ArgumentParser(description='Liox v0.7: inspect or stage portable visual config without installing')
 parser.add_argument('--repo',type=pathlib.Path,required=True)
 parser.add_argument('--output-dir',type=pathlib.Path)
 a=parser.parse_args(argv);repo=a.repo.expanduser().resolve()
 if not repo.is_dir():raise ValueError('Repositorio inexistente')
 out,report=inspect(repo,HOME)
 print('LIOX v0.7 - COMPONENTES VISUALES (SIN APLICAR)')
 print('Configuraciones:',', '.join(out))
 print('Waywallen: entradas de estado de pantalla/fondo retiradas:',report['waywallen']['removed_machine_state_entries'])
 print('Caelestia QML:', 'presente' if report['caelestia']['qml_tree_exists'] else 'ausente', '| versión exacta NO verificada')
 print('Dependencias ausentes:',', '.join(k for k,v in report['checks'].items() if not v) or 'ninguna detectada')
 for note in report['notes']:print('AVISO:',note)
 if a.output_dir:
  target=safe_target(a.output_dir,repo); stage=target.with_name('.'+target.name+'.liox-staging-'+str(os.getpid()))
  try:
   stage.mkdir(mode=0o700)
   for rel,data in out.items():
    p=stage/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data)
    p.chmod(0o600)
   report['sha256']={k:sha(v) for k,v in out.items()}
   (stage/'compatibility.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
   (stage/'compatibility.json').chmod(0o600)
   if target.exists() or target.is_symlink():raise ValueError('El destino apareció durante preparación')
   stage.rename(target)
  except BaseException:
   if stage.exists():shutil.rmtree(stage)
   raise
  print('Archivos de PRUEBA preparados:',target)
 else:print('Simulación: ningún archivo escrito.')
 print('Ninguna configuración activa modificada.')
if __name__=='__main__':
 try:prepare()
 except Exception as e:print('ERROR:',e,file=sys.stderr);sys.exit(1)
