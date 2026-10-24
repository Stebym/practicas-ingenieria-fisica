@echo off
rem Portal IPF - Jimmy Stebym Rosero Barrera (Licencia PolyForm Noncommercial, ver LICENSE)
rem Corre los cuatro bots de datos y luego el bot que arma la pagina.
title Portal IPF - Bots
cd /d "%~dp0"
for %%B in (practicas retos becas convenios) do (
  echo == bot_%%B.py
  python bot_%%B.py
)
echo == bot_pagina.py
python bot_pagina.py
pause
