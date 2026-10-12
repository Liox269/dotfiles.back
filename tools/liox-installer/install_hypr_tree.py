#!/usr/bin/env python3
"""Liox v0.6: install a complete portable Hyprland Lua tree to a NEW directory.
Never touches an existing target, symlink, compositor, package manager or services.
Restore removes only an unmodified tree installed by this tool.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone

REQUIRED = ('hyprland.lua','variables.lua','hyprland/env.lua','hyprland/general.lua',
            'hyprland/input.lua','hyprland/misc.lua','hyprland/animations.lua',
            'hyprland/decoration.lua','hyprland/group.lua','hyprland/execs.lua',
            'hyprland/rules.lua','hyprland/gestures.lua','hyprland/keybinds.lua')
GENERATED = ('hyprland.lua','hyprland/env.lua')

def sha(data): return hashlib.sha256(data).hexdigest()

def files_in(root):
    if root.is_symlink() or not root.is_dir(): raise ValueError('Origen no es directorio normal: '+str(root))
    found = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        folder=Path(base)
        for name in dirs:
            p=folder/name
            if p.is_symlink(): raise ValueError('Directorio enlazado dentro del origen: '+str(p))
        for name in files:
            p=folder/name
            rel=p.relative_to(root).as_posix()
            if p.is_symlink():
                # A source symlink may refer only to a REGULAR file within the original tree.
                actual=p.resolve(strict=True)
                if not actual.is_relative_to(root.resolve()) or not actual.is_file():
                    raise ValueError('Enlace de origen fuera del árbol o no archivo: '+str(p))
                data=actual.read_bytes()
            elif p.is_file():data=p.read_bytes()
            else:raise ValueError('Origen no regular: '+str(p))
            if len(data)>10*1024*1024:raise ValueError('Archivo demasiado grande: '+rel)
            found[rel]=data
    return found

def prepare(repo,drafts):
    root=repo/'config/hypr'
    data=files_in(root)
    for name in REQUIRED:
        if name not in data:raise ValueError('Falta dependencia Hyprland Lua: '+name)
    if drafts.is_symlink() or not drafts.is_dir():raise ValueError('Borradores no válidos')
    for name in GENERATED:
        src=drafts/name
        if src.is_symlink() or not src.is_file():raise ValueError('Falta borrador regular: '+name)
        raw=src.read_bytes()
        if not raw or b'\0' in raw:raise ValueError('Borrador inválido: '+name)
        if re.search(rb'/home/[A-Za-z0-9_.-]+/',raw):raise ValueError('Borrador con ruta personal: '+name)
        data[name]=raw
    # v0.6 deliberately refuses unresolved machine-specific home paths anywhere else.
    issues=[name for name,raw in data.items() if re.search(rb'/home/[A-Za-z0-9_.-]+/',raw)]
    if issues:raise ValueError('Rutas personales pendientes en el árbol: '+', '.join(issues[:12]))
    return data

def safe_target(path):
    path=path.expanduser().absolute()
    for parent in path.parents:
        if parent.is_symlink():raise ValueError('Ruta destino contiene enlace: '+str(parent))
    return path

def prepare_storage(path,target,repo):
    path=safe_target(path)
    if path==target or path.is_relative_to(target) or path.is_relative_to(repo):raise ValueError('Almacén no permitido')
    if path.exists() and (not path.is_dir() or path.stat().st_mode & 0o077):
        raise ValueError('El almacén debe ser un directorio privado (0700)')
    return path

def apply(data,target,storage):
    # Fresh only. No force, no overwrite, no symlink replacement.
    if target.exists() or target.is_symlink():raise ValueError('Destino existente: no se sobrescribe ni reemplaza: '+str(target))
    if not target.parent.is_dir():raise ValueError('Falta directorio padre: '+str(target.parent))
    storage.mkdir(parents=True,mode=0o700,exist_ok=True)
    if storage.stat().st_mode & 0o077:raise ValueError('Almacén no privado')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    receipt=storage/('hypr-tree-v06-'+stamp)
    receipt.mkdir(mode=0o700)
    staged=target.with_name('.'+target.name+'.liox-stage-'+str(os.getpid()))
    if staged.exists() or staged.is_symlink():raise ValueError('Staging ya existente')
    try:
        staged.mkdir(mode=0o700)
        for rel,content in data.items():
            dest=staged/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f: f.write(content)
            dest.chmod(0o600 if rel.endswith('.lua') else 0o644)
        manifest={'version':'0.6','target':str(target),'files':{rel:sha(v) for rel,v in data.items()}}
        (receipt/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (receipt/'manifest.json').chmod(0o600)
        if target.exists() or target.is_symlink():raise ValueError('Destino apareció durante preparación')
        staged.rename(target)
    except BaseException:
        if staged.exists():shutil.rmtree(staged)
        if receipt.exists():shutil.rmtree(receipt)
        raise
    print('INSTALACIÓN OK (sin activar Hyprland):',target)
    print('RECIBO:',receipt)
    print('Para restaurar: python3 install_hypr_tree.py --restore "'+str(receipt)+'" --target "'+str(target)+'"')

def restore(receipt,target,storage):
    receipt=receipt.expanduser().absolute()
    if receipt.is_symlink() or receipt.parent!=storage or not receipt.is_dir():raise ValueError('Recibo fuera del almacén')
    mf=receipt/'manifest.json'
    if mf.is_symlink() or not mf.is_file():raise ValueError('Falta manifiesto')
    manifest=json.loads(mf.read_text())
    if manifest.get('version')!='0.6' or manifest.get('target')!=str(target):raise ValueError('Recibo no corresponde al destino')
    if target.is_symlink() or not target.is_dir():raise ValueError('Destino modificado o inexistente')
    current=files_in(target)
    expected=manifest['files']
    if {rel:sha(data) for rel,data in current.items()} != expected:
        raise ValueError('Destino modificado después de instalar; restauración bloqueada')
    # No deletion if a different mount is now present.
    if os.path.ismount(target):raise ValueError('Destino es punto de montaje; bloqueado')
    shutil.rmtree(target)
    print('RESTAURACIÓN: eliminado únicamente el árbol instalado sin cambios:',target)
    print('El recibo se conserva:',receipt)

def main(argv=None):
    p=argparse.ArgumentParser(description='Instalación segura del árbol completo de Hyprland Lua (solo destino nuevo)')
    p.add_argument('--repo',type=Path)
    p.add_argument('--from-dir',type=Path)
    p.add_argument('--target',type=Path,default=Path.home()/'.config/hypr')
    p.add_argument('--store',type=Path,default=Path.home()/'.local/state/liox-installer/backups')
    p.add_argument('--apply',action='store_true')
    p.add_argument('--restore',type=Path)
    a=p.parse_args(argv)
    target=safe_target(a.target)
    storage=prepare_storage(a.store,target,a.repo.expanduser().resolve() if a.repo else target)
    if a.restore:
        if a.apply or a.repo or a.from_dir:raise ValueError('Restauración es modo independiente')
        restore(a.restore,target,storage);return
    if not a.repo or not a.from_dir:raise ValueError('Necesitas --repo y --from-dir')
    repo=a.repo.expanduser().resolve()
    if target==repo or target.is_relative_to(repo) or repo.is_relative_to(target):raise ValueError('Destino y repositorio se superponen')
    data=prepare(repo,a.from_dir.expanduser().absolute())
    print('LIOX INSTALLER v0.6', 'APLICAR' if a.apply else 'SIMULACIÓN')
    print('Origen:',repo/'config/hypr')
    print('Destino:',target,'(ya existe)' if target.exists() or target.is_symlink() else '(nuevo)')
    print('Archivos del árbol:',len(data))
    print('Monitores y env.lua: se usarán los borradores revisados')
    if target.exists() or target.is_symlink():
        if target.is_symlink(): print('AVISO: destino es un enlace simbólico; no se sigue ni se modifica.')
        print('BLOQUEADO: destino existente; no se modifica ni se reemplaza.')
        if a.apply:raise ValueError('No se instala encima de una configuración existente')
        return
    if not a.apply:
        print('SIMULACIÓN: sin archivos creados. --apply instala SOLO en una ruta nueva.')
        return
    apply(data,target,storage)
    print('No se crearon enlaces, no se recargó Hyprland, no se instalaron paquetes ni servicios.')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr);sys.exit(1)
