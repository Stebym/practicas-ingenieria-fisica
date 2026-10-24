#!/usr/bin/env bash
# Portal IPF - Jimmy Stebym Rosero Barrera (Licencia MIT, ver LICENSE)
# Corre los cuatro bots de datos y luego el bot que arma la página.
# Uso: ./ejecutar_todo.sh            (todos)
#      ./ejecutar_todo.sh retos becas (solo esos, y luego la página)
set -e
cd "$(dirname "$0")"

bots=("$@")
[ ${#bots[@]} -eq 0 ] && bots=(practicas retos becas convenios)
for bot in "${bots[@]}"; do
  echo "== bot_${bot}.py"
  python3 "bot_${bot}.py"
done
echo "== bot_pagina.py"
python3 bot_pagina.py
