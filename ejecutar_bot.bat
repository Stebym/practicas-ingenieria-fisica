@echo off
title Bot de Practicas - Ingenieria Fisica
cd /d "%~dp0"
python bot_practicas.py
python bot_pagina.py
echo.
echo Presiona cualquier tecla para salir...
pause >nul
