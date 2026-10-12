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


# Identificamos aplicaciones por clase, nunca por coincidencia aislada con el titulo.
EMULATOR_CLASSES = {
    'eden': 'Eden', 'dolphin-emu': 'Dolphin', 'dolphin-emu-qt2': 'Dolphin',
    'ryujinx': 'Ryujinx', 'yuzu': 'Yuzu', 'suyu': 'Suyu', 'sudachi': 'Sudachi',
    'cemu': 'Cemu', 'rpcs3': 'RPCS3', 'pcsx2-qt': 'PCSX2', 'duckstation-qt': 'DuckStation',
    'ppsspp': 'PPSSPP', 'retroarch': 'RetroArch', 'xemu': 'xemu',
}
EDEN_TITLE = re.compile(r"^Eden\s*\|.*?\|\s*([^|]+?)\s*\(64-bit\)(?:\s*\||$)", re.I)
DOLPHIN_TITLE = re.compile(r"^Dolphin\s+[^|]+\|.*?\|\s*([^|]+?)\s*\([A-Z0-9]{6}\)\s*$", re.I)
EMULATOR_MENU = re.compile(r"^(?:Eden|Dolphin(?:\s+\d+[.\w-]*)?|Ryujinx|Yuzu|Suyu|Sudachi|Cemu|RPCS3|PCSX2|DuckStation|PPSSPP|RetroArch|xemu)(?:\s*[|:-]\s*(?:Settings|Configuration|Preferences|Ajustes|Configuraci[oó]n|Log|Logs|Game List|Lista de juegos))?\s*$", re.I)


def parse_emulator_title(cls: str, title: str) -> str | None:
    emulator = EMULATOR_CLASSES.get(cls.casefold())
    if emulator is None or not title.strip():
        return None
    title = title.strip()
    if EMULATOR_MENU.fullmatch(title):
        return None
    if emulator == 'Eden':
        match = EDEN_TITLE.match(title)
        return match.group(1).strip() if match else None
    if emulator == 'Dolphin':
        match = DOLPHIN_TITLE.match(title)
        return match.group(1).strip() if match else None
    # Otros emuladores: solo consideramos un titulo de juego si el emulador
    # publica un nombre distinguible en el titulo. No inventamos el juego.
    for separator in (' | ', ' - ', ' — '):
        parts = [x.strip() for x in title.split(separator) if x.strip()]
        if len(parts) >= 2:
            candidates = [x for x in parts if emulator.casefold() not in x.casefold()]
            if candidates:
                candidate = candidates[-1]
                if len(candidate) > 2 and candidate.casefold() not in ('settings', 'preferences', 'configuration'):
                    return candidate
    return None


def clients_to_games(clients: object) -> list[dict]:
    if not isinstance(clients, list):
        return []
    games = []
    seen_emulators = set()
    for client in clients:
        if not isinstance(client, dict):
            continue
        cls = str(client.get('class') or '').strip()
        title = str(client.get('title') or '').strip()
        tags = client.get('tags') or []
        if isinstance(tags, str):
            tags = [tags]
        is_generic_game = bool(GAME_CLASS.fullmatch(cls)) or (isinstance(tags, list) and any(str(t).casefold() == 'game' for t in tags))
        emulator = EMULATOR_CLASSES.get(cls.casefold())
        emu_game = parse_emulator_title(cls, title) if emulator else None
        # Sin un titulo de juego verificable el frontend no inventa una partida.
        if emulator and not emu_game:
            continue
        if not is_generic_game and not emu_game:
            continue
        pid = client.get('pid') if type(client.get('pid')) is int else None
        if emulator:
            key = (cls.casefold(), pid, emu_game.casefold())
            if key in seen_emulators:
                continue
            seen_emulators.add(key)
        ws = client.get('workspace')
        games.append({
            'title': emu_game or title or cls,
            'class': cls,
            'pid': pid,
            'workspace': str(ws.get('name')) if isinstance(ws, dict) and ws.get('name') is not None else None,
            'focused': bool(client.get('focusHistoryID') == 0),
            'platform': emulator or ('Steam' if cls.lower().startswith('steam_app_') else 'Game'),
            'emulated': bool(emulator),
            'address': str(client.get('address')) if isinstance(client.get('address'), str) else None,
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
