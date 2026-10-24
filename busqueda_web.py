#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BÚSQUEDA WEB ABIERTA COMPARTIDA (PORTAL IPF)
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Licencia: PolyForm Noncommercial 1.0.0 con descargo de responsabilidad (ver LICENSE)
=============================================================================
Buscadores web sin clave de API para encontrar convocatorias que no están en
los portales con API (páginas de alcaldías, universidades, empresas...).
Ambos limitan a los bots, así que:
- se espacian las consultas (INTERVALO_S) y se reintenta tras un error;
- Yahoo va primero y DuckDuckGo queda de respaldo;
- un bloqueo se informa en consola en vez de tomarse como "cero resultados".
"""

import re
import threading
import time
from html import unescape
from urllib.parse import unquote

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}
INTERVALO_S = 6.0
_lock = threading.Lock()
_ultima = [0.0]


def _get(url, params):
    with _lock:
        espera = _ultima[0] + INTERVALO_S - time.time()
        if espera > 0:
            time.sleep(espera)
        _ultima[0] = time.time()
    try:
        return requests.get(url, params=params, headers=HEADERS, timeout=12)
    except requests.RequestException:
        return None


def _texto(raw):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", raw or ""))).strip()


def _yahoo(query):
    for intento in range(3):
        r = _get("https://search.yahoo.com/search", {"p": query})
        if r is not None and r.status_code == 200 and "compTitle" in r.text:
            break
        time.sleep(10 * (intento + 1))
    else:
        return None
    resultados = []
    # Cada resultado: <div class="compTitle"><a href=".../RU=<destino>/..."><span>sitio<span>ruta</span></span>Título</a>
    for url, contenido in re.findall(r'<div class="compTitle[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.DOTALL):
        destino = re.search(r"/RU=([^/]+)/", url)
        if destino:
            url = unquote(destino.group(1))
        # El sitio y la ruta van en <span> anidados antes del título: se quitan
        # de adentro hacia afuera.
        anterior = None
        while anterior != contenido:
            anterior, contenido = contenido, re.sub(r"<span[^>]*>[^<]*</span>", "", contenido)
        titulo = _texto(contenido)
        if titulo and "yahoo.com" not in url:
            resultados.append((url, titulo, ""))
    return resultados


def _duckduckgo(query):
    r = _get("https://html.duckduckgo.com/html/", {"q": query})
    if r is None or r.status_code != 200 or "anomaly" in r.text[:20000].lower():
        return None
    enlaces = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.DOTALL)
    resumenes = re.findall(r'class="result__snippet"[^>]*>(.*?)</', r.text, re.DOTALL)
    resultados = []
    for i, (url, titulo) in enumerate(enlaces):
        destino = re.search(r"[?&]uddg=([^&]+)", url)
        if destino:
            url = unquote(destino.group(1))
        resultados.append((url, _texto(titulo), _texto(resumenes[i]) if i < len(resumenes) else ""))
    return resultados


def buscar_web(query):
    """Lista de (url, título, resumen). Lista vacía si todos los buscadores bloquean."""
    for nombre, motor in (("Yahoo", _yahoo), ("DuckDuckGo", _duckduckgo)):
        resultados = motor(query)
        if resultados is not None:
            return [(u, t, s) for u, t, s in resultados if u.startswith("http")]
        print(f"    [!] {nombre} bloqueó la búsqueda '{query}'")
    return []
