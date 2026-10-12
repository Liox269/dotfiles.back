#!/usr/bin/env python3
"""Read-only hardware and compatibility assessment for Liox dotfiles.
Only Python stdlib; never changes the system or installs packages.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

TOOLS = ('git','python3','fish','hyprctl','hyprland','caelestia','quickshell','qs','waywallen','matugen','jq','rsync','foot','kitty','starship','fuzzel')

def run_command(argv, timeout=3):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None

def os_release(path=Path('/etc/os-release')):
    values={}
    try:
        for line in path.read_text(errors='replace').splitlines():
            if '=' not in line or line.startswith('#'): continue
            k,v=line.split('=',1)
            values[k]=v.strip().strip('"')
    except OSError:
        pass
    return values

def parse_gpu(output):
    if not output:
        return {'vendors':[], 'devices':[], 'source':'unavailable'}
    lines=[line.strip() for line in output.splitlines() if re.search(r'VGA compatible controller|3D controller|Display controller',line,re.I)]
    vendors=[]
    for name, pattern in [('NVIDIA',r'NVIDIA'),('AMD',r'AMD|Advanced Micro Devices|ATI'),('Intel',r'Intel')]:
        if any(re.search(pattern,line,re.I) for line in lines): vendors.append(name)
    return {'vendors':vendors,'devices':lines,'source':'lspci'}

def parse_monitors(raw):
    if raw is None: return {'available':False,'outputs':[],'reason':'Hyprland IPC not available in this session'}
    try: obj=json.loads(raw)
    except (TypeError,ValueError): return {'available':False,'outputs':[],'reason':'Invalid hyprctl JSON'}
    if not isinstance(obj,list): return {'available':False,'outputs':[],'reason':'Unexpected hyprctl JSON'}
    outputs=[]
    for item in obj:
        if not isinstance(item,dict): continue
        outputs.append({k:item.get(k) for k in ('name','description','width','height','refreshRate','scale','x','y','transform')})
    return {'available':True,'count':len(outputs),'outputs':outputs}

def assess(report):
    messages=[]
    distro=report['system']['os_id']
    if distro not in ('cachyos','arch') and 'arch' not in report['system']['os_like'].split():
        messages.append('Not detected as Arch/CachyOS; package instructions need manual review.')
    if not report['tools']['hyprctl']:
        messages.append('Hyprland CLI not found; full desktop installation is not yet supported.')
    if not report['monitors']['available']:
        messages.append('Monitor configuration unavailable; do not copy hardcoded DP-2 or HDMI-A-1 outputs.')
    if not report['tools']['caelestia']:
        messages.append('Caelestia executable not found; custom QML modules require separate installation.')
    messages.append('Existing v0.1 installer only handles fish, terminals, utilities and visuals; no full desktop setup.')
    messages.append('Do not copy private credentials or machine-specific files. No changes were made.')
    return messages

def collect():
    osdata=os_release()
    tools={name:bool(shutil.which(name)) for name in TOOLS}
    report={
        'schema_version':1,
        'system':{'os_id':osdata.get('ID','unknown').lower(),'os_name':osdata.get('PRETTY_NAME','unknown'),
                  'os_like':osdata.get('ID_LIKE','').lower(),'kernel':platform.release(),'architecture':platform.machine(),
                  'session_type':os.getenv('XDG_SESSION_TYPE','unknown'), 'desktop':os.getenv('XDG_CURRENT_DESKTOP','unknown')},
        'tools':tools,
        'gpu':parse_gpu(run_command(['lspci','-nn'])),
        'monitors':parse_monitors(run_command(['hyprctl','monitors','-j'])),
        'config_presence':{
            'hyprland_lua':(Path.home()/'.config/hypr/hyprland.lua').is_file(),
            'caelestia_qml':(Path.home()/'.config/quickshell/caelestia').is_dir(),
            'waywallen':(Path.home()/'.config/waywallen').is_dir(),
            'matugen':(Path.home()/'.config/matugen').is_dir(),
        }
    }
    report['warnings']=assess(report)
    return report

def main():
    p=argparse.ArgumentParser(description='Read-only diagnostic of hardware and Liox dotfiles prerequisites')
    p.add_argument('--json',action='store_true',help='Print machine-readable JSON')
    p.add_argument('--output',type=Path,help='Save report as JSON; choose a private directory')
    args=p.parse_args()
    report=collect()
    data=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if args.output:
        out=args.output.expanduser().absolute()
        if out.is_symlink(): raise ValueError('Refusing to overwrite symlink')
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('w') as fp:
            os.chmod(out,0o600)
            fp.write(data)
        print('Saved private report:',out, file=sys.stderr)
    if args.json:
        print(data,end='')
    else:
        s=report['system']
        print('LIOX COMPATIBILITY CHECK (read-only)')
        print('OS:',s['os_name'],'|',s['architecture'],'|',s['session_type'])
        print('GPU:',', '.join(report['gpu']['vendors']) or 'unknown')
        for device in report['gpu']['devices']: print('  ',device)
        m=report['monitors']
        print('Monitors:',str(m['count']) if m['available'] else 'not available')
        for out in m['outputs']:
            print('  {name}: {width}x{height} @ {refreshRate} Hz, scale {scale}'.format(**out))
        print('Installed commands:',', '.join(k for k,v in report['tools'].items() if v) or '(none)')
        print('Missing commands:',', '.join(k for k,v in report['tools'].items() if not v) or '(none)')
        print('Config presence:',', '.join(k+(' yes' if v else ' no') for k,v in report['config_presence'].items()))
        print('Cautions:')
        for warning in report['warnings']: print(' -',warning)
        print('No changes made. For JSON: python3 diagnose.py --json')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(1)
