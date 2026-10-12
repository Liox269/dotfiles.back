#!/usr/bin/env python3
"""Hyprland Lua appearance controller v0.2. No wallpaper, Waywallen or Caelestia config writes."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ASSIGNMENT = r'(?m)^(\s*{key}\s*=\s*)(true|false|\d+(?:\.\d+)?)(\s*,[^\n]*)$'
ANIM_BLOCK = re.compile(r'(animations\s*=\s*\{\s*enabled\s*=\s*)(true|false)(\s*,)', re.S)


def extract(source, key):
    matches = list(re.finditer(ASSIGNMENT.format(key=re.escape(key)), source))
    if len(matches) != 1:
        raise ValueError(f'Esperaba una asignación de {key}, encontré {len(matches)}')
    return matches[0].group(2)


def replace_one(source, key, value):
    matches = list(re.finditer(ASSIGNMENT.format(key=re.escape(key)), source))
    if len(matches) != 1:
        raise ValueError(f'Esperaba una asignación de {key}, encontré {len(matches)}')
    m = matches[0]
    return source[:m.start(2)] + str(value) + source[m.end(2):]


def read_animations(source):
    matches = list(ANIM_BLOCK.finditer(source))
    if len(matches) != 1:
        raise ValueError('No se encontró un único animations = { enabled = ... }')
    return matches[0].group(2) == 'true'


def replace_animations(source, enabled):
    matches = list(ANIM_BLOCK.finditer(source))
    if len(matches) != 1:
        raise ValueError('No se encontró un único animations = { enabled = ... }')
    m = matches[0]
    return source[:m.start(2)] + ('true' if enabled else 'false') + source[m.end(2):]


def snapshot(variables, animation_source):
    return {
        'opacity': round(float(extract(variables, 'windowOpacity')) * 100),
        'blur': extract(variables, 'blurEnabled') == 'true',
        'rounding': int(extract(variables, 'windowRounding')),
        'gaps': int(extract(variables, 'windowGapsIn')),
        'gapsOut': int(extract(variables, 'windowGapsOut')),
        'animations': read_animations(animation_source),
    }


def patch_variables(source, v):
    for key, value in (('windowOpacity', f'{v["opacity"] / 100:.2f}'),
                       ('blurEnabled', 'true' if v['blur'] else 'false'),
                       ('windowRounding', v['rounding']),
                       ('windowGapsIn', v['gaps']),
                       ('windowGapsOut', v['gapsOut'])):
        source = replace_one(source, key, value)
    return source


def atomic_write(path, data):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix='.l iox-appearance-'.replace(' ', ''), dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, path.stat().st_mode & 0o777)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def reload_hyprland():
    proc = subprocess.run(['hyprctl', 'reload'], capture_output=True, text=True, timeout=12)
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode or 'error' in output.lower():
        raise RuntimeError(output or 'Fallo al recargar Hyprland')


def transaction(paths, updated, backups, reload):
    before = {name: path.read_bytes() for name, path in paths.items()}
    changed = [name for name in paths if updated[name] != before[name]]
    if not changed:
        return {'changed': False}
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    saved = backups / f'session-{datetime.now():%Y%m%d-%H%M%S-%f}'
    saved.mkdir(mode=0o700)
    for name in paths:
        (saved / f'{name}.lua').write_bytes(before[name])
        (saved / f'{name}.lua').chmod(0o600)
    try:
        for name in changed:
            atomic_write(paths[name], updated[name])
        if reload:
            reload_hyprland()
    except Exception:
        for name in changed:
            atomic_write(paths[name], before[name])
        if reload:
            try: reload_hyprland()
            except Exception: pass
        raise
    return {'changed': True, 'backup': str(saved)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status','apply','restore'])
    parser.add_argument('--opacity', type=int)
    parser.add_argument('--rounding', type=int)
    parser.add_argument('--gaps', type=int)
    parser.add_argument('--gaps-out', type=int)
    parser.add_argument('--blur', choices=['on','off'])
    parser.add_argument('--animations', choices=['on','off'])
    parser.add_argument('--file', type=Path, default=Path.home()/'.config/hypr/variables.lua')
    parser.add_argument('--animations-file', type=Path, default=Path.home()/'.config/hypr/hyprland/animations.lua')
    parser.add_argument('--backup-dir', type=Path, default=Path.home()/'.local/state/liox-appearance/backups')
    parser.add_argument('--no-reload', action='store_true')
    args = parser.parse_args(argv)
    try:
        paths = {'variables': args.file.expanduser().resolve(strict=True),
                 'animations': args.animations_file.expanduser().resolve(strict=True)}
        before = {k: v.read_text() for k,v in paths.items()}
        current = snapshot(before['variables'], before['animations'])
        if args.action == 'status':
            result = {'ok': True, 'values': current}
        elif args.action == 'apply':
            changes = {'opacity': args.opacity, 'rounding': args.rounding, 'gaps': args.gaps,
                       'gapsOut': args.gaps_out, 'blur': None if args.blur is None else args.blur == 'on',
                       'animations': None if args.animations is None else args.animations == 'on'}
            for key, lo, hi in (('opacity',25,100),('rounding',0,40),('gaps',0,40),('gapsOut',0,40)):
                val = changes[key]
                if val is not None and not lo <= val <= hi:
                    raise ValueError(f'{key} debe estar entre {lo} y {hi}')
            values = {key: current[key] if val is None else val for key, val in changes.items()}
            new = {'variables': patch_variables(before['variables'], values).encode(),
                   'animations': replace_animations(before['animations'], values['animations']).encode()}
            change = transaction(paths, new, args.backup_dir.expanduser(), not args.no_reload)
            result = {'ok':True, **change, 'values': values}
        else:
            dirs = sorted((x for x in args.backup_dir.expanduser().glob('session-*') if x.is_dir()),reverse=True)
            if not dirs:
                raise FileNotFoundError('No existen respaldos v0.2 de sesiones')
            saved = dirs[0]
            old = {name: (saved / f'{name}.lua').read_bytes() for name in paths}
            values = snapshot(old['variables'].decode(), old['animations'].decode())
            change = transaction(paths, old, args.backup_dir.expanduser(), not args.no_reload)
            result = {'ok':True, **change, 'values':values, 'restoredFrom':str(saved)}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
