#!/usr/bin/env python3
"""Portable conservative dotfile installer; Python 3 stdlib only.
Run FROM the copied repo or supply --repo.
"""
import argparse
import datetime as dt
import json
import hashlib
import os
from pathlib import Path
import shutil
import sys
import uuid

MODULES = {
    'fish': [('config/fish/config.fish', '.config/fish/config.fish'), ('config/fish/functions', '.config/fish/functions')],
    'terminals': [('config/foot', '.config/foot'), ('config/kitty', '.config/kitty')],
    'utilities': [('config/btop', '.config/btop'), ('config/fastfetch', '.config/fastfetch'), ('config/fuzzel', '.config/fuzzel'), ('config/cava', '.config/cava')],
    'visual': [('config/Kvantum', '.config/Kvantum'), ('config/starship/starship.toml', '.config/starship.toml')],
}
# Exclude personal secrets and host-dependent files; no arbitrary shell commands.
EXCLUDES = {'fish_variables', 'config.fish.bak.20260910'}

def validate_source(source, repo):
    """Allow only links resolving to regular files inside the same repo."""
    if source.is_symlink():
        resolved = source.resolve(strict=True)
        if not resolved.is_relative_to(repo) or not resolved.is_file():
            raise ValueError('Unsafe source symlink: '+str(source))
    elif not source.is_file():
        raise ValueError('Source is not a regular file: '+str(source))


def plan(repo, home, modules):
    entries=[]
    for module in modules:
        for src, dst in MODULES[module]:
            source=repo/src
            if not source.exists():
                continue
            if source.is_symlink() or source.is_file():
                validate_source(source, repo)
                entries.append((source, home/dst))
            else:
                for s in sorted(source.rglob('*')):
                    if s.name in EXCLUDES:
                        continue
                    if s.is_symlink() or s.is_file():
                        validate_source(s, repo)
                        entries.append((s, home/dst/s.relative_to(source)))
    for s,t in entries:
        if not t.resolve(strict=False).is_relative_to(home):
            raise ValueError('Destination escapes home: '+str(t))
    return entries

def file_equal(s,t):
    return t.is_file() and not t.is_symlink() and s.read_bytes()==t.read_bytes()

def run():
    p=argparse.ArgumentParser(description='Liox portable installer (default: dry-run)')
    p.add_argument('--repo',type=Path,default=Path.cwd())
    p.add_argument('--home',type=Path,default=Path.home(),help=argparse.SUPPRESS)
    p.add_argument('--modules',nargs='+',choices=sorted(MODULES),default=['fish','terminals','utilities','visual'])
    group=p.add_mutually_exclusive_group()
    group.add_argument('--apply',action='store_true')
    group.add_argument('--rollback',type=Path)
    args=p.parse_args()
    repo=args.repo.expanduser().resolve()
    home=args.home.expanduser().resolve()
    state=home/'.local/state/liox-installer'
    if args.rollback:
        folder=args.rollback.expanduser().resolve()
        base=(state/'backups').resolve()
        if not folder.is_relative_to(base) or folder==base:
            raise ValueError('Backup path must be inside '+str(base))
        manifest=json.loads((folder/'manifest.json').read_text())
        for row in reversed(manifest['files']):
            target=home/row['target']
            saved=folder/'before'/row['target']
            installed=row['installed_sha256']
            current=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() and not target.is_symlink() else None
            if current!=installed:
                print('SKIP changed after install:',target)
                continue
            if row['existed']:
                target.unlink()
                shutil.copy2(saved,target)
            else:
                target.unlink()
            print('RESTORED:',target)
        return
    if not (repo/'config').is_dir():
        raise ValueError('Repository must contain config/; use --repo')
    entries=plan(repo,home,args.modules)
    changes=[(s,t) for s,t in entries if not file_equal(s,t)]
    print('Repository:',repo)
    print('Modules:',', '.join(args.modules))
    print('Changes:',len(changes),'of',len(entries),'files')
    for s,t in changes:print(('REPLACE' if t.exists() or t.is_symlink() else 'CREATE '), str(t.relative_to(home)))
    if not args.apply:
        print('DRY RUN: nothing changed. Use --apply to install.')
        return
    if not changes:
        print('Already synchronized.')
        return
    backup=state/'backups'/(dt.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
    backup.mkdir(parents=True,mode=0o700)
    manifest={'repo':str(repo),'modules':args.modules,'files':[]}
    # Before any changes, validate paths and save existing file content.
    for s,t in changes:
        if t.is_symlink() or (t.exists() and not t.is_file()):
            raise ValueError('Refusing non-regular destination: '+str(t))
        parent=t.parent
        while parent!=home:
            if parent.is_symlink():
                raise ValueError('Symlink parent refused: '+str(parent))
            parent=parent.parent
        rel=str(t.relative_to(home))
        existed=t.exists()
        if existed:
            dest=backup/'before'/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(t,dest)
        manifest['files'].append({'target':rel,'existed':existed,'installed_sha256':hashlib.sha256(s.read_bytes()).hexdigest()})
    (backup/'manifest.json').write_text(json.dumps(manifest,indent=2))
    os.chmod(backup/'manifest.json',0o600)
    # Retain prior file when destination's directory path conflicts.
    for s,t in changes:
        t.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(s,t)
    print('INSTALLED. Backup:',backup)
    print('Restore with: python3 installer.py --home "'+str(home)+'" --rollback "'+str(backup)+'"')
    print('No services enabled; no Hyprland or Caelestia files modified.')

if __name__=='__main__':
    try:run()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr)
        sys.exit(1)
