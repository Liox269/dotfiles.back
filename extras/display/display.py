#!/usr/bin/env python3
"""Liox Display v0.2.1: validated game presets; restart shell after confirmed display changes."""
import argparse, contextlib, fcntl, json, os, re, secrets, shutil, subprocess, sys, time
from pathlib import Path

STATE = Path.home()/'.local/state/liox-display'
LUA = Path.home()/'.config/hypr/hyprland.lua'
WAIT = 15
MODE = re.compile(r'^(\d{3,5})x(\d{3,5})@(\d+(?:\.\d+)?)(?:Hz)?$')
OUTPUT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')

def call(args, timeout=5):
    x=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
    if x.returncode or x.stderr.strip().lower().startswith('error') or x.stdout.strip().lower().startswith(('error','warning')):
        raise RuntimeError((x.stderr or x.stdout or 'Comando fallido').strip()[:400])
    return x.stdout.strip()

def monitors():
    payload=json.loads(call(['hyprctl','monitors','-j']))
    if not isinstance(payload,list): raise ValueError('Respuesta inválida de Hyprland')
    return [m for m in payload if isinstance(m,dict) and isinstance(m.get('name'),str)]

def canonical(s):
    match=MODE.fullmatch(s)
    if not match: raise ValueError('Modo no válido')
    w,h,rate=match.groups()
    return f'{int(w)}x{int(h)}@{rate}',int(w),int(h),float(rate)

def options(m):
    out=[]; seen=set()
    for raw in m.get('availableModes') or []:
        try: mode,_,_,_=canonical(raw)
        except (ValueError,TypeError): continue
        if mode not in seen: out.append(mode);seen.add(mode)
    return out

def snapshot(m):
    return {'name':m['name'],'mode':f"{int(m['width'])}x{int(m['height'])}@{float(m['refreshRate']):.3f}",
            'position':f"{int(m['x'])}x{int(m['y'])}", 'scale':float(m['scale']),
            'transform':int(m.get('transform',0))}

def lua_command(s):
    # Every string is prevalidated or derived from hyprctl; json.dumps produces quoted Lua strings.
    return ('hl.monitor({ output = '+json.dumps(s['name'])+', mode = '+json.dumps(s['mode'])+
            ', position = '+json.dumps(s['position'])+', scale = '+str(s['scale'])+
            ', transform = '+str(s['transform'])+' })')

def apply(s): return call(['hyprctl','eval',lua_command(s)])

@contextlib.contextmanager
def locked():
    STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=STATE/'lock'
    with open(lock,'a+') as fd:
        fcntl.flock(fd,fcntl.LOCK_EX)
        yield

def pending_path(): return STATE/'pending.json'

def pending():
    p=pending_path()
    if not p.exists(): return None
    return json.loads(p.read_text())

def save(data):
    p=pending_path(); tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(data));os.chmod(tmp,0o600);os.replace(tmp,p)

def clear(): pending_path().unlink(missing_ok=True)

def rollback(rec):
    apply(rec['before'])

def status():
    ms=monitors(); p=pending()
    return {'ok':True,'displays':[{'name':m['name'],'description':m.get('description',''), 'width':m.get('width'),
            'height':m.get('height'),'refreshRate':m.get('refreshRate'),'scale':m.get('scale'),
            'x':m.get('x'),'y':m.get('y'),'transform':m.get('transform',0),'focused':m.get('focused',False),
            'availableModes':options(m)} for m in ms], 'count':len(ms),
            'pending':bool(p),'secondsLeft':max(0,int(p['deadline']-time.time())) if p else 0,
            'message':'Configuración de pantalla; confirma en 15 segundos para conservar los cambios.'}

def test(name,mode,scale):
    if not OUTPUT.fullmatch(name): raise ValueError('Nombre de pantalla inválido')
    mode,_,_,_=canonical(mode)
    if not (0.75<=scale<=2.5): raise ValueError('Escala fuera de rango 0.75–2.5')
    with locked():
        if pending():raise ValueError('Hay una prueba pendiente. Confirma o restaura primero.')
        ms=monitors();m=next((m for m in ms if m['name']==name),None)
        if not m: raise ValueError('Pantalla desconectada')
        if mode not in options(m): raise ValueError('Modo no anunciado por el monitor')
        if len(ms)<2:raise ValueError('Se requieren dos monitores conectados para probar cambios con seguridad')
        before=snapshot(m); target={**before,'mode':mode,'scale':scale}
        if before['mode']==target['mode'] and before['scale']==scale: pass
        token=secrets.token_hex(16)
        rec={'token':token,'before':before,'target':target,'deadline':time.time()+WAIT}
        save(rec)  # mark before risky switch
        try:apply(target)
        except Exception:
            try:rollback(rec)
            finally:clear()
            raise
        # detached watchdog survives Settings closure; it never changes persistent Lua.
        try:
            subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'watch',token],
                             start_new_session=True,stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except Exception:
            try:rollback(rec)
            finally:clear()
            raise
        return {'ok':True,'message':'Prueba iniciada. Confirma en 15 segundos.', 'secondsLeft':WAIT}

def persist(rec, lua_path=LUA):
    if not lua_path.is_file(): raise ValueError('hyprland.lua no encontrado; se revertirá la prueba')
    text=lua_path.read_text()
    name=re.escape(rec['target']['name'])
    pattern=re.compile(r'(?m)^hl\.monitor\(\{\s*output\s*=\s*"'+name+r'"[^\n]*\}\)\s*$')
    matches=list(pattern.finditer(text))
    if len(matches)!=1: raise ValueError('No hay exactamente una regla de monitor compatible en hyprland.lua')
    # Preserve the existing arrangement and override only mode and scale, maintaining transform/other options.
    line=matches[0].group(0)
    if not re.search(r'\bmode\s*=\s*"[^"]+"',line) or not re.search(r'\bscale\s*=\s*\d+(?:\.\d+)?',line):
        raise ValueError('Regla no editable de forma segura')
    line=re.sub(r'\bmode\s*=\s*"[^"]+"','mode = '+json.dumps(rec['target']['mode']),line,count=1)
    line=re.sub(r'\bscale\s*=\s*\d+(?:\.\d+)?','scale = '+str(rec['target']['scale']),line,count=1)
    new=text[:matches[0].start()]+line+text[matches[0].end():]
    backup=STATE/('hyprland-'+time.strftime('%Y%m%d-%H%M%S')+'.lua.bak')
    shutil.copy2(lua_path,backup)
    temp=lua_path.with_suffix('.lua.liox-tmp')
    try:
        temp.write_text(new)
        os.chmod(temp,lua_path.stat().st_mode)
        os.replace(temp,lua_path)
    finally:temp.unlink(missing_ok=True)
    return str(backup)

def relaunch_shell():
    """Restart only after confirmation; detached from the Caelestia process."""
    shell = shutil.which('caelestia')
    if not shell:
        return False
    # Detached process survives Quickshell exit; delay gives response time to arrive.
    try:
        subprocess.Popen(['/bin/sh', '-c', 'sleep 2; "$1" shell --kill; sleep 1; "$1" shell -d', 'liox-display', shell],
                         start_new_session=True, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False

def confirm():
    with locked():
        rec=pending()
        if not rec: raise ValueError('No existe una prueba pendiente')
        if time.time()>=rec['deadline']:
            rollback(rec);clear();raise ValueError('Tiempo agotado. Se restauró el modo anterior')
        # Persist only after confirmation and before clearing the rollback timer.
        backup=persist(rec)
        clear()
        restarted = relaunch_shell()
        return {'ok':True,'message':('Configuración guardada. Caelestia se reiniciará para adaptar la interfaz.' if restarted else 'Configuración guardada. Reinicia Caelestia manualmente para adaptar la interfaz.'),'backup':backup,'shellRestartScheduled':restarted}

def cancel():
    with locked():
        rec=pending()
        if not rec:return {'ok':True,'message':'No hay cambios pendientes'}
        rollback(rec);clear()
        return {'ok':True,'message':'Se restauró la configuración anterior'}

def watch(token):
    while True:
        with locked():
            rec=pending()
            if not rec or rec['token']!=token:return
            remain=rec['deadline']-time.time()
            if remain<=0:
                try:rollback(rec)
                finally:clear()
                return
        time.sleep(min(max(remain,0.1),0.5))

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['status','test','confirm','cancel','watch'])
    p.add_argument('--name');p.add_argument('--mode');p.add_argument('--scale',type=float)
    p.add_argument('token',nargs='?')
    args=p.parse_args(argv)
    try:
        if args.action=='status': result=status()
        elif args.action=='test': result=test(args.name or '',args.mode or '',args.scale if args.scale is not None else -1)
        elif args.action=='confirm':result=confirm()
        elif args.action=='cancel':result=cancel()
        else:
            if not args.token:raise ValueError('Falta token del watchdog')
            watch(args.token);return 0
        print(json.dumps(result,ensure_ascii=False));return 0
    except Exception as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 1
if __name__=='__main__':sys.exit(main())
