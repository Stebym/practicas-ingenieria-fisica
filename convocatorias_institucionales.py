#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CONVOCATORIAS INSTITUCIONALES (PORTAL IPF)
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Licencia: PolyForm Noncommercial 1.0.0 con descargo de responsabilidad (ver LICENSE)
=============================================================================
Las convocatorias grandes de prácticas (Alcaldía, Gobernación, FLA, ISAGEN,
Ecopetrol, Bancolombia...) no salen en Magneto ni en LinkedIn: se anuncian en
las páginas de prácticas de las universidades. Este módulo lee sus feeds RSS
(fuentes_convocatorias.json) y deja solo las convocatorias que piden una
carrera afín y siguen abiertas.
"""

import os
import re
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from html import unescape

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FUENTES_PATH = os.path.join(BASE_DIR, "fuentes_convocatorias.json")
# WordPress.com responde 403 al User-Agent completo de Chrome enviado desde
# requests; uno honesto que identifica al portal sí pasa.
HEADERS = {
    "User-Agent": "PortalPracticasIPF/1.0 (+https://stebym.github.io/practicas-ingenieria-fisica/)",
}
# Sin fecha de cierre explícita, una convocatoria más vieja que esto se da por cerrada.
DIAS_MAXIMOS_SIN_CIERRE = 40

TITULO_CONVOCATORIA_RE = re.compile(
    r"pr[aá]cticas?|practicantes?|pasant[ií]as?|aprendices|talento\s+(?:joven|b)\b|semillero", re.IGNORECASE
)
# Charlas, ferias y resultados no son convocatorias a las que uno se postule.
TITULO_NO_CONVOCATORIA_RE = re.compile(
    r"resultados?|listado|invitaci[oó]n|charla|feria|webinar|taller|seleccionad|ganador|modalidad\s+de\s+pr[aá]cticas", re.IGNORECASE
)
CARRERA_AFIN_RE = re.compile(
    r"ingenier[ií]a\s+f[ií]sica|\bf[ií]sica\b|electromec[aá]nic|electr[oó]nic|el[eé]ctric|mecatr[oó]nic|"
    r"instrumentaci|automatizaci|metrolog|materiales|bioingenier|todas\s+las\s+(?:ingenier[ií]as|carreras)|"
    r"cualquier\s+(?:ingenier[ií]a|carrera|programa)|ingenier[ií]as\b|ciencias\s+exactas|stem\b|"
    r"ciencia\s+de\s+datos|anal[ií]tica\s+de\s+datos",
    re.IGNORECASE,
)
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
# "hasta el 30 de octubre", "cierre: 9 de octubre de 2026". "Del 13 de enero al 9 de julio"
# suele ser el periodo de la práctica, no el cierre, así que "al" no cuenta.
CIERRE_RE = re.compile(
    r"(?:hasta|cierra|cierre|plazo|l[ií]mite|vence)\b[^.\n]{0,40}?"
    r"(\d{1,2})\s+de\s+(" + "|".join(MESES) + r")(?:\s+(?:de|del)\s+(\d{4}))?",
    re.IGNORECASE,
)


def _texto(raw):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", unescape(raw or "")))).strip()


def fecha_cierre(texto, publicada):
    """La fecha de cierre más tardía que anuncie el texto, o None si no la dice."""
    fechas = []
    for dia, mes, anio in CIERRE_RE.findall(texto):
        anio = int(anio) if anio else publicada.year
        try:
            f = date(anio, MESES[mes.lower()], int(dia))
        except ValueError:
            continue
        # "hasta el 15 de enero" publicado en noviembre es del año siguiente.
        if not anio and f < publicada:
            f = f.replace(year=f.year + 1)
        fechas.append(f)
    return max(fechas) if fechas else None


def _empresa(titulo, fuente):
    nombre = re.sub(
        r"\b(?:convocatorias?|abiertas?|abierto|inscripciones|post[uú]late|haz|hacer|tus|las|pr[aá]cticas?|practicantes?|"
        r"pasant[ií]as?|profesionales?|acad[eé]micas?|universitari[oa]s?|para|da|un|paso|el|la|los|de|del|en|y|semestre|periodo)\b"
        r"|\d{4}\s*-\s*\d|\d{4}|[-–:,¡!¿?]",
        " ", titulo, flags=re.IGNORECASE,
    )
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre if 2 < len(nombre) < 60 else f"Convocatoria ({fuente})"


def _cuerpo_publicacion(link):
    """Texto de la entrada cuando el feed solo trae un resumen."""
    try:
        r = requests.get(link, headers=HEADERS, timeout=15)
    except requests.RequestException:
        return ""
    if r.status_code != 200:
        return ""
    m = re.search(r'class="[^"]*entry-content[^"]*"[^>]*>(.*?)(?:</article>|<footer|class="[^"]*(?:sharedaddy|post-navigation))',
                  r.text, re.DOTALL)
    return _texto(m.group(1)) if m else ""


def leer_feed(fuente, hoy=None):
    """Convocatorias abiertas y afines de un feed RSS de WordPress."""
    hoy = hoy or date.today()
    encontradas = []
    for pagina in range(1, int(fuente.get("paginas", 1)) + 1):
        url = fuente["feed"] + (f"?paged={pagina}" if pagina > 1 else "")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
        except requests.RequestException:
            break
        if r.status_code != 200:
            break
        items = re.findall(r"<item>(.*?)</item>", r.text, re.DOTALL)
        if not items:
            break
        for item in items:
            def campo(tag):
                m = re.search(rf"<{tag}>(.*?)</{tag}>", item, re.DOTALL)
                return re.sub(r"^<!\[CDATA\[|\]\]>$", "", m.group(1).strip()) if m else ""
            titulo = _texto(campo("title"))
            link = campo("link")
            if not TITULO_CONVOCATORIA_RE.search(titulo) or TITULO_NO_CONVOCATORIA_RE.search(titulo):
                continue
            try:
                publicada = parsedate_to_datetime(campo("pubDate")).date()
            except (TypeError, ValueError):
                continue
            if (hoy - publicada).days > 120:
                continue
            cuerpo = _texto(campo("content:encoded") or campo("description"))
            if len(cuerpo) < 300:
                cuerpo = _cuerpo_publicacion(link) or cuerpo
            # Cada fuente puede repetir una nota fija (p. ej. el blog de la UdeA nombra
            # siempre Electrónica/Telecomunicaciones); esa nota no es un requisito.
            for patron in fuente.get("ignorar", []):
                cuerpo = re.sub(patron, " ", cuerpo, flags=re.IGNORECASE)
            texto = f"{titulo} {cuerpo}"
            carreras = sorted({m.group(0).lower() for m in CARRERA_AFIN_RE.finditer(texto)})
            if not carreras:
                continue
            cierre = fecha_cierre(texto, publicada)
            if cierre and cierre < hoy:
                continue
            if not cierre and (hoy - publicada).days > DIAS_MAXIMOS_SIN_CIERRE:
                continue
            job = {
                "titulo": titulo,
                "empresa": _empresa(titulo, fuente["nombre"]),
                "ubicacion": "Medellín, Antioquia (convocatoria institucional)",
                "url": link,
                "fecha_publicacion": publicada.isoformat(),
                "fuente": f"Convocatoria institucional · {fuente['nombre']}",
                "perfil": "Carreras mencionadas: " + ", ".join(carreras),
                "descripcion_fuente": cuerpo[:2500],
                "tipo_empleo": "Práctica",
                # Ya se filtró aquí por carrera afín y vigencia; el clasificador
                # del bot no debe juzgarlas por el título, que es de noticia.
                "curada": True,
            }
            if cierre:
                job["fecha_cierre_iso"] = cierre.isoformat()
            encontradas.append(job)
    return encontradas


def scrape_convocatorias_institucionales(fuentes):
    resultados = []
    for fuente in fuentes or []:
        if isinstance(fuente, dict) and fuente.get("feed"):
            resultados.extend(leer_feed(fuente))
    return resultados


if __name__ == "__main__":
    import json
    with open(FUENTES_PATH, encoding="utf-8") as f:
        for c in scrape_convocatorias_institucionales(json.load(f)):
            print(c["fecha_publicacion"], "| cierre", c.get("fecha_cierre_iso", "?"), "|", c["empresa"], "|", c["titulo"])
            print("   ", c["perfil"], "|", c["url"])
