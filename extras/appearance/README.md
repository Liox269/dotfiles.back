# Advanced Appearance — instalación reproducible v0.2.2

Incluye el controlador funcional v0.2, la vista con desplazamiento v0.2.1 y un instalador capaz de reconocer si WallpaperAndStyle.qml ya contiene AdvancedAppearance. No modifica el fondo de Caelestia, Waywallen, Matugen, DualSense ni Gaming Center.

Desde `~/dotfiles-clean` (Fish):

```fish
unzip -o ~/Descargas/appearance-repro-v022.zip -d /tmp
python3 /tmp/appearance-repro-v022/install.py --dry-run --repo ~/dotfiles-clean
python3 /tmp/appearance-repro-v022/install.py --install --repo ~/dotfiles-clean
caelestia shell --kill
sleep 1
caelestia shell -d
```

El instalador actualiza tanto `extras/appearance` del repositorio como la configuración activa. Antes de escribir crea un respaldo y emite el comando exacto de restauración. Aplicar los cambios en el panel es una acción separada: durante la instalación NO se modifica Hyprland Lua. Puedes verificar con `python3 ~/.local/lib/liox-appearance/appearance.py status` y `jq '.background.wallpaperEnabled' ~/.config/caelestia/shell.json` (esperado `false`).

Los sliders afectan a la opacidad de ventanas, blur, esquinas, espacios interiores/exteriores y animaciones; el script NO modifica las curvas de las animaciones. La plantilla de QML usa la ruta personal que el instalador resuelve desde `$HOME`.
