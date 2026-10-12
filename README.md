# Liox Dotfiles

Configuración personal de **CachyOS + Hyprland (Lua) + Caelestia Shell**, con fondos administrados por **Waywallen**, colores generados con **Matugen**, integración **DualSense**, una pestaña **Gaming** y controles **Advanced Appearance** dentro de los ajustes.

> **Estado del proyecto:** configuración personalizada, probada en el escritorio del autor. No es un instalador universal ni una distribución de Linux. Algunas funciones necesitan adaptar rutas, versiones y servicios al equipo de destino.

## Índice

1. [Antes de empezar](#antes-de-empezar)
2. [Instalación desde cero](#instalación-desde-cero)
3. [Estructura del repositorio](#estructura-del-repositorio)
4. [Hyprland Lua y atajos](#hyprland-lua-y-atajos)
5. [Fondos de pantalla y colores dinámicos](#fondos-de-pantalla-y-colores-dinámicos)
6. [Caelestia Shell](#caelestia-shell)
7. [Control Center del DualSense](#control-center-del-dualsense)
8. [Gaming Center](#gaming-center)
9. [Advanced Appearance](#advanced-appearance)
10. [Respaldos y restauración](#respaldos-y-restauración)
11. [Seguridad y Git](#seguridad-y-git)
12. [Problemas habituales](#problemas-habituales)
13. [Historial de mejoras](#historial-de-mejoras)

## Antes de empezar

### Componentes principales

| Componente | Función |
| --- | --- |
| CachyOS | Distribución Linux basada en Arch |
| Hyprland con configuración Lua | Gestión de ventanas, workspaces y animaciones |
| Caelestia Shell 2.5.0 | Barra, Dashboard, paneles y ajustes |
| Quickshell | Motor QML de Caelestia |
| Waywallen | **Dibuja el fondo** de pantalla |
| Matugen | Genera colores a partir del wallpaper |
| Fish + Starship | Shell y prompt |
| Foot / Kitty | Terminales |
| Fuzzel | Lanzador de aplicaciones |
| Python 3 | Servicios y scripts de integración |
| `jq`, `git`, `unzip` | Utilidades de diagnóstico e instalación |

**Compatibilidad:** los módulos añadidos se desarrollaron para la versión de Caelestia y la configuración Lua utilizadas en este equipo. Las actualizaciones de Caelestia o Hyprland pueden cambiar las API QML y los dispatchers.

### Requisitos y recomendaciones

- Una instalación de CachyOS con entorno gráfico y una sesión funcional de Hyprland.
- Acceso a `sudo` para las dependencias del sistema, **no** para ejecutar scripts de configuración personal.
- Copia de seguridad de `~/.config` antes de reemplazar cualquier dotfile.
- Verificar los paquetes disponibles antes de instalarlos: algunos componentes pueden venir de AUR o repositorios particulares.

Sitios oficiales: [CachyOS](https://cachyos.org/), [Hyprland](https://hypr.land/), [Caelestia](https://github.com/caelestia-dots/shell), [Quickshell](https://quickshell.outfoxxed.me/).

## Instalación desde cero

### 1. Instalar CachyOS

Descarga la ISO desde el sitio oficial, crea un USB de instalación y sigue el instalador. Btrfs es opcional. **Tener Btrfs no garantiza que Snapper esté configurado correctamente**; verifica los subvolúmenes antes de depender de las instantáneas.

### 2. Instalar herramientas básicas

En un sistema Arch/CachyOS:

```bash
sudo pacman -Syu
sudo pacman -S --needed git fish python jq unzip rsync \
  hyprland foot kitty thunar firefox fuzzel starship
```

Instala **Caelestia Shell, Quickshell, Waywallen, Matugen y las herramientas del controlador** siguiendo las instrucciones compatibles con la versión de tu sistema. No se asume que todos estos paquetes estén presentes en los mismos repositorios.

### 3. Obtener el repositorio

```bash
git clone https://github.com/Liox269/dotfiles.back.git ~/dotfiles
cd ~/dotfiles
```

> **Atención a las versiones:** la rama de desarrollo local contiene cambios todavía no publicados en `main`. Si descargas el repositorio público antes de su sincronización, puede que Gaming Center y Advanced Appearance aún no aparezcan. Comprueba `git branch -a` y la documentación de la revisión descargada.

### 4. Revisar el instalador antes de usarlo

Si la revisión incluye `install.sh`:

```bash
sed -n '1,240p' install.sh
```

Comprueba qué archivos enlaza o sobrescribe, crea tu propio respaldo y solo entonces ejecuta el instalador si es compatible:

```bash
bash install.sh
```

**No se garantiza** que un instalador genérico configure automáticamente Caelestia, sus modificaciones QML, Hyprland Lua, la sincronización de Waywallen ni los módulos opcionales. Las siguientes secciones documentan esas piezas por separado.

### 5. Preparar la sesión

Comprueba que estás usando los archivos de configuración esperados:

```bash
ls -l ~/.config/hypr/
ls -l ~/.config/quickshell/caelestia/
command -v caelestia
command -v hyprctl
```

Si trabajas con Fish, los comandos marcados `bash` puedes ejecutarlos desde Fish; los scripts de Python se ejecutan con `python3`.

## Estructura del repositorio

Estas son las rutas relevantes del proyecto; algunas pueden no existir todavía en versiones públicas anteriores:

```text
config/
  hypr/                              # Configuración de Hyprland en Lua
  caelestia/                         # Ajustes de Caelestia
  waywallen/                         # Configuración del wallpaper
  matugen/                            # Generación de paletas
  fish/                               # Shell Fish
  foot/                               # Terminal Foot
  kitty/                              # Terminal Kitty
extras/
  gaming-center/
    dashboard/                        # Gaming.qml, integración y gestión
    stats/                            # Seguimiento opcional de sesiones
  appearance/
    AdvancedAppearance.qml           # Panel avanzado de Settings
    appearance.py                    # Controlador de Hyprland Lua
    install.py                       # Instalador reversible
    README.md                        # Documentación específica
scripts/
  backup/create.sh                   # Respaldo local de rutas permitidas
  backup/restore.sh                  # Restauración de respaldo
  security/audit.sh                  # Comprobación básica de rutas sensibles
tests/
  test_gaming_stats.py               # Pruebas del seguimiento de juegos
```

**No guardes en Git** el directorio de estado local, respaldos, cookies, sesiones, bases de datos privadas ni credenciales.

## Hyprland Lua y atajos

Esta configuración usa **archivos `.lua`**, no una configuración clásica basada únicamente en `hyprland.conf`.

Archivos importantes:

- `config/hypr/variables.lua`: parámetros visuales y atajos.
- `config/hypr/hyprland/general.lua`: separaciones, bordes y otros valores generales.
- `config/hypr/hyprland/decoration.lua`: redondeo, blur y sombras.
- `config/hypr/hyprland/animations.lua`: animaciones y curvas.
- `config/hypr/hyprland/rules.lua`: reglas de ventanas y capas.
- `config/hypr/hyprland/keybinds.lua`: asignaciones de teclas.

### Atajos habituales

| Atajo | Acción |
| --- | --- |
| `SUPER + T` | Terminal Foot |
| `SUPER + W` | Firefox |
| `SUPER + E` | Thunar |
| `SUPER + C` | Editor |
| `SUPER + Q` | Cerrar ventana |
| `SUPER + F` | Pantalla completa |
| `SUPER + ALT + Space` | Alternar ventana flotante |
| `SUPER + L` | Bloquear |
| `SUPER + S` | Workspace especial |
| `SUPER + V` | Portapapeles |
| `SUPER + Period` | Selector de emojis |
| `Print` | Captura de pantalla |
| `SUPER + ALT + F` | Pantalla completa con bordes, según la configuración |

La tecla `SUPER` suele ser la tecla Windows. Consulta `variables.lua` y `keybinds.lua` para la lista completa: son la referencia definitiva.

### Particularidad importante del dispatcher Lua

El comando tradicional de Hyprland:

```bash
hyprctl dispatch focuswindow "address:0x..."
```

**No funciona** en esta variante Lua. Para enfocar la dirección real de una ventana se comprobó:

```fish
set addr (hyprctl clients -j | jq -r '.[] | select(.class == "dolphin-emu" and (.title | contains("Super Mario Strikers"))) | .address' | head -n 1)
if test -n "$addr"
    hyprctl dispatch "hl.dsp.focus({ window = 'address:$addr' })"
end
```

La dirección de una ventana cambia al cerrarla o volverla a abrir; nunca fijes una dirección hexadecimal antigua en el código.

## Fondos de pantalla y colores dinámicos

**Waywallen dibuja el fondo de pantalla. Caelestia NO debe hacerlo simultáneamente.**

```bash
jq '.background.wallpaperEnabled' ~/.config/caelestia/shell.json
```

En esta configuración, el resultado esperado es:

```text
false
```

El flujo de personalización es:

1. Waywallen cambia el wallpaper.
2. El mecanismo local de sincronización detecta el cambio.
3. Matugen genera la paleta de colores desde la imagen.
4. Caelestia recibe/aplica su esquema dinámico.
5. Los componentes QML que usan correctamente la paleta reflejan los cambios.

El script de sincronización utilizado en el entorno de desarrollo se denomina `sync-waywallen-colors.sh`. **Verifica su ruta e integración con Hyprland antes de asumir que se inicia automáticamente**. Evita ejecutar dos copias del sincronizador.

No habilites `Display wallpaper` de Caelestia si quieres conservar Waywallen como único compositor del fondo.

### Diagnóstico de colores

```bash
jq '.background.wallpaperEnabled' ~/.config/caelestia/shell.json
cat ~/.config/waywallen/config.toml
cat ~/.config/matugen/config.toml
```

Si el fondo cambia pero alguna tarjeta no adopta los nuevos colores, puede tratarse de colores fijos en el QML de **ese módulo**, no de un fallo de Waywallen.

## Caelestia Shell

Caelestia aporta Dashboard, controles rápidos, barra y configuración. El proyecto incluye personalizaciones de QML, por lo que **una actualización de Caelestia puede sobrescribir archivos modificados**.

Reinicio manual de Caelestia desde Fish:

```fish
caelestia shell --kill
sleep 1
caelestia shell -d
```

Si falla al arrancar, revisa las líneas `ERROR` del terminal y restaura el último respaldo del QML; no reinstales todo el escritorio a ciegas.

### Dashboard

Se conserva la organización original del Dashboard: **Dashboard, Media, Performance y Gaming**. Gaming es una pestaña adicional, no una segunda aplicación Quickshell ni un icono extra de la barra.

## Control Center del DualSense

El mando DualSense tiene una integración local para mostrar conexión, batería y estado, además de gestionar opciones RGB cuando la conexión y los permisos lo permiten.

Piezas relevantes de la instalación:

```text
~/.config/quickshell/caelestia/scripts/dualsense.py
~/.config/quickshell/caelestia/services/DualSenseMonitor.qml
~/.config/quickshell/caelestia/modules/bar/popouts/DualSensePanel.qml
~/.config/caelestia/dualsense.json
```

Se ha comprobado funcionamiento por Bluetooth con batería visible en Caelestia. Algunas funciones RGB pueden competir con **Steam Input**: no ejecutes dos controladores de iluminación simultáneamente. La detección de Gaming Center y el seguimiento de estadísticas **no cambian la iluminación del mando**.

Los identificadores del mando, direcciones Bluetooth y estados locales **no deben publicarse como datos personales ni incrustarse como valores universales**.

## Gaming Center

La pestaña **Gaming** del Dashboard permite:

- Detectar ventanas reconocidas de Steam y títulos emulados de Eden y Dolphin.
- Presentar varios juegos al mismo tiempo en una lista desplazable.
- Mostrar el estado de Steam, Gamescope y DualSense cuando los datos están disponibles.
- Enfocar la ventana del juego seleccionado mediante su **dirección actual de Hyprland Lua**, evitando confundir el menú de Dolphin con la partida.

Casos verificados durante el desarrollo: títulos de Steam como *Cuphead* y *Stellar Blade*; Eden con *Super Smash Bros. Ultimate*; Dolphin con *Super Mario Strikers*.

### Versión visual estable

Tras experimentar con varias variantes de colores dinámicos que provocaron problemas de contraste, se recuperó como **versión visual estable** el `Gaming.qml` del commit:

```text
71ba271 — fix: focus games using Hyprland Lua dispatcher
```

**No se recomienda instalar** las variantes de tema v0.6.4–v0.6.7 sin una revisión adicional del QML. En especial, no sustituyas automáticamente los colores por `m3onSurface` si el fondo real del componente permanece oscuro.

### Reinstalar solo Gaming

En una instalación que **ya tenga** registrada la cuarta pestaña dentro de `Content.qml`, consulta primero las acciones disponibles:

```bash
python3 extras/gaming-center/dashboard/manage.py --help
```

En las versiones compatibles del gestor:

```bash
python3 extras/gaming-center/dashboard/manage.py --dry-run
python3 extras/gaming-center/dashboard/manage.py --install
```

Esto gestiona `Gaming.qml`, **no crea por sí mismo la pestaña en una instalación nueva**. Antes de usarlo desde cero, comprueba que `Content.qml` incluya la integración de Gaming; consulta el instalador/guía de `extras/gaming-center/dashboard/` para esa revisión.

Después reinicia Caelestia.

### Estadísticas opcionales de juego

También existe un registrador local de sesiones que usa Python y SQLite. **No requiere modificar el Dashboard**, y su visualización no está integrada en la pestaña Gaming.

```bash
python3 -m unittest discover -s tests -p 'test_gaming_stats.py' -v
python3 extras/gaming-center/stats/manage.py dry-run
python3 extras/gaming-center/stats/manage.py install
systemctl --user status liox-gaming-stats.service --no-pager
```

Consulta los datos:

```bash
python3 extras/gaming-center/stats/tracker.py report --days 7
python3 extras/gaming-center/stats/tracker.py history
```

Para ver las opciones de desinstalación:

```bash
python3 extras/gaming-center/stats/manage.py --help
```

La información de sesiones se guarda **fuera del repositorio** bajo `~/.local/state/liox-gaming-center/`. Si no deseas mantener el proceso, puedes detenerlo:

```bash
systemctl --user disable --now liox-gaming-stats.service
```

## Advanced Appearance

Integrado dentro de **Settings → Wallpaper & style** de Caelestia. Amplía las opciones nativas, sin reemplazar los ajustes de wallpaper, colores o tema oscuro.

Controles implementados:

| Control | Parámetro Lua |
| --- | --- |
| Opacidad de ventanas | `windowOpacity` |
| Blur | `blurEnabled` |
| Redondeo de esquinas | `windowRounding` |
| Espaciado interior | `windowGapsIn` |
| Espaciado exterior | `windowGapsOut` |
| Animaciones | `animations.enabled` |

Los controles visuales son `SliderRow` y `ToggleRow` originales de Caelestia. El contenido tiene desplazamiento vertical para acceder a todos los botones, incluso en ventanas pequeñas.

El panel dispone de:

- **Valores elegidos**: carga una propuesta sin aplicarla.
- **Aplicar**: escribe los cambios en la configuración de Hyprland, con respaldo.
- **Restaurar**: revierte los ajustes utilizando el respaldo compatible.

### Valores sugeridos originalmente

| Parámetro | Valor |
| --- | --- |
| Opacidad | 45 % |
| Blur | Desactivado |
| Esquinas | 6 px |
| Espaciado interior | 17 px |
| Espaciado exterior | 10 px |
| Animaciones | Activadas |

**Estos no son necesariamente los valores actualmente aplicados.** El panel lee la configuración real, y solo escribe al pulsar **Aplicar**.

> Nota: una opacidad del 45 % puede dificultar la lectura de algunas aplicaciones. Puedes elegir otro porcentaje sin modificar los demás parámetros.

### Instalación reproducible (v0.2.2)

Desde la raíz del repositorio **que contiene los archivos actuales**:

```bash
python3 extras/appearance/install.py --help
python3 extras/appearance/install.py --dry-run --repo "$PWD"
python3 extras/appearance/install.py --install --repo "$PWD"
```

El instalador:

- Reconoce si `WallpaperAndStyle.qml` ya tiene integrada la sección y evita duplicarla.
- Copia el QML y el controlador Python compatibles.
- Crea un respaldo e imprime el comando exacto para restaurar.
- **No aplica cambios de Hyprland durante la instalación**.
- **No cambia** `background.wallpaperEnabled`, Waywallen, Matugen, Gaming Center ni DualSense.

Reinicia Caelestia después de instalar.

Comprobar los valores actuales:

```bash
python3 ~/.local/lib/liox-appearance/appearance.py status
```

Ejemplo de respuesta (ilustrativo, **no es un estado garantizado**):

```json
{
  "ok": true,
  "values": {
    "opacity": 100,
    "blur": true,
    "rounding": 6,
    "gaps": 3,
    "gapsOut": 10,
    "animations": true
  }
}
```

Consulta `extras/appearance/README.md` para detalles del instalador y la restauración. Conserva siempre el comando de respaldo que imprime cada ejecución.

## Respaldos y restauración

### Respaldo privado con lista permitida

```bash
bash scripts/backup/create.sh
```

El script guarda **solo las rutas configuradas**, no todo `~/.config`, en:

```text
~/.local/state/liox-dotfiles/backups/FECHA/
```

Entre esas rutas están configuraciones Hyprland, Caelestia, Waywallen, Matugen, Fish y archivos clave del DualSense. El respaldo es **privado**, no debe subirse al repositorio ni compartirse sin inspección.

### Restauración

```bash
# Mostrar qué se restauraría (sin cambiar nada)
bash scripts/backup/restore.sh "$HOME/.local/state/liox-dotfiles/backups/FECHA"

# Restaurar después de revisar la simulación
bash scripts/backup/restore.sh "$HOME/.local/state/liox-dotfiles/backups/FECHA" --apply
```

Sustituye `FECHA` por la carpeta de respaldo real. La segunda orden puede sobrescribir archivos actuales; revisa primero la simulación. Cada instalador de Gaming o Appearance también genera sus **propios respaldos**, con instrucciones específicas para deshacer únicamente su modificación.

### Recomendación

Antes de una actualización importante:

1. Crea un respaldo privado.
2. Comprueba `git status`.
3. Ejecuta la simulación del instalador.
4. Instala y verifica que Caelestia se inicie.
5. Prueba las funciones modificadas.
6. Haz el commit solo cuando todo funcione.

Los snapshots de Snapper son una protección **adicional**, no sustituyen estas copias; en particular, una ruta `.snapshots` no configurada como subvolumen Btrfs puede impedir su funcionamiento.

## Seguridad y Git

### Archivos que nunca deben publicarse

- Cookies y sesiones de aplicaciones.
- Directorios `Local Storage`, `Session Storage` e `IndexedDB`.
- Tokens, contraseñas, claves privadas o ficheros `.env` con secretos.
- Historial personal de juegos, bases de datos, logs y respaldos privados.
- Perfiles completos del navegador o de servicios de streaming.

Se retiraron las rutas de sesión de TIDAL del proyecto de respaldo. **Eliminar archivos del árbol actual no equivale a eliminar secretos del historial remoto**. La revisión de seguridad debe considerar el historial entero y, si hubo tokens expuestos, invalidarlos desde el servicio correspondiente.

### Auditoría básica

```bash
bash scripts/security/audit.sh
```

Este script busca rutas sospechosas y datos de aplicaciones; **no es un escáner exhaustivo de secretos**. Si no muestra resultados, eso no demuestra que todos los commits estén libres de credenciales.

Comprobaciones adicionales:

```bash
git status --short
git log -5 --oneline
git remote -v
git ls-files
```

Si has saneado el historial de manera local, **no uses `git push --force` sin revisar primero el remoto, las ramas, la copia de seguridad y el alcance de la reescritura**. Conserva una copia privada del repositorio original hasta finalizar la migración.

### Commits destacados

| Commit | Cambio |
| --- | --- |
| `71ba271` | Corrección del enfoque de ventanas para Hyprland Lua |
| `36abb56` | Lista desplazable de varios juegos |
| `69d4a4b` | Advanced Appearance y seguimiento de sesiones |
| `b9485ea` | Instalación reproducible de Advanced Appearance |

## Problemas habituales

**Caelestia muestra `Type ... unavailable`**

Un componente QML puede tener un import faltante o usar una API que cambió de versión. Revisa el error completo y restaura el último QML funcional. No edites varias piezas a la vez.

**Gaming Center tiene textos negros o invisibles**

Se detectaron problemas de contraste en varias versiones experimentales. Restaura el `Gaming.qml` estable de `71ba271` y evita instalar parches de tema no validados.

**El botón de enfocar juego no responde**

Esta configuración usa dispatchers Lua. La corrección funcional usa `hl.dsp.focus({ window = 'address:...' })`, con una dirección obtenida de `hyprctl clients -j`.

**El fondo cambia pero no cambian los colores**

Comprueba el sincronizador de Waywallen/Matugen y que Caelestia utilice el esquema dinámico. Si Performance cambia correctamente pero Gaming no, revisa los colores propios de Gaming.

**El wallpaper de Caelestia tapa Waywallen**

Comprueba que `jq '.background.wallpaperEnabled' ~/.config/caelestia/shell.json` devuelva `false`.

**Advanced Appearance no aplica los valores**

Comprueba que el QML y el controlador Python pertenezcan a la misma versión. El panel envía opacidad como porcentaje (`45`), no como decimal (`0.45`).

**Los botones no se ven**

Utiliza el desplazamiento vertical del panel v0.2.1 o posterior. No es necesario ampliar los ajustes ni reducir las fuentes.

**La auditoría no devuelve coincidencias**

Es una señal positiva sobre rutas, no una garantía de ausencia de secretos.

## Historial de mejoras

- **Base:** CachyOS, Hyprland Lua, Caelestia, Fish, Waywallen y Matugen.
- **Sincronización visual:** wallpaper gestionado por Waywallen y paletas dinámicas.
- **DualSense:** estado Bluetooth, batería y controles RGB dentro de Caelestia.
- **Gaming Center:** cuarta pestaña del Dashboard, detección Steam/Eden/Dolphin, múltiples juegos y foco corregido para Lua.
- **Gaming Stats:** seguimiento opcional y local de sesiones, con pruebas automatizadas.
- **Advanced Appearance v0.1–v0.1.1:** controles iniciales y corrección de porcentajes.
- **Advanced Appearance v0.2:** espaciados separados e interruptor de animaciones.
- **Advanced Appearance v0.2.1:** scroll vertical para llegar a los botones.
- **Advanced Appearance v0.2.2:** instalación y restauración reproducibles.
- **Seguridad:** scripts de auditoría y respaldos, exclusión de sesiones privadas y trabajo de saneamiento del historial.

---

**Proyecto personal en evolución.** Prioriza respaldos, compatibilidad y pruebas antes de aplicar cambios a la configuración activa.
