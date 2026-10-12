#!/usr/bin/env python3
"""Liox v0.8 - reversible, isolated visual configuration test installer.
Applies only to explicitly supplied, non-live test root. Never mutates ~/.config.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime

FILES = ('waywallen/config.toml', 'matugen/config.toml', 'caelestia/shell.json')
MAX_BYTES = 2_000_000

def digest(data):
    return hashlib.sha256(data).hexdigest()

def root_check(raw):
    p = raw.expanduser().absolute()
    home = Path.home().absolute()
    forbidden = (home, home / '.config', home / 'dotfiles', home / 'dotfiles-clean', Path('/etc'))
    if any(p == item or p.is_relative_to(item) for item in forbidden):
        raise ValueError('Destino protegido: usa una carpeta de pruebas fuera de HOME y ~/.config')
    if not p.is_relative_to(Path('/tmp')):
        raise ValueError('v0.8 solo permite pruebas bajo /tmp; no instala en el escritorio activo')
    if any(a.is_symlink() for a in (p, *p.parents)):
        raise ValueError('Ruta destino contiene un enlace simbólico')
    return p

def safe_path(root, rel):
    p = root / rel
    if any(a.is_symlink() for a in (p, *p.parents) if a == root or a.is_relative_to(root)):
        raise ValueError('Enlace simbólico no permitido: ' + str(p))
    if p.exists() and not p.is_file():
        raise ValueError('Destino no regular: ' + str(p))
    return p

def load_stage(stage):
    stage = stage.expanduser().absolute()
    if stage.is_symlink() or not stage.is_dir():
        raise ValueError('Carpeta stage inexistente o enlazada')
    report_path = stage / 'compatibility.json'
    if report_path.is_symlink():
        raise ValueError('Informe enlazado no permitido')
    report = json.loads(report_path.read_text())
    if report.get('version') != '0.7' or report.get('live_changes') is not False:
        raise ValueError('Informe de v0.7 incompatible')
    expected = report.get('sha256', {})
    if set(expected) != set(FILES):
        raise ValueError('SHA256 del stage incompleto')
    result = {}
    for rel in FILES:
        path = stage / rel
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(stage.resolve()):
            raise ValueError('Fuente no válida: ' + rel)
        data = path.read_bytes()
        if len(data) > MAX_BYTES or digest(data) != expected[rel]:
            raise ValueError('Archivo alterado desde la preparación: ' + rel)
        result[rel] = data
    import tomllib
    tomllib.loads(result['waywallen/config.toml'].decode())
    tomllib.loads(result['matugen/config.toml'].decode())
    shell = json.loads(result['caelestia/shell.json'])
    if shell != {'background': {'wallpaperEnabled': False}}:
        raise ValueError('Caelestia del stage debe contener solamente wallpaperEnabled=false')
    return result

def desired_content(root, stage_files):
    output = dict(stage_files)
    path = safe_path(root, 'caelestia/shell.json')
    if path.is_file():
        existing = json.loads(path.read_text())
        if not isinstance(existing, dict) or not isinstance(existing.get('background', {}), dict):
            raise ValueError('JSON existente de Caelestia incompatible')
        # Patch only one setting, do not replace other Caelestia preferences.
        existing.setdefault('background', {})['wallpaperEnabled'] = False
        output['caelestia/shell.json'] = (json.dumps(existing, ensure_ascii=False, indent=2) + '\n').encode()
    return output

def install(stage, root, apply):
    root = root_check(root)
    data = load_stage(stage)
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise ValueError('Ruta de prueba no es directorio regular')
    desired = desired_content(root, data)
    changed = []
    for rel in FILES:
        target = safe_path(root, rel)
        old = target.read_bytes() if target.exists() else None
        if old != desired[rel]:
            changed.append((rel, old, desired[rel]))
    print('LIOX v0.8 - ' + ('INSTALACIÓN DE PRUEBA' if apply else 'SIMULACIÓN'))
    print('Destino:', root)
    for rel, old, new in changed:
        print(('REEMPLAZAR' if old is not None else 'CREAR'), rel)
    print('Cambios:', len(changed))
    if not apply:
        print('No se modificó ningún archivo; añade --apply para instalar SOLO en /tmp.')
        return
    if not changed:
        print('Sin cambios; nada que restaurar.')
        return
    backup_base = Path.home() / '.local/state/liox-installer/backups'
    backup_base.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = Path(tempfile.mkdtemp(prefix='visual-v08-', dir=backup_base))
    backup.chmod(0o700)
    manifest = {'version': '0.8', 'root': str(root), 'files': {}}
    for rel, old, new in changed:
        manifest['files'][rel] = {'existed': old is not None, 'before_sha256': digest(old) if old is not None else None, 'after_sha256': digest(new)}
        if old is not None:
            old_path = backup / 'old' / rel
            old_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.write_bytes(old)
            old_path.chmod(0o600)
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (backup / 'manifest.json').chmod(0o600)
    written = []
    try:
        for rel, _, new in changed:
            target = safe_path(root, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            temp_path = target.with_name('.' + target.name + '.liox-' + str(os.getpid()))
            if temp_path.exists() or temp_path.is_symlink():
                raise ValueError('Archivo temporal inesperado: ' + str(temp_path))
            try:
                with temp_path.open('xb') as handle: handle.write(new)
                temp_path.chmod(0o600)
                temp_path.replace(target)
            finally:
                if temp_path.exists(): temp_path.unlink()
            written.append(rel)
    except Exception:
        for rel in reversed(written):
            target = root / rel
            old = manifest['files'][rel]
            if old['existed']:
                shutil.copy2(backup / 'old' / rel, target)
            else:
                target.unlink(missing_ok=True)
        raise
    print('INSTALACIÓN OK (carpeta temporal):', root)
    print('RECIBO:', backup)
    print('Restaurar: python3 install_visual.py --restore "' + str(backup) + '" --target-root "' + str(root) + '"')

def restore(backup, root):
    root = root_check(root)
    backup = backup.expanduser().absolute()
    backup_base = (Path.home() / '.local/state/liox-installer/backups').absolute()
    if not backup.is_relative_to(backup_base) or backup.is_symlink() or not backup.is_dir():
        raise ValueError('Recibo fuera del directorio privado')
    manifest_path = backup / 'manifest.json'
    if manifest_path.is_symlink(): raise ValueError('Recibo enlazado')
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('version') != '0.8' or manifest.get('root') != str(root):
        raise ValueError('Recibo incompatible con este destino')
    files = manifest.get('files', {})
    if not files or set(files) - set(FILES): raise ValueError('Recibo inválido')
    # Verify all hashes before making changes; no partial restore after manual edits.
    for rel, meta in files.items():
        target = safe_path(root, rel)
        if not target.is_file() or digest(target.read_bytes()) != meta['after_sha256']:
            raise ValueError('Archivo cambiado posteriormente, se bloquea restauración: ' + rel)
        if meta['existed']:
            old = backup / 'old' / rel
            if old.is_symlink() or not old.is_file() or digest(old.read_bytes()) != meta['before_sha256']:
                raise ValueError('Respaldo inválido: ' + rel)
    for rel, meta in files.items():
        target = root / rel
        if meta['existed']:
            shutil.copy2(backup / 'old' / rel, target)
        else:
            target.unlink()
    print('RESTAURACIÓN OK:', root)
    print('Los directorios vacíos pueden permanecer; no afectan ~/.config.')

def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--from-dir', type=Path)
    g.add_argument('--restore', type=Path)
    p.add_argument('--target-root', type=Path, required=True)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    if args.restore:
        if args.apply: raise ValueError('--apply no se usa con --restore')
        restore(args.restore, args.target_root)
    else:
        install(args.from_dir, args.target_root, args.apply)

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
