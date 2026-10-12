# Display Manager v0.1.1 — página independiente

Esta actualización mueve Display Manager fuera de **Wallpaper & style** y lo añade como categoría propia **Displays** del menú lateral de Settings de Caelestia 2.5.0, junto a Network.

- Conserva `AdvancedAppearance` dentro de Wallpaper & style.
- Lee resolución, Hz, posición, escala y modos de `hyprctl monitors -j`.
- No cambia físicamente la configuración de ningún monitor (solo lectura).
- Actualiza `PageRegistry.qml` y `PageCompRegistry.qml` en conjunto para mantener el orden de páginas.
- Crea respaldos y admite restauración. Se puede ejecutar de nuevo sin duplicar el menú.
- No modifica Waywallen, Matugen, Hyprland Lua, el fondo de Caelestia, DualSense ni Gaming.

```bash
python3 install.py --dry-run --repo "$HOME/dotfiles-clean"
python3 install.py --install --repo "$HOME/dotfiles-clean"
```

Reinicia Caelestia: `caelestia shell --kill; sleep 1; caelestia shell -d`.

El instalador muestra la ruta de respaldo y el comando exacto de restauración.

**Compatibilidad:** revisa la simulación antes de instalar; el instalador exige la estructura original de Caelestia v2.5.0 y la integración previa de Advanced Appearance.
