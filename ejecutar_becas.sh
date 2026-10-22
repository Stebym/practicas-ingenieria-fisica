#!/usr/bin/env bash
# Bot de Becas y Convenios Internacionales - Ingeniería Física UNAL
set -e
cd "$(dirname "$0")"

echo "Iniciando rastreo de becas y convenios internacionales..."
python3 bot_becas_internacionales.py
