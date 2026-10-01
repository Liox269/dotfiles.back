# 🌌 Dotfiles

¡Bienvenido! Este repositorio es la "receta" de mi computadora. Aquí guardo todas las configuraciones que hacen que mi sistema se vea increíble y funcione rápido. 

Si eres nuevo en Linux o quieres probar mi configuración, **este manual es para ti**. He diseñado todo para que sea fácil de instalar, incluso si nunca has tocado una terminal.

---

## 💿 Paso 0: El Sistema Operativo

Para que mis configuraciones funcionen exactamente como en las capturas, necesitas instalar la distribución de Linux que yo uso.

### 🚀 ¿Qué es CachyOS?
**CachyOS** es una versión de Arch Linux optimizada para el máximo rendimiento. Es increíblemente rápida y viene con herramientas que facilitan mucho la vida al usuario.

### 📥 Cómo obtenerlo:
1. **Descarga la ISO**: Ve a la página oficial [cachyos.org](https://cachyos.org/download).
2. **Crea un USB Booteable**: Usa una herramienta como **Rufus** (en Windows) o **BalenaEtcher** para grabar la ISO en un pendrive.
3. **Instala**: Arranca tu PC desde el USB y sigue el instalador gráfico. 
   - **Sugerencia**: Durante la instalación, elige el sistema de archivos **Btrfs**, ya que es el que yo uso y permite hacer "snapshots" (copias de seguridad instantáneas) si algo sale mal.

---

## 🌟 ¿Qué hace especial a este sistema?

La magia principal es la **Sincronización de Colores Automática**. 
Imagínate que cambias el fondo de pantalla: el sistema "lee" los colores de esa imagen y, en un segundo, cambia el color de las ventanas, la terminal, la barra de tareas y las aplicaciones para que todo combine perfectamente. ✨

---

## 🛠️ Requisitos Previos (Antes de aplicar los Dotfiles)

Una vez que ya tengas CachyOS instalado y estés en el escritorio, necesitas instalar estas herramientas básicas para que mi configuración no dé errores. Abre la terminal y ejecuta:

### 📦 Instalación de Dependencias
Copia y pega este comando para instalar todo lo necesario de una vez:

```bash
sudo pacman -S git fish hyprland starship matugen waywallen thunar firefox codium foot kitty fuzzel btop htop nvtop cava fastfetch lazygit micro nvim
```

---

## 🚀 Cómo instalar mis configuraciones (Paso a Paso)

Ahora que tienes el sistema y las apps, vamos a aplicar mi "look":

1. **Descargar mis configuraciones:**
   ```bash
   git clone https://github.com/Liox269/dotfiles.back ~/dotfiles
   ```

2. **Entrar a la carpeta:**
   ```bash
   cd ~/dotfiles
   ```

3. **Dar permiso al instalador y ejecutarlo:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

**¿Qué acaba de pasar?** El script `install.sh` creó "puentes" (enlaces simbólicos) entre tu sistema y esta carpeta. Si cambias algo en la configuración, se guarda aquí automáticamente. Además, si tenías algo ya configurado, el script lo guardó como `.bak` para que no pierdas nada.

---

## ⌨️ Guía de Atajos (¿Cómo controlo todo?)

En Hyprland no usas mucho el ratón, usas el teclado. La tecla **SUPER** es generalmente la tecla de **Windows**.

### 🛠️ Magia de Liox (Efectos Visuales)
| Teclas | ¿Qué hace? |
| :--- | :--- |
| `SUPER` + `ALT` + `V` | **Modo Vibrante**: Hace que los colores se vean mucho más vivos. |
| `SUPER` + `ALT` + `SHIFT` + `V` | **Modo Normal**: Quita el efecto vibrante. |

### 🚀 Atajos de Supervivencia (Uso Diario)
| Teclas | Acción |
| :--- | :--- |
| `SUPER` + `Q` | **Cerrar Programa**: Cierra la ventana activa. |
| `SUPER` + `T` | **Abrir Terminal**: Abre la consola Fish. |
| `SUPER` + `W` | **Navegador**: Abre Firefox. |
| `SUPER` + `E` | **Archivos**: Abre Thunar. |
| `SUPER` + `C` | **Editor**: Abre Codium. |
| `SUPER` + `V` | **Portapapeles**: Abre el historial de copiado. |
| `SUPER` + `L` | **Bloquear**: Bloquea la sesión. |
| `SUPER` + `S` | **Espacio Especial**: Abre el espacio de trabajo especial. |
| `SUPER` + `Period` | **Emojis**: Abre el selector de emojis. |
| `Print` | **Captura**: Toma una captura de pantalla completa. |

### 🪟 Gestión de Ventanas
- **Moverse**: `SUPER` + `Flechas` para saltar entre ventanas.
- **Mover Ventana**: `SUPER` + `SHIFT` + `Flechas` para mover la ventana activa.
- **Cambiar Tamaño**: `SUPER` + `ALT` + `Flechas` para ajustar el ancho o alto.
- **Flotante**: `SUPER` + `ALT` + `Espacio` para hacer que la ventana flote.
- **Pantalla Completa**: `SUPER` + `F`.

### 📁 Espacios de Trabajo (Workspaces)
- **Saltar a Workspace**: `SUPER` + `Número (0-9)`.
- **Mover Ventana a Workspace**: `SUPER` + `ALT` + `Número (0-9)`.
- **Navegar rápido**: `SUPER` + `Rueda del ratón`.

---

## 📚 Diccionario de Configuraciones (Todo lo que hay en el repo)

### 🖥️ Entorno y Ventanas
- **Hyprland**: El corazón del sistema. Controla cómo se mueven las ventanas y los atajos.
- **Caelestia**: El framework que le da la identidad y el flujo de trabajo avanzado.
- **UWSM**: Gestiona la sesión de usuario para que todo inicie correctamente.

### 🎨 Estética y Colores
- **Matugen**: Genera la paleta de colores basada en el wallpaper.
- **Waywallen**: El gestor de fondos de pantalla.
- **Kvantum / Qt5ct / Qt6ct**: Hacen que las aplicaciones de KDE/Qt se vean coherentes y oscuras.

### 🐚 Terminal y Consola
- **Fish**: La terminal inteligente con auto-completado.
- **Starship**: El prompt (la línea de comandos) con iconos y colores.
- **Foot / Kitty**: Terminales rápidas y ligeras.
- **Fuzzel**: El lanzador de aplicaciones (el menú donde buscas programas).

### 🛠️ Herramientas de Sistema
- **Btop / Htop / Nvtop**: Monitores de recursos (CPU, RAM, GPU) con colores personalizados.
- **Fastfetch**: Muestra la información del sistema al abrir la terminal.
- **Cava**: El visualizador de música que se mueve al ritmo del sonido.
- **Lazygit**: Una forma visual y rápida de manejar Git.
- **Micro / Nvim**: Editores de texto potentes para programar.

### 🎵 Multimedia
- **Tidal Hi-Fi**: Configuraciones optimizadas para la mejor calidad de audio.

---

## 💡 Soluciones a Problemas Comunes

**"Instalé todo pero los colores no cambian"**
$\rightarrow$ Asegúrate de tener instalado `matugen` y `waywallen`. Intenta cambiar el fondo desde Waywallen.

**"Quiero volver a mi configuración anterior"**
$\rightarrow$ El instalador creó archivos `.bak` en tu carpeta `.config`. Borra el symlink y renombra el `.bak`.

**"El comando `install.sh` me da error de permiso"**
$\rightarrow$ No olvides ejecutar `chmod +x install.sh` antes de lanzarlo.

**Creado con ❤️ por [Liox269](https://github.com/Liox269). ¡Bienvenido al mundo de Linux!** 🚀
