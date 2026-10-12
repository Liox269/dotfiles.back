# Liox Installer v1.0 Preview — guía de instalación (español)

> **Estado: PREVIEW / SOLO PRUEBAS.** Este asistente NO realiza una instalación del escritorio en `~/.config`. Solo diagnostica, genera archivos portátiles y permite probar la instalación y restauración en directorios nuevos bajo `/tmp`. **No ejecutes `install.sh` como sustituto:** es un instalador antiguo, independiente y puede reemplazar configuraciones.

## 1. Preparación de una computadora nueva

Recomendado: CachyOS/Arch x86_64 con Hyprland Lua funcional, Python 3, Git y acceso a un escritorio Wayland. Caelestia Shell + Quickshell, Waywallen, Matugen, Fish y demás dependencias deben instalarse por separado de acuerdo con sus manuales oficiales. **Esta preview no instala paquetes ni servicios.**

```fish
# Clona en una carpeta de trabajo; NO uses ~/dotfiles si ya es tu configuración en vivo.
git clone https://github.com/Liox269/dotfiles.back.git ~/dotfiles-clean
cd ~/dotfiles-clean
python3 tools/liox-installer/wizard.py --repo ~/dotfiles-clean
```

El diagnóstico es **solo lectura**: detecta GPUs, monitores, programas y archivos existentes. La falta de un programa opcional, como Kitty, no implica por sí sola que se haya interrumpido la inspección.

## 2. Preparar borradores portátiles

```fish
python3 tools/liox-installer/wizard.py \
  --repo ~/dotfiles-clean \
  --stage \
  --workspace /tmp/liox-v10-review
```

El workspace debe **no existir** antes de ejecutarlo. Se generan borradores para el árbol Hyprland Lua, Waywallen/Matugen y Caelestia, además del informe privado de hardware. Comprueba las rutas y los monitores antes de usarlos. **No publiques `diagnostic.json` ni recibos de restauración.**

## 3. Probar los tres componentes sin afectar el escritorio

```fish
python3 tools/liox-installer/wizard.py \
  --repo ~/dotfiles-clean \
  --stage --apply-temp \
  --workspace /tmp/liox-v10-install-test
```

En las pruebas del autor, el asistente generó 20 archivos de Hyprland, 3 de configuración visual y 9 archivos relativos a módulos QML. El programa muestra en pantalla los **recibos y comandos específicos de restauración**. Guárdalos antes de eliminar el workspace. No se crean enlaces a `~/.config` ni se activa Hyprland o Caelestia.

## 4. Restauración de pruebas

Cada etapa tiene su propia restauración; **todavía no hay rollback conjunto automático**. Sustituye `<RECIBO_...>` por los recibos mostrados en tu instalación de prueba:

```fish
python3 tools/liox-installer/install_caelestia_stage.py \
  --restore '<RECIBO_CAELESTIA>' \
  --target-root /tmp/liox-v10-install-test/installed-caelestia
python3 tools/liox-installer/install_visual.py \
  --restore '<RECIBO_VISUAL>' \
  --target-root /tmp/liox-v10-install-test/installed-visual
python3 tools/liox-installer/install_hypr_tree.py \
  --restore '<RECIBO_HYPR>' \
  --target /tmp/liox-v10-install-test/installed-hypr
```

Verificación:

```fish
for modulo in installed-caelestia installed-visual installed-hypr
    set ruta /tmp/liox-v10-install-test/$modulo
    if test -d $ruta
        echo "$modulo: "(find $ruta -type f | wc -l)" archivos"
    else
        echo "$modulo: restaurado"
    end
end
```

## 5. Opciones del asistente

`--modules hypr visual caelestia` permite seleccionar etapas. `--caelestia` especifica el árbol QML a auditar y `--repo` la raíz de las fuentes. Consulta `python3 tools/liox-installer/wizard.py --help` para las opciones reales.

## 6. Advertencias de compatibilidad

- Hyprland utiliza **Lua** y algunos dispatchers no son equivalentes a la versión convencional.
- `~/.config/hypr` puede ser un enlace simbólico a una carpeta LIVE; no instalar sobre ese enlace sin un respaldo y estrategia explícita.
- La versión exacta y API de **Caelestia 2.5.0** con Gaming Center, Advanced Appearance y Display Manager **aún no están verificadas en una instalación limpia**.
- Los archivos QML de prueba comprueban marcadores y rutas de backend, **no ejecutan ni validan visualmente QML**.
- **Waywallen** debe seguir dibujando el fondo. `background.wallpaperEnabled` en Caelestia debe permanecer `false`.
- Los archivos de Waywallen no deben transferir identificadores de pantallas ni fondos de otra computadora.
- Matugen necesita validación adicional de rutas de plantillas y sincronización real de colores.
- No ejecutes el asistente con `sudo`; prueba primero una sesión y usuario separados antes de distribuirlo como instalación estable.

## 7. Estado del proyecto

| Etapa | Estado comprobado |
| --- | --- |
| Diagnóstico y portabilidad | En CachyOS del autor |
| Instalación Hyprland | En directorio nuevo bajo `/tmp`; restauración comprobada |
| Configuración visual | En directorio nuevo bajo `/tmp`; restauración comprobada |
| Módulos personalizados QML | Copiados en directorio nuevo bajo `/tmp`; marcadores de backend sustituidos y restauración comprobada |
| Instalación real sobre `~/.config` | **No disponible** |
| Compatibilidad con Caelestia limpio | **Pendiente** |
| Reversión automática global | **Pendiente** |

Antes de publicar una versión estable: validar dependencias/versiones, confirmar integración QML sobre una copia completa limpia, completar la instalación reversible y probar en una segunda PC.
