#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BOT DE CONVENIOS INTERNACIONALES UNAL (DRIVE / GOOGLE SHEETS DE LA DRE)
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Universidad Nacional de Colombia - Sede Medellín • Ingeniería Física
Licencia: PolyForm Noncommercial 1.0.0 con descargo de responsabilidad (ver LICENSE)
=============================================================================
Descarga la hoja pública de convenios de la Dirección de Relaciones Exteriores
de la UNAL y conserva los vigentes de ciencias, ingeniería y movilidad.
Salida: convenios_internacionales.json (la página la arma bot_pagina.py).
"""

import os
import io
import csv
import re
import json
import requests

from firma import encabezado_bot, sellar_registros

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONVENIOS_JSON_PATH = os.path.join(BASE_DIR, "convenios_internacionales.json")

# Hoja oficial de Convenios UNAL DRE (Google Sheets público)
SHEET_ID = "1X0ZaWn8uxyFy9w_lf3lzHjdvmL6L3IYGbjMnR6D51As"
GID = "1315141815"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_unal_convenios():
    """Descarga y filtra convenios vigentes para STEM y movilidad internacional de la UNAL."""
    print("[*] Descargando catálogo de convenios UNAL DRE desde Google Sheets...")
    try:
        r = requests.get(SHEET_CSV_URL, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            print(f" [!] Error al descargar sheet: HTTP {r.status_code}")
            return []
        
        reader = csv.reader(io.StringIO(r.text))
        rows = list(reader)
        print(f" [✓] {len(rows)} filas descargadas. Procesando y filtrando áreas STEM...")

        afines = []
        # La tabla oficial de datos comienza en la fila 26 (índice 25 son encabezados)
        for row in rows[26:]:
            if len(row) < 8:
                continue
            ano, pais, inst, nombre, tipo, estado, link, area = row[:8]
            if estado.strip().upper() != "VIGENTE":
                continue
            
            area_u = area.upper()
            is_stem = any(k in area_u for k in [
                "INGENIERÍA", "INGENIERIA", "MATEMATICA", "CIENCIAS", "EXACTAS",
                "TODAS LAS ÁREAS", "INTERDISCIPLINAR", "TECNOLOGÍA", "TECNOLOGIA"
            ])
            if not is_stem:
                continue
            
            is_intl = pais.strip().upper() != "COLOMBIA"
            is_practica = any(k in tipo.upper() for k in [
                "PRÁCTICA", "PRACTICA", "PASANTÍA", "PASANTIA", "INTERCAMBIO",
                "MOVILIDAD", "INVESTIGACIÓN", "INVESTIGACION", "DOBLE TITULACIÓN", "ERASMUS"
            ])
            
            if is_practica or is_intl:
                clean_pais = pais.strip().title()
                clean_inst = re.sub(r"\s+", " ", inst.strip().title())
                clean_tipo = re.sub(r"\s+", " ", tipo.strip().title())
                clean_nombre = re.sub(r"\s+", " ", nombre.strip())
                clean_area = re.sub(r"\s+", " ", area.strip().title())
                
                afines.append({
                    "ano": ano.strip(),
                    "pais": clean_pais,
                    "institucion": clean_inst,
                    "nombre": clean_nombre,
                    "tipo": clean_tipo,
                    "link": link.strip(),
                    "area": clean_area
                })
        
        print(f" [✓] {len(afines)} convenios vigentes STEM/Internacionales identificados.")
        if not afines:
            print(" [!] La hoja no devolvió convenios; se conserva el archivo anterior.")
            return []
        sellar_registros(afines, campo_clave="link")
        with open(CONVENIOS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(afines, f, ensure_ascii=False, indent=2)
        print(f" [✓] Guardado en: {CONVENIOS_JSON_PATH}")
        return afines
    except Exception as e:
        print(f" [!] Excepción descargando convenios: {e}")
        return []

def main():
    print(encabezado_bot("[CONVENIOS] BOT DE CONVENIOS INTERNACIONALES UNAL (DRE)"))
    fetch_unal_convenios()

if __name__ == "__main__":
    main()
