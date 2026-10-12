#!/usr/bin/env python3
"""Read-only Gaming Center backend for Hyprland/Caelestia 2.5.0.
No root, no lighting writes, no Steam/GameMode control. JSON stdout only.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time

GAME_CLASS = re.compile(r"^(steam_app_\d+|steam_app_default|gamescope)$", re.I)
GAME_TAG = re.compile(r"(?:^|[,\s])game(?:$|[,\s])", re.I)


def run(*args: str, timeout: float = 2.0) -> str | None:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return proc.stdout if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def clients_to_games(clients: object) -> list[dict]:
    if not isinstance(clients, list):
        return []
    games = []
    for client in clients:
        if not isinstance(client, dict):
            continue
        cls = str(client.get('class') or '')
        tags = client.get('tags') or []
        if isinstance(tags, str):
            tags = [tags]
        if not GAME_CLASS.search(cls) and not (isinstance(tags, list) and any(str(t).lower() == 'game' for t in tags)):
            continue
        games.append({
            'title': str(client.get('title') or cls),
            'class': cls,
            'pid': client.get('pid') if isinstance(client.get('pid'), int) else None,
            'workspace': client.get('workspace', {}).get('name') if isinstance(client.get('workspace'), dict) else None,
            'focused': bool(client.get('focusHistoryID') == 0),
        })
    return games


def safe_json(data: str | None) -> object:
    if data is None:
        return None
    try:
        return json.loads(data)
    except (ValueError, TypeError):
        return None


def proc_names() -> set[str]:
    names = set()
    try:
        for p in Path('/proc').iterdir():
            if not p.name.isdecimal():
                continue
            try:
                names.add((p / 'comm').read_text().strip())
            except (OSError, UnicodeError):
                continue
    except OSError:
        pass
    return names


def dualsense_status() -> dict:
    helper = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')/'quickshell/caelestia/scripts/dualsense.py'
    if not helper.is_file():
        return {'available': False, 'devices': [], 'reason': 'helper_missing'}
    data = safe_json(run('python3', str(helper), 'scan', timeout=4))
    devices = data.get('devices', []) if isinstance(data, dict) else []
    return {'available': True, 'devices': devices if isinstance(devices, list) else []}


def snapshot() -> dict:
    clients_raw = run('hyprctl', '-j', 'clients')
    clients = safe_json(clients_raw)
    processes = proc_names()
    return {
        'version': 1,
        'hyprlandAvailable': isinstance(clients, list),
        'games': clients_to_games(clients),
        'steamRunning': any(p in processes for p in ('steam', 'steamwebhelper')),
        'gamescopeRunning': 'gamescope' in processes,
        'dualsense': dualsense_status(),
        'timestamp': int(time.time()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Gaming Center read-only status')
    parser.add_argument('action', choices=['status', 'watch'])
    parser.add_argument('--interval', type=float, default=5)
    args = parser.parse_args()
    if args.action == 'status':
        print(json.dumps(snapshot(), ensure_ascii=False))
        return
    if not 2 <= args.interval <= 60:
        parser.error('--interval debe estar entre 2 y 60 segundos')
    try:
        while True:
            print(json.dumps(snapshot(), ensure_ascii=False), flush=True)
            time.sleep(args.interval)
    except (KeyboardInterrupt, BrokenPipeError):
        return


if __name__ == '__main__':
    main()
