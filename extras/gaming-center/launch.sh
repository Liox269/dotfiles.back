#!/usr/bin/env bash
set -euo pipefail
root=$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")
if ! command -v qs >/dev/null 2>&1; then
    printf 'ERROR: falta qs (Quickshell)\n' >&2
    exit 1
fi
if [[ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    printf 'AVISO: no hay una sesión Hyprland detectada.\n' >&2
fi
# Instancia Quickshell independiente; NO iniciar otro `caelestia shell -d`.
exec qs -p "$root/qml/shell.qml"
