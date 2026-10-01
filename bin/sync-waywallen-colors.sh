#!/usr/bin/env bash

CONFIG_FILE="$HOME/.config/waywallen/config.toml"
DB_FILE="$HOME/.local/share/waywallen/waywallen-v2.db"
LAST_ID_FILE="/tmp/caelestia_last_wallpaper_id"

sync_colors() {
    [ ! -f "$CONFIG_FILE" ] && return
    
    CURRENT_ID=$(grep "last_wallpaper" "$CONFIG_FILE" | head -n 1 | sed 's/.*= "\(.*\)"/\1/')
    [ -z "$CURRENT_ID" ] && return

    if [ -f "$LAST_ID_FILE" ] && [ "$(cat "$LAST_ID_FILE")" == "$CURRENT_ID" ]; then
        return
    fi

    echo "=> ¡Cambio de fondo detectado! ID: $CURRENT_ID"
    
    WALLPAPER_PATH=$(sqlite3 "$DB_FILE" "SELECT COALESCE(preview_path, path) FROM item WHERE id = '$CURRENT_ID'")
    [ -z "$WALLPAPER_PATH" ] && return
    
    if [[ "$WALLPAPER_PATH" != /* ]]; then
        FILENAME=$(basename "$WALLPAPER_PATH")
        for base in "$HOME/.local/share/Steam" "$HOME/.steam/steam"; do
            if [ -f "$base/$WALLPAPER_PATH" ]; then
                WALLPAPER_PATH="$base/$WALLPAPER_PATH"
                break
            fi
        done
        if [[ "$WALLPAPER_PATH" != /* ]]; then
            WALLPAPER_PATH=$(find "$HOME/.local/share/waywallen" -name "$FILENAME" | head -n 1)
        fi
    fi
    
    [ -z "$WALLPAPER_PATH" ] || [ ! -f "$WALLPAPER_PATH" ] && return
    
    SAFE_WALLPAPER="/tmp/caelestia_color_${CURRENT_ID}.png"
    
    if command -v ffmpeg >/dev/null 2>&1; then
        ffmpeg -y -i "$WALLPAPER_PATH" -vframes 1 "$SAFE_WALLPAPER" >/dev/null 2>&1
    elif command -v magick >/dev/null 2>&1; then
        magick "$WALLPAPER_PATH[0]" "$SAFE_WALLPAPER" >/dev/null 2>&1
    else
        cp "$WALLPAPER_PATH" "$SAFE_WALLPAPER"
    fi
    
    echo "=> Generando colores con Matugen/Caelestia..."
    caelestia scheme set -n dynamic > /dev/null 2>&1
    caelestia wallpaper -f "$SAFE_WALLPAPER" > /dev/null 2>&1

# --- NUEVO: Refrescar temas GTK / Aplicaciones externas ---
    # Si Caelestia tiene un comando nativo para refrescar GTK o templates, va aquí. 
    # O forzamos a matugen si genera templates directos:
    matugen image "$SAFE_WALLPAPER" > /dev/null 2>&1

# EL TRUCO ESTRELLA: Tocar el archivo de configuración .lua para forzar el Hot Reload de Caelestia
    echo "=> Aplicando recarga en caliente a la UI (.lua)..."
    sleep 0.5
    [ -f "$HOME/.config/caelestia/shell.lua" ] && touch "$HOME/.config/caelestia/shell.lua"
    [ -f "$HOME/.local/state/caelestia/scheme.lua" ] && touch "$HOME/.local/state/caelestia/scheme.lua"    
    echo "$CURRENT_ID" > "$LAST_ID_FILE"
    echo "=> ¡Listo! Interfaz actualizada."
}

if [[ "$1" == "--daemon" ]]; then
    while true; do
        sync_colors
        sleep 1
    done
else
    sync_colors
fi
