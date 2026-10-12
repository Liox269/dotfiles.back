#!/usr/bin/env python3
"""Local session tracking for Gaming Center (Steam/Eden/Dolphin/etc.).
Samples the existing status backend, persists SQLite, never writes controller state.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time

INTERVAL = 10
BASE = Path(__file__).resolve().parents[1]
BACKEND = BASE / 'status.py'
DATA_DIR = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state')) / 'liox-gaming-center'
DB = DATA_DIR / 'sessions.sqlite3'


def connect(path: Path = DB):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    db = sqlite3.connect(path, timeout=10)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('''CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY,
      game_key TEXT NOT NULL, title TEXT NOT NULL, platform TEXT NOT NULL,
      started_at INTEGER NOT NULL, last_seen INTEGER NOT NULL,
      ended_at INTEGER, seconds INTEGER NOT NULL DEFAULT 0
    )''')
    db.execute('CREATE INDEX IF NOT EXISTS sessions_game ON sessions(game_key, started_at)')
    db.commit()
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return db


def game_identity(game):
    platform = str(game.get('platform') or 'Steam' if str(game.get('class','')).startswith('steam_app_') else game.get('platform') or 'Other').strip()
    title = str(game.get('title') or '').strip()
    if not title:
        return None
    # A consistent title/platform combines windows of the same game, regardless of PID.
    return (f'{platform.casefold()}::{title.casefold()}', title, platform)


def reconcile(db, games, now, interval=INTERVAL):
    """Credit only real elapsed sample gaps. Long gaps close, not inflate, sessions."""
    unique = {}
    for game in games if isinstance(games, list) else []:
        if not isinstance(game, dict):
            continue
        identity = game_identity(game)
        if identity:
            unique[identity[0]] = identity
    active = {r[1]: r for r in db.execute('SELECT id, game_key, last_seen, seconds FROM sessions WHERE ended_at IS NULL')}
    for key, row in list(active.items()):
        sid, _, last_seen, seconds = row
        if key not in unique or now < last_seen or now - last_seen > interval * 2 + 3:
            db.execute('UPDATE sessions SET ended_at=? WHERE id=?', (last_seen, sid))
            del active[key]
    for key, title, platform in unique.values():
        if key in active:
            sid, _, last_seen, seconds = active[key]
            elapsed = max(0, min(now - last_seen, interval * 2 + 3))
            db.execute('UPDATE sessions SET last_seen=?, seconds=? WHERE id=?', (now, seconds + elapsed, sid))
        else:
            db.execute('INSERT INTO sessions(game_key,title,platform,started_at,last_seen) VALUES(?,?,?,?,?)', (key,title,platform,now,now))
    db.commit()


def close_open(db):
    db.execute('UPDATE sessions SET ended_at=last_seen WHERE ended_at IS NULL')
    db.commit()


def report(db, days=7):
    cutoff = int(time.time()) - days * 86400
    rows = db.execute('''SELECT game_key, MAX(title), MAX(platform), SUM(seconds), COUNT(*), MAX(last_seen)
                         FROM sessions WHERE last_seen>=? GROUP BY game_key ORDER BY SUM(seconds) DESC''', (cutoff,)).fetchall()
    return {'periodDays':days,'games':[{'key':k,'title':t,'platform':p,'seconds':int(s),'sessions':n,'lastPlayed':last} for k,t,p,s,n,last in rows], 'totalSeconds':sum(int(r[3]) for r in rows)}


def backend_games():
    try:
        proc = subprocess.run([sys.executable, str(BACKEND), 'status'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=8, text=True)
        if proc.returncode:
            return None
        data = json.loads(proc.stdout)
        return data.get('games',[]) if data.get('hyprlandAvailable') else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def watch(db, interval):
    running = True
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        while running:
            games = backend_games()
            if games is None:
                # Do not generate false sessions or count time while Hyprland is unavailable.
                close_open(db)
            else:
                reconcile(db, games, int(time.time()), interval)
            time.sleep(interval)
    finally:
        close_open(db)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['watch','report','history'])
    parser.add_argument('--days',type=int,default=7)
    parser.add_argument('--interval',type=int,default=INTERVAL)
    args = parser.parse_args()
    if not 2 <= args.interval <= 60 or not 1 <= args.days <= 365:
        parser.error('invalid range')
    with connect() as db:
        if args.action == 'watch':
            watch(db,args.interval)
        elif args.action == 'report':
            print(json.dumps(report(db,args.days),ensure_ascii=False,indent=2))
        else:
            rows = db.execute('SELECT title,platform,started_at,last_seen,seconds FROM sessions ORDER BY started_at DESC LIMIT 25').fetchall()
            print(json.dumps([{'title':r[0],'platform':r[1],'startedAt':r[2],'lastSeen':r[3],'seconds':r[4]} for r in rows],ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
