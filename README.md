# 🌌 Liox269 Dotfiles - El Manual Maestro

¡Bienvenido! Este repositorio es la "receta" de mi computadora. Aquí guardo todas las configuraciones que hacen que mi sistema se vea increíble y funcione rápido. 

Si eres nuevo en Linux o quieres probar mi configuración, **este manual es para ti**. He diseñado todo para que sea fácil de instalar, incluso si nunca has tocado una terminal.

---

## 🌟 ¿Qué hace especial a este sistema?

La magia principal es la **Sincronización de Colores Automática**. 
Imagínate que cambias el fondo de pantalla: el sistema "lee" los colores de esa imagen y, en un segundo, cambia el color de las ventanas, la terminal, la barra de tareas y las aplicaciones para que todo combine perfectamente. ¡Como magia! ✨

---

## 🛠️ Guía para Principiantes: ¿Qué necesito antes de empezar?

Para que mi configuración funcione, tu computadora debe tener instalado **CachyOS** (o una base Arch Linux). Antes de ejecutar mi instalador, necesitas instalar estas herramientas (puedes buscarlas en la tienda de aplicaciones o usar la terminal):

### 📦 Lo Básico (Imprescindibles)
- **Git**: Para descargar este repositorio.
- **Fish**: Es la "consola" o terminal donde escribes los comandos.
- **Hyprland**: Es el "cerebro" que organiza las ventanas en la pantalla.
- **Starship**: Es lo que hace que la línea donde escribes comandos se vea bonita y con iconos.

### 🎨 Lo Visual (Para que los colores funcionen)
- **Waywallen**: El programa para poner fondos de pantalla.
- **Matugen**: El motor que extrae los colores del fondo.

---

## 🚀 Cómo instalarlo (Paso a Paso)

No te asustes por la terminal, solo copia y pega estos comandos uno por uno:

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

### 🛠️ Funciones Especiales (Magia de Liox)
| Teclas | ¿Qué hace? |
| :--- | :--- |
| `SUPER` + `ALT` + `V` | **Modo Vibrante**: Hace que los colores de la pantalla se vean mucho más vivos y saturados. |
| `SUPER` + `ALT` + `SHIFT` + `V` | **Modo Normal**: Quita el efecto vibrante y vuelve a los colores originales. |

### 🚀 Atajos Básicos (Para empezar a navegar)
*(Nota: Estos son los atajos estándar de mi configuración)*
- `SUPER` + `Q`: Abre la terminal (para escribir comandos).
- `SUPER` + `C`: Cierra la ventana que tienes abierta.
- `SUPER` + `M`: Sale de Hyprland y vuelve a la pantalla de inicio de sesión.
- `SUPER` + `E`: Abre el explorador de archivos.
- `SUPER` + `V`: Abre el menú de aplicaciones (donde buscas tus programas).
- `SUPER` + `R`: Abre el lanzador rápido para ejecutar algo.

---

## 📂 ¿Dónde está cada cosa? (Para los curiosos)

Si quieres cambiar algo manualmente, busca aquí:
- **Colores y Temas**: `~/dotfiles/config/matugen`
- **Atajos y Ventanas**: `~/dotfiles/config/hypr/hyprland.conf`
- **Consola/Terminal**: `~/dotfiles/config/fish`
- **Fondos de Pantalla**: `~/dotfiles/config/waywallen`
- **Scripts Maestros**: `~/dotfiles/bin/`

---

## 💡 Soluciones a Problemas Comunes

**"Instalé todo pero los colores no cambian"**
$\rightarrow$ Asegúrate de tener instalado `matugen` y `waywallen`. Luego, intenta cambiar el fondo de pantalla desde Waywallen.

**"Quiero volver a mi configuración anterior"**
$\rightarrow$ El instalador creó archivos `.bak` en tu carpeta `.config`. Solo tienes que borrar el enlace simbólico y renombrar el archivo `.bak` a su nombre original.

**"El comando `install.sh` me da error de permiso"**
$\rightarrow$ No olvides ejecutar `chmod +x install.sh` antes de lanzarlo.

---

## 📈 ¿Cómo mejorar este sistema?
Este es un proyecto vivo. Si encuentras una forma de hacerlo más rápido o más bonito:
1. Haz el cambio en tu carpeta `~/dotfiles`.
2. Sube los cambios a GitHub.
3. ¡Disfruta de tu nueva mejora!

**Creado con ❤️ por [Liox269](https://github.com/Liox269). ¡Bienvenido al mundo de Linux!** 🚀
