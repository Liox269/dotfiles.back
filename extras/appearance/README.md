# Advanced Appearance v0.1

Añade controles de apariencia de Hyprland al final de **Settings → Wallpaper & style** en Caelestia Shell 2.5.0, manteniendo el resto de la pantalla.

- Opacidad de ventanas, blur activado/desactivado, redondeo y espacios interiores.
- Botón **Valores elegidos**: 45 %, blur desactivado, 6 px y 17 px. No aplica cambios hasta pulsar **Aplicar**.
- **Restaurar** devuelve el respaldo previo más reciente de `variables.lua`.
- Las animaciones **permanecen activadas**, sin modificarlas. Este primer parche no ofrece todavía un interruptor de animaciones.
- **No cambia** `background.wallpaperEnabled` (debe seguir `false`), Waywallen, Matugen, Gaming Center ni DualSense.
- 45 % **opacidad** = 55 % transparencia de las ventanas de Hyprland. La transparencia de los paneles de Caelestia se controla por separado mediante su interruptor existente.

## Instalar (Fish)

```fish
cd ~/dotfiles-clean
unzip -o ~/Descargas/advanced-appearance-v01.zip -d /tmp
python3 /tmp/advanced-appearance-v01/install.py --dry-run
python3 /tmp/advanced-appearance-v01/install.py
caelestia shell --kill
sleep 1
caelestia shell -d
```

Si el instalador no reconoce el QML o Lua, aborta sin alterar archivos. Al instalar no cambia la apariencia de Hyprland hasta pulsar Aplicar en la UI.

**Antes de pulsar Aplicar**, conserva abierto un terminal: una ventana con 45 % de opacidad puede resultar difícil de leer. Si se produce un error de `hyprctl reload`, el controlador restaura automáticamente la versión previa del archivo.

Para consultar los valores actuales:

```fish
python3 ~/.local/lib/liox-appearance/appearance.py status
```

Para restaurar el último conjunto de valores del controlador:

```fish
python3 ~/.local/lib/liox-appearance/appearance.py restore
```

Para desinstalar el **panel**, usa la ruta de respaldo que imprime `install.py`:

```fish
python3 /tmp/advanced-appearance-v01/install.py --restore /ruta/que/imprimio/el/instalador
```

Y reinicia Caelestia manualmente. La desinstalación del panel no altera tus valores de Hyprland; usa `appearance.py restore` si también quieres recuperar los valores anteriores.

La carpeta `extras/appearance` se copia al repositorio `~/dotfiles-clean` para poder confirmar los archivos en Git.
