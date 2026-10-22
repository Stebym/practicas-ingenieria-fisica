#!/usr/bin/env bash
# Bot de Rastreo de Prácticas - Ingeniería Física UNAL
set -e
cd "$(dirname "$0")"

echo "Iniciando rastreo de prácticas para Ingeniería Física..."
python3 bot_practicas.py
