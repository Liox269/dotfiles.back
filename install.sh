#!/bin/sh

  # Colores para la terminal
  GREEN='\033[0;32m'
  BLUE='\033[0;34m'
  YELLOW='\033[1;33m'
  NC='\033[0m'

  echo "${BLUE}============================================================${NC}"
  echo "${BLUE}   🚀 RESTAURANDO CONFIGURACIONES DE LIOX269...${NC}"
  echo "${BLUE}============================================================${NC}"

  if [ ! -d "./config" ]; then
      echo "${YELLOW}❌ Error: Debes ejecutar este script desde la carpeta ~/dotfiles${NC}"
      exit 1
  fi

  mkdir -p "$HOME/.config"

  link_config() {
      src="$1"
      dst="$2"
      if [ -e "$dst" ] || [ -L "$dst" ]; then
          echo "${YELLOW}⚠️  $dst ya existe. Respaldando como .bak${NC}"
          mv "$dst" "${dst}.bak" 2>/dev/null
      fi
      ln -s "$src" "$dst"
      echo "${GREEN}✅ Vinculado:${NC} $dst -> $src"
  }

  echo "\n${BLUE}📦 Procesando carpetas de configuración...${NC}"
  for dir in config/*/; do
      dir=${dir%/}
      folder_name=${dir##*/}
      if [ "$folder_name" = "starship" ]; then
          continue
      fi
      link_config "$HOME/dotfiles/$dir" "$HOME/.config/$folder_name"
  done

  echo "\n${BLUE}🛠️  Instalando scripts y binarios...${NC}"
  mkdir -p "$HOME/.local/bin"
  if [ -d "./bin" ]; then
      for script in bin/*; do
          [ -e "$script" ] || continue
          script_name=${script##*/}
          link_config "$HOME/dotfiles/bin/$script_name" "$HOME/.local/bin/$script_name"
          chmod +x "$HOME/.local/bin/$script_name"
      done
  fi

  echo "\n${BLUE}📄 Procesando archivos individuales...${NC}"
  if [ -f "./config/starship/starship.toml" ]; then
      link_config "$HOME/dotfiles/config/starship/starship.toml" "$HOME/.config/starship.toml"
  fi

  echo "\n${BLUE}============================================================${NC}"
  echo "${GREEN}✨ ¡PROCESO COMPLETADO CON ÉXITO!${NC}"
  echo "${BLUE}============================================================${NC}"
