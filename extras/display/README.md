# Liox Display Manager v0.2.1 — CS2 y actualización de Caelestia

Actualiza v0.2; conserva la categoría lateral Displays y la prueba de seguridad de 15 segundos.

## Perfiles del LG GN65R (DP-2)

- **Nativo · 120 Hz:** 1920×1080@119.98 — recomendado para el escritorio.
- **CS2 4:3 · 120 Hz:** 1024×768@119.99 — modo que anuncia el LG; imagen estirada o con barras depende del escalado en CS2 y la GPU.
- **CS2 FPS · 120 Hz:** 800×600@119.97 — imagen menos nítida, no implica mayor FPS en todos los equipos.
- 1280×960 **NO** aparece en la lista de modos disponibles del monitor; por seguridad no se fuerza.

**Recomendado para jugar:** mantener el escritorio nativo a 1920×1080 y modificar la resolución desde las opciones de vídeo de CS2, preferiblemente a pantalla completa si tu configuración lo admite. Los presets del Display Manager cambian la resolución **del escritorio**, no las opciones de CS2. El panel no controla automáticamente el escalado stretched/black bars.

## Caelestia y los cambios de resolución

Hyprland puede cambiar la resolución sin que todos los elementos de Quickshell se redistribuyan correctamente en caliente. Por ello, al pulsar **Mantener cambios** y terminar de escribir el respaldo de `hyprland.lua`, el backend programa un **reinicio diferido de Caelestia** (`caelestia shell --kill; caelestia shell -d`). Esto ocurre **solo después de confirmar**, no durante la prueba de 15 segundos; la cuenta atrás y el watchdog independientes se conservan. La interfaz desaparece unos segundos y reaparece ajustada a la nueva geometría. Si el ejecutable `caelestia` no está en PATH, se indicará que debe reiniciarse manualmente.

**Importante:** el reinicio reconstruye la geometría del shell; no garantiza que todas las ventanas de otras aplicaciones reordenen su tamaño. Cerrar Settings antes de confirmar simplemente provoca la reversión automática. Si Hyprland o el watchdog se bloquean, la recuperación automática no está garantizada.

## Instalar desde Fish

```fish
cd ~/dotfiles-clean
unzip -o ~/Descargas/liox-display-v021.zip -d /tmp
python3 /tmp/liox-display-v021/install.py --dry-run --repo ~/dotfiles-clean
python3 /tmp/liox-display-v021/install.py --install --repo ~/dotfiles-clean
caelestia shell --kill
sleep 1
caelestia shell -d
```

Luego Settings → Displays. Selecciona un perfil del LG; el modo se prepara en el ComboBox, **no se aplica hasta pulsar Probar 15 segundos**. Pulsa Mantener cambios para guardarlo y reiniciar Caelestia.

Recuperación de una prueba pendiente:

```fish
python3 ~/.local/lib/liox-display/display.py cancel
```

El instalador respaldará solo los archivos que modifica; no toca Gaming Center, Advanced Appearance, DualSense, Waywallen ni `background.wallpaperEnabled`. No cambia la resolución durante la instalación.
