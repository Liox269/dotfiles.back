# dotfiles — Hyprland + caelestia rice

Mis dotfiles personales de Hyprland y resto del window manager sobre **CachyOS**.

## ⚠️ Basado en caelestia-dots

Este repo **incluye únicamente los archivos personalizados del usuario**. La mayoría
del comportamiento del WM (animaciones, keybinds, reglas de ventana, esquema de
colores base) viene del rice **[caelestia-dots/caelestia](https://github.com/caelestia-dots/caelestia)**,
que se encuentra clonado localmente en `~/caelestia` y NO se incluye aquí.

Crédits: <https://github.com/caelestia-dots/caelestia>

## Contenido

```
hypr/      hyprland.conf + scheme + shader personalizado (mi_vibrance.glsl)
caelestia/ overrides del usuario sobre el rice (user-config.fish, hypr-user.lua, ...)
uwsm/      variables de entorno (env, env-hyprland)
foot/      terminal
fish/      shell (config + greeting + variables)
fuzzel/    launcher
btop/      monitor de sistema + tema caelestia
micro/     editor (settings + colorschemes catppuccin)
cava/      visualizador de audio
fastfetch/ info del sistema
starship/  prompt
shell/     .zshrc, .bashrc, .bash_profile, .bash_logout
```

## Paquetes necesarios (Arch/CachyOS)

```bash
sudo pacman -S hyprland hyprshade uwsm foot fish fisher starship fuzzel \
                btop micro cava fastfetch swww hyprlock hypridle
```

Adicional (AUR, opcional):

```bash
yay -S catppuccin-micro-git  # los colorschemes ya vienen en este repo
```

## Instalación

El repo **no usa symlinks automáticos** (no es Stow). Para aplicar los dotfiles:

1. **Clonar caelestia upstream** (necesario, estos dotfiles lo dan por sentado):

   ```bash
   git clone https://github.com/caelestia-dots/caelestia.git ~/caelestia
   ```

2. **Copiar las configs a `~/.config/`**:

   ```bash
   cp -r hypr/*    ~/.config/hypr/
   cp -r caelestia/* ~/.config/caelestia/
   cp -r uwsm/*    ~/.config/uwsm/
   cp -r foot/*    ~/.config/foot/
   cp -r fish/*    ~/.config/fish/
   cp -r fuzzel/*  ~/.config/fuzzel/
   cp -r btop/*    ~/.config/btop/
   cp -r micro/*   ~/.config/micro/
   cp -r cava/*    ~/.config/cava/
   cp -r fastfetch/* ~/.config/fastfetch/
   mkdir -p ~/.config && cp starship/starship.toml ~/.config/
   ```

3. **Copiar los archivos de shell al home**:

   ```bash
   cp shell/.zshrc        ~/
   cp shell/.bashrc       ~/
   cp shell/.bash_profile ~/
   cp shell/.bash_logout  ~/
   ```

4. **Reiniciar Hyprland** (`Super+Esc` para menu, o reiniciar sesión).

## Hardware probado

- 2 monitores: DP-2 (1920x1080@60) + HDMI-A-1 (1920x1080@144)
- GPU NVIDIA (ver `~/.config/hypr/hyprland.conf` para `QT_FFMPEG_DECODING_HW_DEVICE_TYPES`)
- Distro: CachyOS (kernel cachyos, perfil gamer + nvidia)

## Notas

- `~/.config/hypr/scheme/current.{conf,lua}` es el esquema personalizado activo.
- `~/.config/hypr/shaders/mi_vibrance.glsl` es un shader Hyprland propio (vibrance).
- El wallapper (`swww img ~/Descargas/_.jpeg`) está hardcodeado en `hyprland.conf`.