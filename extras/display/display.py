#!/usr/bin/env python3
"""Read-only Hyprland-Lua display inventory. No configuration writes."""
import argparse
import json
import subprocess
import sys


def inventory(payload):
    if not isinstance(payload, list):
        raise ValueError('Hyprland no devolvió una lista de monitores')
    displays = []
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str):
            continue
        modes = item.get('availableModes') or []
        if not isinstance(modes, list):
            modes = []
        modes = [x for x in modes if isinstance(x, str)]
        displays.append({
            'name': item['name'], 'description': str(item.get('description') or ''),
            'width': item.get('width'), 'height': item.get('height'),
            'refreshRate': item.get('refreshRate'), 'scale': item.get('scale'),
            'x': item.get('x'), 'y': item.get('y'),
            'transform': item.get('transform'), 'focused': bool(item.get('focused')),
            'disabled': bool(item.get('disabled')), 'availableModes': modes,
        })
    return {'ok': True, 'displays': displays, 'count': len(displays),
            'readOnly': True, 'message': 'Solo lectura: no cambia monitores ni Hyprland Lua.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status'])
    args = parser.parse_args(argv)
    try:
        output = subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True,
                                text=True, timeout=6, check=True)
        print(json.dumps(inventory(json.loads(output.stdout)), ensure_ascii=False))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 1

if __name__ == '__main__':
    sys.exit(main())
