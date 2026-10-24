#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
FIRMA, AUTORÍA Y AVISO LEGAL DEL PORTAL IPF
Proyecto: Portal de Prácticas, Retos y Becas • Ingeniería Física UNAL Medellín
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Licencia: PolyForm Noncommercial 1.0.0 con descargo de responsabilidad (ver LICENSE)
=============================================================================
Módulo compartido por todos los bots. Centraliza:
1. La autoría y el aviso legal que se muestran en la página y en los datos.
2. La firma interna del proyecto, que viaja dentro de la estructura de los
   archivos generados (no solo en un comentario visible):
   - una marca de agua invisible (caracteres de ancho cero) en el pie de la
     página;
   - un sello por registro (`_sello`) en cada JSON de datos, derivado de la
     firma y del enlace de cada oportunidad.
   `python verificar_firma.py <archivo>` detecta ambas marcas.
"""

import hashlib

AUTOR = "Jimmy Stebym Rosero Barrera"
CONTACTO = "jiroserob@unal.edu.co"
PROYECTO = "Portal IPF · Prácticas, Retos y Becas · Ingeniería Física UNAL Medellín"
REPOSITORIO = "https://github.com/Stebym/practicas-ingenieria-fisica"
SITIO = "https://stebym.github.io/practicas-ingenieria-fisica/"
ANIO = 2026

# Identificador estable de la obra. Cambiarlo invalida los sellos ya emitidos.
FIRMA_ID = hashlib.sha256(f"{AUTOR}|{PROYECTO}|{ANIO}".encode("utf-8")).hexdigest()[:16]

AVISO_LEGAL_CORTO = (
    "Proyecto académico independiente. No somos agencia de empleo ni representamos "
    "a las empresas, universidades o plataformas citadas. La información proviene de "
    "fuentes públicas y puede cambiar o tener errores: verifica siempre en la fuente "
    "oficial antes de postularte. El autor no se hace responsable por decisiones, "
    "postulaciones, pérdidas o daños derivados del uso de este portal ni por el mal "
    "uso que terceros hagan del código o de los datos."
)

# Marca de agua invisible: los bits de FIRMA_ID se codifican con caracteres de
# ancho cero entre dos delimitadores (WORD JOINER). No altera el texto visible.
_CERO, _UNO, _DELIM = "​", "‌", "⁠"


def marca_agua(texto):
    """Devuelve `texto` con la firma del proyecto incrustada de forma invisible."""
    bits = "".join(f"{int(c, 16):04b}" for c in FIRMA_ID)
    oculto = _DELIM + "".join(_UNO if b == "1" else _CERO for b in bits) + _DELIM
    mitad = len(texto) // 2
    return texto[:mitad] + oculto + texto[mitad:]


def leer_marca_agua(texto):
    """Extrae la firma incrustada por `marca_agua`, o None si no la hay."""
    inicio = texto.find(_DELIM)
    fin = texto.find(_DELIM, inicio + 1)
    if inicio < 0 or fin < 0:
        return None
    bits = "".join("1" if c == _UNO else "0" for c in texto[inicio + 1:fin] if c in (_CERO, _UNO))
    if len(bits) % 4:
        return None
    return "".join(f"{int(bits[i:i + 4], 2):x}" for i in range(0, len(bits), 4))


def sello(clave):
    """Sello corto de un registro: solo coincide si fue generado con FIRMA_ID."""
    return hashlib.sha256(f"{FIRMA_ID}:{clave}".encode("utf-8")).hexdigest()[:12]


def sellar_registros(registros, campo_clave="url"):
    """Agrega `_sello` a cada registro (dict) usando su enlace como clave."""
    for registro in registros:
        if isinstance(registro, dict):
            registro["_sello"] = sello(str(registro.get(campo_clave) or registro.get("titulo") or ""))
    return registros


def encabezado_bot(nombre_bot):
    """Encabezado de consola común a todos los bots."""
    linea = "=" * 70
    return f"{linea}\n {nombre_bot}\n {PROYECTO}\n Autor: {AUTOR} • Firma {FIRMA_ID}\n{linea}"
