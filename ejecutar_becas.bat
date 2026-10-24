@echo off
cd /d "%~dp0"
echo Iniciando rastreo de becas y convenios internacionales...
python bot_becas.py
python bot_convenios.py
python bot_pagina.py
pause
