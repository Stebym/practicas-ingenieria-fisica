#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica si un archivo (HTML o JSON) contiene la firma interna del Portal IPF.
Autor: Jimmy Stebym Rosero Barrera • Licencia MIT (ver LICENSE)

Uso:
    python verificar_firma.py index.html vacantes_practicas.json retos_hackatones.json
"""

import json
import sys

from firma import FIRMA_ID, leer_marca_agua, sello


def verificar(ruta):
    with open(ruta, encoding="utf-8") as f:
        contenido = f.read()
    hallazgos = []
    if leer_marca_agua(contenido) == FIRMA_ID:
        hallazgos.append("marca de agua invisible")
    if f'content="ipf-{FIRMA_ID}"' in contenido or f"--ipf-firma: '{FIRMA_ID}'" in contenido:
        hallazgos.append("metadato de firma")
    try:
        datos = json.loads(contenido)
    except ValueError:
        datos = None
    if isinstance(datos, list) and datos:
        registros = [d for d in datos if isinstance(d, dict) and "_sello" in d]
        validos = sum(
            1 for d in registros
            if d["_sello"] == sello(str(d.get("url") or d.get("link") or d.get("titulo") or ""))
        )
        if validos:
            hallazgos.append(f"{validos} de {len(datos)} registros con sello válido")
    return hallazgos


def main():
    rutas = sys.argv[1:] or ["index.html"]
    for ruta in rutas:
        try:
            hallazgos = verificar(ruta)
        except OSError as error:
            print(f"{ruta}: no se pudo leer ({error})")
            continue
        estado = "FIRMADO" if hallazgos else "sin firma del Portal IPF"
        detalle = f" ({', '.join(hallazgos)})" if hallazgos else ""
        print(f"{ruta}: {estado}{detalle}")


if __name__ == "__main__":
    main()
