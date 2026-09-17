#!/bin/bash
# Abre un espacio de trabajo de forma SECUENCIAL y predecible:
#   por cada app: cambia a su escritorio -> espera -> lanza -> sondea.
# Al cambiar de escritorio antes de lanzar, la ventana nueva hereda el
# escritorio con foco, asi que cada app cae donde debe (incluso la misma
# app en varios escritorios). Tras lanzar, sondea cada 1s hasta detectar
# la ventana nueva en ese escritorio (con un tope de WAIT_MAP segundos) y
# entonces espera WAIT_LAUNCH para que la ventana termine de asentarse.
# Al final vuelve al escritorio `switchTo`.
#
# Crea un archivo "busy" mientras corre para que el plugin de la barra
# muestre un spinner.
#
# Uso: launch.sh <indice>
# Requiere: jq, hyprctl, uwsm-app.

set -u
CONFIG="$HOME/.config/omarchy/workspace-setups.json"
BUSY="/tmp/workspace-setups.busy"
INDEX="${1:-0}"
WAIT_FOCUS=1     # espera tras cambiar de escritorio
WAIT_LAUNCH=2    # espera tras detectar la ventana (asentamiento)
WAIT_MAP=10      # tope de espera para que aparezca la ventana

command -v jq >/dev/null || { echo "falta jq" >&2; exit 1; }
[[ -f $CONFIG ]] || { echo "no existe $CONFIG" >&2; exit 1; }

COUNT=$(jq '.setups | length' "$CONFIG")
(( INDEX >= 0 && INDEX < COUNT )) || { echo "indice fuera de rango" >&2; exit 1; }
SETUP=$(jq -c ".setups[$INDEX]" "$CONFIG")

# Marca de ocupado (la quita siempre al salir).
touch "$BUSY"
trap 'rm -f "$BUSY"' EXIT

mapfile -t APPS < <(jq -c '.apps[] | select(.command != null and .command != "")' <<<"$SETUP")

for app in "${APPS[@]}"; do
  WS=$(jq -r 'if .workspace == null then 1 else .workspace end' <<<"$app")
  CMD=$(jq -r '.command' <<<"$app")

  # 1) Cambia al escritorio objetivo
  hyprctl dispatch "hl.dsp.focus({ workspace = \"${WS}\" })" >/dev/null 2>&1
  # 2) Espera
  sleep "$WAIT_FOCUS"
  # 3) Anota las ventanas actuales del escritorio (para detectar la nueva)
  BEFORE=$(hyprctl -j clients | jq -r --arg ws "$WS" \
    '.[] | select(.workspace.id == ($ws | tonumber)) | .address' | sort)
  # 4) Lanza la aplicacion (hereda el escritorio con foco)
  hyprctl dispatch "hl.dsp.exec_cmd(\"uwsm-app -- ${CMD}\")" >/dev/null 2>&1
  # 5) Sondea cada 1s hasta que aparezca la ventana nueva (tope WAIT_MAP s)
  for ((i = 0; i < WAIT_MAP; i++)); do
    sleep 1
    NOW=$(hyprctl -j clients | jq -r --arg ws "$WS" \
      '.[] | select(.workspace.id == ($ws | tonumber)) | .address' | sort)
    # Si hay alguna direccion en NOW que no estaba en BEFORE: ventana detectada
    if comm -13 <(printf '%s\n' "$BEFORE") <(printf '%s\n' "$NOW") | grep -q .; then
      break
    fi
  done
  # 6) Espera a que la ventana termine de asentarse antes de la siguiente
  sleep "$WAIT_LAUNCH"
done

# Al final, vuelve al escritorio objetivo del espacio (si se definio).
SWITCH=$(jq -r '.switchTo // empty' <<<"$SETUP")
if [[ -n $SWITCH ]]; then
  hyprctl dispatch "hl.dsp.focus({ workspace = \"${SWITCH}\" })" >/dev/null 2>&1
fi
