#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
usage() { printf 'Uso: bash %s RUTA_BACKUP [--apply]\nSin --apply solo muestra archivos para restaurar.\n' "$0"; }
[[ $# -ge 1 && $# -le 2 ]] || { usage; exit 2; }
BACKUP="$(realpath -e -- "$1")"
[[ -d "$BACKUP/config" && -f "$BACKUP/manifest.txt" ]] || { echo 'Respaldo inválido' >&2; exit 1; }
[[ $# -eq 1 || "$2" == --apply ]] || { usage; exit 2; }
# Avoid pathological config trees. Only restore allowlisted paths.
allowed=(hypr caelestia quickshell/caelestia/scripts/dualsense.py quickshell/caelestia/services/DualSenseMonitor.qml quickshell/caelestia/modules/bar/popouts/DualSensePanel.qml waywallen/config.toml matugen/config.toml fish/config.fish foot/foot.ini kitty/kitty.conf)
for rel in "${allowed[@]}"; do
  src="$BACKUP/config/$rel"
  [[ -e "$src" ]] || continue
  dst="$HOME/.config/$rel"
  if [[ $# -eq 1 ]]; then
    printf 'Restauraría: %s\n' "$dst"
    continue
  fi
  mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" || -L "$dst" ]]; then
    moved="${dst}.before-liox-restore-$(date +%Y%m%d-%H%M%S)"
    mv -- "$dst" "$moved"
    printf 'Preexistente guardado: %s\n' "$moved"
  fi
  cp -a -- "$src" "$dst"
  printf 'Restaurado: %s\n' "$dst"
done
if [[ $# -eq 1 ]]; then
  echo 'Simulación: no se modificó ningún archivo. Añade --apply para restaurar.'
fi
