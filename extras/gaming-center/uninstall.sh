#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
dest="${XDG_BIN_HOME:-$HOME/.local/bin}/liox-gaming-center"
if [[ -L "$dest" && "$(readlink -- "$dest")" == "$root/launch.sh" ]]; then
    rm -- "$dest"
    printf 'Desinstalado enlace %s\n' "$dest"
else
    printf 'No se borró nada: el enlace no pertenece a este módulo.\n'
fi
