#!/usr/bin/env python3
"""Liox v0.9.1: install staged Caelestia files ONLY into a new isolated /tmp tree."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

MODULES = {
    "gaming": [
        ("sources/extras/gaming-center/dashboard/Gaming.qml", "modules/dashboard/Gaming.qml"),
    ],
    "appearance": [
        ("sources/extras/appearance/AdvancedAppearance.qml", "modules/nexus/pages/AdvancedAppearance.qml"),
        ("sources/extras/appearance/appearance.py", "lib/liox-appearance/appearance.py"),
    ],
    "display": [
        ("sources/extras/display/DisplayManager.qml", "modules/nexus/pages/DisplayManager.qml"),
        ("sources/extras/display/display.py", "lib/liox-display/display.py"),
    ],
}
REGISTRY = {
    "gaming": ("modules/dashboard/Content.qml", "Gaming"),
    "appearance": ("modules/nexus/pages/WallpaperAndStyle.qml", "AdvancedAppearance {"),
    "display": ("modules/nexus/PageRegistry.qml", "LIOX_DISPLAY_SETTINGS_V011"),
}
BASELINES = [
    "modules/dashboard/Content.qml",
    "modules/nexus/pages/WallpaperAndStyle.qml",
    "modules/nexus/PageRegistry.qml",
    "modules/nexus/PageCompRegistry.qml",
]

def digest(b): return hashlib.sha256(b).hexdigest()
def in_tmp(p):
    tmp=Path("/tmp").resolve()
    return p != tmp and tmp in p.parents

def planned(stage, target, selected):
    audit=json.loads((stage/"audit.json").read_text())
    if audit.get("errors") or audit.get("live_changes") is not False or not audit.get("stage_only"):
        raise ValueError("Auditoría previa incompleta o con errores")
    result={}
    for rel in BASELINES:
        source=stage/"baseline"/rel
        if not source.is_file() or source.is_symlink():raise ValueError("Falta baseline: "+rel)
        result[rel]=source.read_bytes()
    for mod in selected:
        item=audit.get("modules",{}).get(mod)
        if not item or not item.get("present"):raise ValueError("Módulo no auditado: "+mod)
        src=stage/"sources"/item["source"]
        if not src.is_file() or src.is_symlink() or digest(src.read_bytes())!=item.get("sha256"):
            raise ValueError("Fuente modificada desde auditoría: "+str(src))
        reg,marker=REGISTRY[mod]
        if marker not in result[reg].decode("utf-8"):
            raise ValueError("Integración faltante para "+mod+": "+reg)
        if mod=="display" and "LIOX_DISPLAY_SETTINGS_V011" not in result["modules/nexus/PageCompRegistry.qml"].decode():
            raise ValueError("Display: falta registro del componente")
        for src_rel,dest_rel in MODULES[mod]:
            source=stage/src_rel
            if not source.is_file() or source.is_symlink():raise ValueError("Falta fuente: "+src_rel)
            payload=source.read_bytes()
            if dest_rel.endswith(".qml"):
                content=payload.decode("utf-8")
                if mod=="display":
                    if content.count("__BACKEND__")!=5:raise ValueError("Display: marcador inesperado")
                    content=content.replace("__BACKEND__",str(target/"lib/liox-display/display.py"))
                elif mod=="appearance":
                    if content.count("__CONTROLLER__")!=4:raise ValueError("Appearance: marcador inesperado")
                    content=content.replace("__CONTROLLER__",str(target/"lib/liox-appearance/appearance.py"))
                payload=content.encode()
            result[dest_rel]=payload
    return result

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group()
    g.add_argument("--apply",action="store_true")
    g.add_argument("--restore",type=Path)
    p.add_argument("--stage",type=Path)
    p.add_argument("--target-root",type=Path,required=True)
    p.add_argument("--modules",nargs="+",choices=tuple(MODULES),default=list(MODULES))
    args=p.parse_args()
    target=Path(str(args.target_root.expanduser())).absolute()
    if not in_tmp(target) or target.is_symlink():raise ValueError("El destino debe ser una carpeta no enlazada dentro de /tmp")
    if args.restore:
        receipt=args.restore.expanduser().resolve()
        root=Path.home()/".local/state/liox-installer/backups"
        if root.resolve() not in receipt.parents:raise ValueError("Recibo fuera del directorio permitido")
        data=json.loads((receipt/"receipt.json").read_text())
        if data["target"]!=str(target):raise ValueError("Destino distinto al del recibo")
        if not target.is_dir() or target.is_symlink():raise ValueError("Destino no encontrado")
        for rel,expected in data["files"].items():
            f=target/rel
            if not f.is_file() or f.is_symlink() or digest(f.read_bytes())!=expected:
                raise ValueError("El archivo cambió. No se restaurará automáticamente: "+rel)
        for rel in data["files"]:
            (target/rel).unlink()
        # Only remove empty directories owned by this isolated installation.
        for d in sorted((p for p in target.rglob("*") if p.is_dir()),key=lambda x:len(x.parts),reverse=True):
            if not d.is_symlink():
                try:d.rmdir()
                except OSError:pass
        try:target.rmdir()
        except OSError:pass
        print("RESTAURACIÓN OK: archivos de la prueba eliminados; recibo conservado.")
        return
    if not args.stage:raise ValueError("Se requiere --stage")
    stage=args.stage.expanduser().resolve(strict=True)
    selected=list(dict.fromkeys(args.modules))
    planned_files=planned(stage,target,selected)
    print("LIOX CAELESTIA v0.9.1 — "+("INSTALACIÓN DE PRUEBA" if args.apply else "SIMULACIÓN"))
    print("Módulos:",", ".join(selected))
    print("Archivos preparados:",len(planned_files))
    print("Destino:",target)
    if target.exists():
        raise ValueError("Destino existente; crea uno nuevo dentro de /tmp")
    if not args.apply:
        print("No se creó ningún archivo. Añade --apply para escribir SOLO en el destino temporal.")
        return
    target.mkdir(parents=False,mode=0o700)
    try:
        for rel,payload in planned_files.items():
            f=target/rel
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_bytes(payload)
        root=Path.home()/".local/state/liox-installer/backups"
        root.mkdir(parents=True,exist_ok=True)
        receipt=Path(tempfile.mkdtemp(prefix="caelestia-v091-",dir=root))
        receipt.chmod(0o700)
        (receipt/"receipt.json").write_text(json.dumps({
            "target":str(target),"modules":selected,
            "files":{rel:digest(payload) for rel,payload in planned_files.items()}
        },indent=2))
    except Exception:
        shutil.rmtree(target)
        raise
    print("INSTALACIÓN TEMPORAL OK:",target)
    print("RECIBO:",receipt)
    print(f'RESTAURAR: python3 {Path(__file__).resolve()} --restore "{receipt}" --target-root "{target}"')
    print("NO se instaló ni inició Caelestia. Registro QML validado por marcadores, no por ejecución.")
if __name__=="__main__":
    try:main()
    except Exception as ex:print("ERROR:",ex,file=sys.stderr);sys.exit(1)
