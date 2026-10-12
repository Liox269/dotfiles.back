#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
dest="${XDG_BIN_HOME:-$HOME/.local/bin}/liox-gaming-center"
mkdir -p -- "$(dirname -- "$dest")"
if [[ -e "$dest" && ! -L "$dest" ]]; then
    printf 'ERROR: %s existe y no es un enlace simbólico. No se sobrescribe.\n' "$dest" >&2
    exit 1
fi
if [[ -L "$dest" ]]; then
    actual=$(readlink -- "$dest")
    if [[ "$actual" != "$root/launch.sh" ]]; then
        printf 'ERROR: %s apunta a otro destino (%s). No se sobrescribe.\n' "$dest" "$actual" >&2
        exit 1
    fi
fi
ln -sfn -- "$root/launch.sh" "$dest"
printf 'INSTALADO: %s -> %s\n' "$dest" "$root/launch.sh"
printf 'Ejecuta: liox-gaming-center\n'
