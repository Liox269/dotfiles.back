#!/usr/bin/env bash
set -Eeuo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"
echo '--- Rutas sospechosas entre los archivos versionados ---'
git ls-files | grep -Ei '(^|/)(Cookies(-journal)?|Local Storage|Session Storage|IndexedDB|\.env([^/]*)?|[^/]*\.(pem|key|token))($|/)' || true
echo '--- Datos de aplicaciones que NO deben versionarse ---'
git ls-files | grep -Ei '^config/(tidal-hifi|TIDAL Hi-Fi)/' || true
echo '--- Resumen de modificaciones ---'
git status --short | head -30
echo 'Nota: es un análisis de nombres, NO una auditoría completa de secretos.'
