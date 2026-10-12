#!/usr/bin/env python3
"""Local Hyprland Lua appearance controller; no wallpaper or Caelestia config writes."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime

FIELDS = {
    'opacity': ('windowOpacity', int, 25, 100),
    'rounding': ('windowRounding', int, 0, 40),
    'gaps': ('windowGapsIn', int, 0, 40),
}
BLUR_KEY = 'blurEnabled'
ASSIGNMENT = r'(?m)^(\s*{key}\s*=\s*)(true|false|\d+(?:\.\d+)?)(\s*,[^\n]*)$'


def extract(source, name):
    matches = re.findall(ASSIGNMENT.format(key=re.escape(name)), source)
    if len(matches) != 1:
        raise ValueError(f'Esperaba una única asignación de {name}; encontré {len(matches)}')
    return matches[0][1]


def snapshot(source):
    return {'opacity': round(float(extract(source, 'windowOpacity')) * 100),
            'blur': extract(source, BLUR_KEY) == 'true',
            'rounding': int(extract(source, 'windowRounding')),
            'gaps': int(extract(source, 'windowGapsIn'))}


def replace_one(source, name, val):
    pattern = ASSIGNMENT.format(key=re.escape(name))
    matches = list(re.finditer(pattern, source))
    if len(matches) != 1:
        raise ValueError(f'Asignación inesperada para {name}')
    match = matches[0]
    return source[:match.start(2)] + val + source[match.end(2):]


def patch(source, values):
    result = source
    result = replace_one(result, 'windowOpacity', f'{values["opacity"] / 100:.2f}')
    result = replace_one(result, BLUR_KEY, 'true' if values['blur'] else 'false')
    result = replace_one(result, 'windowRounding', str(values['rounding']))
    result = replace_one(result, 'windowGapsIn', str(values['gaps']))
    return result


def atomic_write(path, data):
    fd, temp = tempfile.mkstemp(prefix='.appearance-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temp, path.stat().st_mode & 0o777)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def apply(path, backups, values, reload):
    before = path.read_bytes()
    text = before.decode('utf-8')
    updated = patch(text, values).encode('utf-8')
    if updated == before:
        return {'ok': True, 'changed': False, 'values': snapshot(text)}
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    dest = backups / f'variables-{datetime.now():%Y%m%d-%H%M%S-%f}.lua'
    dest.write_bytes(before)
    dest.chmod(0o600)
    atomic_write(path, updated)
    try:
        if reload:
            outcome = subprocess.run(['hyprctl', 'reload'], capture_output=True, text=True, timeout=10)
            if outcome.returncode != 0 or 'error' in outcome.stdout.lower():
                raise RuntimeError((outcome.stdout + outcome.stderr).strip())
    except Exception:
        atomic_write(path, before)
        raise
    return {'ok': True, 'changed': True, 'backup': str(dest), 'values': snapshot(updated.decode())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['status', 'apply', 'restore'])
    ap.add_argument('--opacity', type=int)
    ap.add_argument('--rounding', type=int)
    ap.add_argument('--gaps', type=int)
    ap.add_argument('--blur', choices=['on', 'off'])
    ap.add_argument('--file', type=Path, default=Path.home() / '.config/hypr/variables.lua')
    ap.add_argument('--backup-dir', type=Path, default=Path.home() / '.local/state/liox-appearance/backups')
    ap.add_argument('--no-reload', action='store_true')
    args = ap.parse_args()
    try:
        path = args.file.expanduser().resolve(strict=True)
        text = path.read_text()
        before = snapshot(text)
        if args.action == 'status':
            print(json.dumps({'ok': True, 'values': before}))
            return
        if args.action == 'apply':
            values = {'opacity': args.opacity, 'rounding': args.rounding,
                      'gaps': args.gaps, 'blur': args.blur == 'on'}
            for name, (_, typ, low, high) in FIELDS.items():
                val = values[name]
                if val is None or not low <= val <= high:
                    raise ValueError(f'{name} debe estar entre {low} y {high}')
            if args.blur is None:
                raise ValueError('Falta --blur')
            print(json.dumps(apply(path, args.backup_dir.expanduser(), values, not args.no_reload)))
        elif args.action == 'restore':
            candidates = sorted(args.backup_dir.expanduser().glob('variables-*.lua'))
            if not candidates:
                raise FileNotFoundError('No hay respaldos de cambios anteriores')
            restored = candidates[-1].read_bytes()
            snapshot(restored.decode())
            current = path.read_bytes()
            atomic_write(path, restored)
            try:
                if not args.no_reload:
                    res = subprocess.run(['hyprctl', 'reload'], capture_output=True, text=True, timeout=10)
                    if res.returncode != 0 or 'error' in res.stdout.lower():
                        raise RuntimeError((res.stdout + res.stderr).strip())
            except Exception:
                atomic_write(path, current)
                raise
            print(json.dumps({'ok': True, 'values': snapshot(restored.decode()), 'backup': str(candidates[-1])}))
    except Exception as err:
        print(json.dumps({'ok': False, 'error': str(err)}))
        raise SystemExit(1)

if __name__ == '__main__':
    main()
