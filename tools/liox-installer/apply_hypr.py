#!/usr/bin/env python3
"""Liox installer v0.5: install/revert two reviewed portable Lua files.
No compositor reload, no package or service changes. Uses a private backup.
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

PATHS = ('hyprland.lua', 'hyprland/env.lua')
MODULES = ('variables.lua', 'hyprland/general.lua', 'hyprland/input.lua', 'hyprland/misc.lua',
           'hyprland/animations.lua', 'hyprland/decoration.lua', 'hyprland/group.lua',
           'hyprland/execs.lua', 'hyprland/rules.lua', 'hyprland/gestures.lua',
           'hyprland/keybinds.lua', 'hyprland/env.lua')

def digest(data): return hashlib.sha256(data).hexdigest()

def regular_file(path): return path.is_file() and not path.is_symlink()

def under_safe(base, rel):
    p = base / rel
    if base.is_symlink() or not base.is_dir(): raise ValueError('Directorio base inválido: '+str(base))
    t = base
    for comp in Path(rel).parts[:-1]:
        t = t / comp
        if t.is_symlink(): raise ValueError('Directorio enlazado no permitido: '+str(t))
        if t.exists() and not t.is_dir(): raise ValueError('Padre no es directorio: '+str(t))
    if p.is_symlink(): raise ValueError('Archivo destino enlazado no permitido: '+str(p))
    return p

def plan(source, target):
    if source.is_symlink() or not source.is_dir(): raise ValueError('Origen inválido')
    # Refuse sources that overlap target, so backups cannot copy the live config itself.
    if source.resolve().is_relative_to(target.resolve()) or target.resolve().is_relative_to(source.resolve()):
        raise ValueError('Origen y destino no pueden contenerse mutuamente')
    data = {}
    for rel in PATHS:
        f = under_safe(source, rel)
        if not regular_file(f): raise ValueError('Falta archivo regular generado: '+str(f))
        content=f.read_bytes()
        if not content or b'\x00' in content: raise ValueError('Fuente vacía o binaria')
        data[rel] = content
        under_safe(target,rel)
    # Never deploy monitor definitions without the remaining Lua dependencies.
    for rel in MODULES:
        if rel == 'hyprland/env.lua': continue
        if not regular_file(under_safe(target,rel)):
            raise ValueError('Falta dependencia Lua en destino: '+str(target/rel)+'; v0.5 requiere Hyprland preinstalado')
    for rel in PATHS:
        if re.search(rb'/home/[\w.-]+/', data[rel]):
            raise ValueError('Fuente contiene rutas de usuario absolutas: '+rel)
    return data

def snapshot(target, data, storage):
    storage.mkdir(mode=0o700,parents=True,exist_ok=True)
    if storage.is_symlink(): raise ValueError('Almacenamiento enlazado no permitido')
    if (storage.stat().st_mode & 0o077): raise ValueError('Directorio de backups debe ser privado (0700): '+str(storage))
    folder=storage / ('hypr-v05-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    folder.mkdir(mode=0o700)
    manifest={'version': '0.5', 'target':str(target), 'files':{}}
    try:
        for rel,content in data.items():
            dest=under_safe(target,rel)
            old=dest.read_bytes() if regular_file(dest) else None
            if dest.exists() and old is None: raise ValueError('Destino especial no permitido: '+str(dest))
            manifest['files'][rel]={'existed':old is not None,'new_hash':digest(content)}
            if old is not None:
                b=folder/'old'/rel
                b.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                b.write_bytes(old)
                b.chmod(0o600)
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (folder/'manifest.json').chmod(0o600)
        return folder
    except BaseException:
        shutil.rmtree(folder)
        raise

def atomic_write(dest,data):
    dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=dest.with_name(dest.name+'.liox-tmp-'+str(os.getpid()))
    try:
        with tmp.open('xb') as f:
            os.fchmod(f.fileno(),0o600)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,dest)
    finally:
        if tmp.exists():tmp.unlink()

def restore(folder,target,storage,force=False):
    folder=folder.expanduser().absolute()
    if folder.parent!=storage.absolute() or folder.is_symlink():
        raise ValueError('Backup fuera del almacén de v0.5')
    manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('version')!='0.5' or manifest.get('target')!=str(target) or set(manifest.get('files',{}))!=set(PATHS):
        raise ValueError('Manifiesto incompatible')
    changes=[]
    for rel in PATHS:
        dest=under_safe(target,rel)
        current=dest.read_bytes() if regular_file(dest) else None
        if dest.exists() and current is None: raise ValueError('Destino cambiado a tipo no regular')
        info=manifest['files'][rel]
        if not force and digest(current or b'') != info['new_hash']:
            raise ValueError('Se detectaron cambios posteriores en '+rel+'; no se sobrescribe. Revisa manualmente o --force-restore')
        old=folder/'old'/rel
        if info['existed']:
            if not regular_file(old):raise ValueError('Backup incompleto: '+rel)
            changes.append((dest,old.read_bytes()))
        else:changes.append((dest,None))
    if not force:
        for dest,_ in changes:print('RESTAURAR:',dest)
    for dest,old in changes:
        if old is None: dest.unlink(missing_ok=True)
        else:atomic_write(dest,old)
    print('Restauración OK; no se recargó Hyprland.')

def main(argv=None):
    p=argparse.ArgumentParser(description='v0.5: instala o restaura dos archivos Lua; no recarga Hyprland')
    p.add_argument('--from-dir',type=Path,help='Borradores preparados por portable_setup.py v0.4')
    p.add_argument('--target',type=Path,default=Path.home()/'.config/hypr')
    p.add_argument('--store',type=Path,default=Path.home()/'.local/state/liox-installer/backups')
    p.add_argument('--apply',action='store_true',help='Requiere confirmación manual previa de la simulación')
    p.add_argument('--restore',type=Path)
    p.add_argument('--force-restore',action='store_true',help='Sobrescribir cambios posteriores, solo para recuperación consciente')
    a=p.parse_args(argv)
    requested_target=a.target.expanduser().absolute()
    linked_target=requested_target.is_symlink()
    target=requested_target.resolve(strict=True)
    storage=a.store.expanduser().absolute()
    if not target.is_dir():raise ValueError('Directorio Hyprland inexistente: '+str(requested_target))
    if linked_target:
        print('AVISO: '+str(requested_target)+' es un enlace a '+str(target))
        print('Solo se inspeccionará el destino real; no se escribirá a través del enlace.')
        if a.apply or a.restore:
            raise ValueError('Instalar/restaurar sobre un directorio enlazado está bloqueado. No borres el enlace.')
    if storage.is_relative_to(target):raise ValueError('Backups no deben estar en configuración Hyprland')
    if a.restore:
        if a.apply or a.from_dir:raise ValueError('--restore es modo separado')
        restore(a.restore,target,storage,a.force_restore)
        return
    if not a.from_dir:raise ValueError('Especifica --from-dir para instalar')
    if a.force_restore:raise ValueError('--force-restore requiere --restore')
    data=plan(a.from_dir.expanduser().absolute(),target)
    diffs=[rel for rel in PATHS if not regular_file(target/rel) or (target/rel).read_bytes()!=data[rel]]
    print('LIOX v0.5', 'APLICAR' if a.apply else 'SIMULACIÓN')
    for rel in PATHS:print(('CAMBIAR' if rel in diffs else 'IGUAL'),target/rel)
    if not diffs:print('Sin cambios.');return
    if not a.apply:print('SIMULACIÓN: ningún archivo modificado; usa --apply solo tras revisar.');return
    folder=snapshot(target,data,storage)
    try:
        for rel in diffs:atomic_write(under_safe(target,rel),data[rel])
    except BaseException:
        # Roll back changed files on failure, without assuming any compositor reload.
        restore(folder,target,storage,force=True)
        raise
    print('Archivos instalados. Backup:',folder)
    print('Restaurar: python3 apply_hypr.py --restore "'+str(folder)+'"')
    print('No se ha reiniciado/recargado Hyprland, ni instalado un escritorio completo.')

if __name__=='__main__':
    try:main()
    except Exception as exc: print('ERROR:',exc,file=sys.stderr);sys.exit(1)
