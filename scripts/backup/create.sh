#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
BACKUP_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/liox-dotfiles/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_ROOT/$STAMP"
mkdir -p "$DEST"
chmod 700 "$BACKUP_ROOT" "$DEST"
# Explicit allowlist: never archive browser profiles, cookies or full ~/.config.
items=(
  "config:hypr"
  "config:caelestia"
  "config:quickshell/caelestia/scripts/dualsense.py"
  "config:quickshell/caelestia/services/DualSenseMonitor.qml"
  "config:quickshell/caelestia/modules/bar/popouts/DualSensePanel.qml"
  "config:waywallen/config.toml"
  "config:matugen/config.toml"
  "config:fish/config.fish"
  "config:foot/foot.ini"
  "config:kitty/kitty.conf"
)
manifest="$DEST/manifest.txt"
printf 'Liox dotfiles backup %s\n' "$STAMP" > "$manifest"
for item in "${items[@]}"; do
  relative="${item#config:}"
  source="$HOME/.config/$relative"
  if [[ -e "$source" ]]; then
    mkdir -p "$DEST/config/$(dirname "$relative")"
    # Dereference symlinks: restore remains independent of dotfile symlink targets.
    cp -aL -- "$source" "$DEST/config/$relative"
    printf '%s\n' "config/$relative" >> "$manifest"
  fi
done
# Settings separate from QML modules, but may contain controller identifiers: local only.
if [[ -f "$HOME/.config/caelestia/dualsense.json" ]]; then
  mkdir -p "$DEST/config/caelestia"
  cp -aL "$HOME/.config/caelestia/dualsense.json" "$DEST/config/caelestia/dualsense.json"
  printf '%s\n' "config/caelestia/dualsense.json" >> "$manifest"
fi
chmod -R go-rwx "$DEST"
printf 'Respaldo privado creado: %s\n' "$DEST"
printf 'IMPORTANTE: no añadas esta carpeta al repositorio ni la publiques.\n'
