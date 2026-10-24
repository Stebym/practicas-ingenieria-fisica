#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BOT DE RASTREO: RETOS, HACKATONES Y COMPETENCIAS (PORTAL IPF)
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Universidad Nacional de Colombia - Sede Medellín • Ingeniería Física
Licencia: PolyForm Noncommercial 1.0.0 con descargo de responsabilidad (ver LICENSE)
=============================================================================
Rastrea oportunidades para participar como estudiante:
1. Hackatones en línea abiertos o próximos (API pública de Devpost).
2. Competencias de datos e IA (Zindi y DrivenData).
3. Retos de ciudad, innovación abierta y convocatorias en Colombia y Medellín
   (Ruta N, Alcaldía, Metro, MinCiencias, iNNpulsa, movilidad, energía...)
   mediante búsqueda web abierta.
4. Plataformas y programas recurrentes curados en retos_destacados.json.

Reglas de alcance (iguales a las de prácticas):
- En línea / remoto: sirve desde cualquier país.
- Presencial: solo Medellín / Antioquia.
Salida: retos_hackatones.json (la página la arma bot_pagina.py).
"""

import json
import os
import re
import sys
import time
from datetime import date, datetime
from html import unescape
from urllib.parse import urlparse

import requests

from busqueda_web import buscar_web
from firma import encabezado_bot, sellar_registros

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RETOS_JSON_PATH = os.path.join(BASE_DIR, "retos_hackatones.json")
RETOS_DESTACADOS_PATH = os.path.join(BASE_DIR, "retos_destacados.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

LOCAL_RE = re.compile(r"medell[ií]n|antioquia|valle de aburr[aá]|envigado|itag[uüí]|rionegro|sabaneta|\bbello\b", re.IGNORECASE)
ONLINE_RE = re.compile(r"\b(?:online|en\s+l[ií]nea|virtual|remot[oa]|remote|global|worldwide)\b", re.IGNORECASE)

# Temas que encajan con el perfil de Ingeniería Física. Cada coincidencia suma
# puntos; los retos sin ninguna quedan al final de la lista.
TEMAS_PERFIL = {
    "Física, cuántica y espacio": r"quantum|cu[aá]ntic|f[ií]sic|physics|\bspace\b|espacial|nasa|astro|sat[eé]lit|aeroespacial",
    "Energía y clima": r"energ[ií]a|energy|solar|renovable|renewable|clima|climate|carbon|sostenib|sustainab|hidr[oó]geno|grid|red\s+el[eé]ctrica",
    "Movilidad y ciudad": r"movilidad|mobility|tr[aá]fico|traffic|transporte|transport|pico\s+y\s+placa|ciudad|city|smart\s+cit|urban|metro\b|seguridad\s+vial",
    "Datos, IA y simulación": r"\bai\b|\bia\b|inteligencia\s+artificial|machine\s+learning|deep\s+learning|datos|data|analytics|anal[ií]tica|simulaci|modelado|llm|computer\s+vision|visi[oó]n\s+artificial",
    "Hardware, IoT y electrónica": r"hardware|iot|internet\s+de\s+las\s+cosas|embedded|embebid|electr[oó]nic|rob[oó]tic|robotics|sensor|drone|dron|arduino|fpga",
    "Salud y biomédica": r"health|salud|medical|m[eé]dic|biomed|biotech|bioingenier",
    "Materiales y manufactura": r"materiales|materials|manufactur|industria\s*4\.0|industrial|miner[ií]a|mining|geolog",
    "Innovación abierta": r"innovaci[oó]n\s+abierta|open\s+innovation|reto\s+empresarial|startup|emprend",
}
TEMAS_FUERA = re.compile(
    r"\b(?:nft|crypto|memecoin|gambling|casino|betting|onlyfans|high\s*school(?:ers?)?|secondary\s+school|"
    r"middle\s+school|k-?12|solo\s+colegios?)\b",
    re.IGNORECASE,
)

# Búsquedas web para retos en Colombia que no tienen API.
WEB_QUERIES = [
    ("retos de innovación abierta Ruta N convocatoria", "Colombia"),
    ("reto de ciudad Medellín convocatoria estudiantes", "Colombia"),
    ("hackatón Medellín 2026", "Colombia"),
    ("hackathon Colombia 2026 estudiantes universitarios", "Colombia"),
    ("reto movilidad Medellín datos abiertos convocatoria", "Colombia"),
    ("reto pico y placa movilidad hackatón", "Colombia"),
    ("convocatoria retos MinCiencias estudiantes 2026", "Colombia"),
    ("iNNpulsa convocatoria reto innovación 2026", "Colombia"),
    ("Metro de Medellín innovación abierta reto", "Colombia"),
    ("datos abiertos Colombia concurso reto 2026", "Colombia"),
    ("NASA Space Apps Challenge Medellín", "Colombia"),
    ("reto energía Colombia estudiantes ingeniería convocatoria 2026", "Colombia"),
    ("Meta hackathon Llama challenge 2026", "Internacional"),
    ("student engineering challenge 2026 open international", "Internacional"),
]
RETO_RE = re.compile(r"\b(?:retos?|hackat[oó]n(?:es)?|hackathon|desaf[ií]os?|challenge|concurso|convocatoria|competencia|competition|bootcamp|ideat[oó]n)\b", re.IGNORECASE)
WEB_DOMINIOS_EXCLUIDOS = ("facebook.com", "instagram.com", "tiktok.com", "x.com", "twitter.com", "youtube.com", "linkedin.com/posts")

MESES_EN = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def html_to_text(raw):
    text = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def parse_devpost_end(dates):
    """'Oct 17 - 24, 2026' | 'Sep 30 - Nov 05, 2026' | 'Dec 15, 2026 - Jan 10, 2027' -> fecha final."""
    if not dates:
        return None
    end = dates.split("-")[-1].strip()
    m = re.match(r"(?:([A-Za-z]{3})[a-z]*\s+)?(\d{1,2}),\s*(\d{4})", end)
    if not m:
        return None
    month_txt = m.group(1)
    if not month_txt:
        start_month = re.match(r"([A-Za-z]{3})", dates.strip())
        month_txt = start_month.group(1) if start_month else None
    month = MESES_EN.get((month_txt or "").lower())
    if not month:
        return None
    try:
        return date(int(m.group(3)), month, int(m.group(2)))
    except ValueError:
        return None


def puntuar(reto):
    """Afinidad con el perfil: suma por cada tema que aparece en título, temas y descripción."""
    texto = " ".join(str(reto.get(k, "")) for k in ("titulo", "organizador", "descripcion")) + " " + " ".join(reto.get("temas", []))
    temas = [nombre for nombre, patron in TEMAS_PERFIL.items() if re.search(patron, texto, re.IGNORECASE)]
    reto["areas_perfil"] = temas
    if not re.search(r"[1-9]", str(reto.get("premio", ""))):
        reto["premio"] = ""
    score = 20 * len(temas)
    if reto.get("premio"):
        score += 10
    if reto.get("modalidad", "").startswith("Presencial"):
        score += 15  # eventos en Medellín: más fáciles de aprovechar
    if reto.get("pais") == "Colombia":
        score += 20
    if reto.get("apto_principiantes"):
        score += 5
    reto["score"] = score
    return reto


def scrape_devpost(max_pages=12):
    """Hackatones en línea abiertos o próximos en Devpost."""
    results = []
    for page in range(1, max_pages + 1):
        try:
            r = requests.get(
                "https://devpost.com/api/hackathons",
                params={"status[]": ["open", "upcoming"], "challenge_type[]": "online", "order_by": "deadline", "page": page},
                headers=HEADERS,
                timeout=12,
            )
            if r.status_code != 200:
                break
            hackathons = r.json().get("hackathons", [])
        except (requests.RequestException, ValueError):
            break
        if not hackathons:
            break
        for h in hackathons:
            if h.get("invite_only"):
                continue
            fin = parse_devpost_end(h.get("submission_period_dates", ""))
            themes = [t.get("name", "") for t in h.get("themes", []) if isinstance(t, dict)]
            results.append({
                "titulo": h.get("title", "").strip(),
                "organizador": (h.get("organization_name") or "").strip() or "Devpost",
                "plataforma": "Devpost",
                "tipo": "Hackatón",
                "modalidad": "En línea",
                "ubicacion": "En línea (internacional)",
                "pais": "Internacional",
                "url": h.get("url", ""),
                "fechas": h.get("submission_period_dates", ""),
                "fecha_cierre_iso": fin.isoformat() if fin else "",
                "premio": html_to_text(h.get("prize_amount", "")).replace(" ", ""),
                "temas": themes,
                "apto_principiantes": any("beginner" in t.lower() for t in themes),
                "inscritos": h.get("registrations_count"),
                "estado": "Abierto" if h.get("open_state") == "open" else "Próximamente",
                "fuente": "Devpost API",
            })
        time.sleep(0.4)
    return results


def scrape_zindi():
    """Competencias activas de ciencia de datos en Zindi (abiertas a todo el mundo)."""
    try:
        r = requests.get(
            "https://api.zindi.africa/v1/competitions",
            params={"per_page": 50, "active": "1", "kind": "competition"},
            headers=HEADERS,
            timeout=12,
        )
        data = r.json().get("data", []) if r.status_code == 200 else []
    except (requests.RequestException, ValueError):
        return []
    results = []
    for c in data:
        if c.get("is_access_restricted") or c.get("secret_code_required") or not c.get("open", True):
            continue
        fin = str(c.get("end_time") or "")[:10]
        results.append({
            "titulo": c.get("title", "").strip(),
            "organizador": (c.get("organization") or {}).get("name", "Zindi") if isinstance(c.get("organization"), dict) else "Zindi",
            "plataforma": "Zindi",
            "tipo": "Competencia de datos / IA",
            "modalidad": "En línea",
            "ubicacion": "En línea (internacional)",
            "pais": "Internacional",
            "url": f"https://zindi.africa/competitions/{c.get('id')}",
            "fechas": f"{str(c.get('start_time') or '')[:10]} a {fin}",
            "fecha_cierre_iso": fin,
            "premio": c.get("reward") or "",
            "temas": ["Ciencia de datos", "IA"],
            "apto_principiantes": bool(c.get("is_beginner_friendly")),
            "inscritos": c.get("participations_count"),
            "estado": "Abierto",
            "fuente": "Zindi API",
        })
    return results


def scrape_drivendata():
    """Competencias activas de DrivenData (ciencia de datos con impacto social)."""
    try:
        r = requests.get("https://www.drivendata.org/competitions/", headers=HEADERS, timeout=12)
        page = r.text if r.status_code == 200 else ""
    except requests.RequestException:
        return []
    results = []
    for attrs, body in re.findall(r'<div class="[^"]*panel-container active-comp[^"]*"([^>]*)>(.*?)panel-competition-title', page, re.DOTALL):
        if 'data-status_active="1"' not in attrs:
            continue
        link = re.search(r'href="(/competitions/\d+/[^"]+)"[^>]*title="([^"]+)"', body)
        if not link:
            continue
        deadline = re.search(r'data-deadline="-?1?(\d{8})"', attrs)
        fin = ""
        if deadline:
            d = deadline.group(1)
            fin = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        prize = re.search(r'data-total_prize_purse="([\d.]+)"', attrs)
        categorias = re.findall(r'data-category_([a-z_]+)="1"', attrs)
        results.append({
            "titulo": unescape(link.group(2)).strip(),
            "organizador": "DrivenData",
            "plataforma": "DrivenData",
            "tipo": "Competencia de datos / IA",
            "modalidad": "En línea",
            "ubicacion": "En línea (internacional; revisar elegibilidad de premios)",
            "pais": "Internacional",
            "url": "https://www.drivendata.org" + link.group(1),
            "fechas": f"Cierra {fin}" if fin else "",
            "fecha_cierre_iso": fin,
            "premio": f"${float(prize.group(1)):,.0f} USD" if prize and float(prize.group(1)) > 0 else "",
            "temas": [c.replace("_", " ") for c in categorias],
            "apto_principiantes": False,
            "estado": "Abierto",
            "fuente": "DrivenData",
        })
    return results


def scrape_web(query, alcance):
    """Retos en Colombia vía búsqueda web: son pistas y se marcan para verificar vigencia."""
    anio = date.today().year
    results = []
    for link, title, snippet in buscar_web(query):
        if any(d in link for d in WEB_DOMINIOS_EXCLUIDOS):
            continue
        evidencia = f"{title} {snippet}"
        if not RETO_RE.search(evidencia):
            continue
        # Descartar resultados que solo hablan de ediciones pasadas.
        anios = {int(a) for a in re.findall(r"\b(20\d\d)\b", evidencia)}
        if anios and max(anios) < anio:
            continue
        en_colombia = alcance == "Colombia"
        presencial_local = bool(LOCAL_RE.search(evidencia))
        results.append({
            "titulo": title,
            "organizador": urlparse(link).netloc.removeprefix("www."),
            "plataforma": "Búsqueda web",
            "tipo": "Hackatón" if re.search(r"hackat|hackathon", evidencia, re.IGNORECASE) else "Reto / convocatoria",
            "modalidad": "Presencial o en línea (confirmar)" if presencial_local else "Confirmar en la fuente",
            "ubicacion": "Medellín / Antioquia" if presencial_local else ("Colombia" if en_colombia else "Internacional"),
            "pais": "Colombia" if en_colombia else "Internacional",
            "url": link,
            "fechas": "Verificar vigencia en la fuente",
            "fecha_cierre_iso": "",
            "premio": "",
            "temas": [],
            "descripcion": snippet[:400],
            "estado": "Verificar vigencia",
            "fuente": f"Búsqueda web · {urlparse(link).netloc}",
        })
    return results


def en_alcance(reto):
    """En línea desde cualquier lugar; presencial solo en Medellín / Antioquia."""
    texto = f"{reto.get('modalidad', '')} {reto.get('ubicacion', '')}"
    return bool(ONLINE_RE.search(texto) or LOCAL_RE.search(texto) or "confirmar" in texto.lower())


def vigente(reto, hoy):
    fin = reto.get("fecha_cierre_iso")
    if not fin:
        return True
    try:
        return datetime.fromisoformat(fin).date() >= hoy
    except ValueError:
        return True


def main():
    print(encabezado_bot("[RETOS] BOT DE RETOS, HACKATONES Y COMPETENCIAS"))
    hoy = date.today()
    retos = []

    destacados = load_json(RETOS_DESTACADOS_PATH, [])
    for d in destacados:
        d = dict(d)
        d.setdefault("fuente", "Curado")
        d["curado"] = True
        retos.append(d)
    print(f"[*] Plataformas y programas curados: {len(destacados)}")

    for nombre, funcion in (("Devpost", scrape_devpost), ("Zindi", scrape_zindi), ("DrivenData", scrape_drivendata)):
        encontrados = funcion()
        print(f"[*] {nombre}: {len(encontrados)} oportunidades")
        retos.extend(encontrados)

    print(f"[*] Búsqueda web de retos en Colombia e internacionales ({len(WEB_QUERIES)} búsquedas)...")
    for query, alcance in WEB_QUERIES:
        encontrados = scrape_web(query, alcance)
        print(f"    '{query}': {len(encontrados)}")
        retos.extend(encontrados)


    unicos = {}
    for reto in retos:
        clave = re.sub(r"^https?://(www\.)?", "", str(reto.get("url", ""))).rstrip("/").lower()
        if not clave or clave in unicos:
            continue
        if TEMAS_FUERA.search(f"{reto.get('titulo', '')} {' '.join(reto.get('temas', []))}"):
            continue
        if not reto.get("curado") and not (en_alcance(reto) and vigente(reto, hoy)):
            continue
        unicos[clave] = puntuar(reto)

    final = sorted(
        unicos.values(),
        # Primero los retos abiertos ahora; las plataformas permanentes al final.
        key=lambda r: (bool(r.get("curado")), -r.get("score", 0), r.get("fecha_cierre_iso") or "9999"),
    )
    sellar_registros(final)
    if not [r for r in final if not r.get("curado")]:
        # Si todas las fuentes fallaron, conservar la última versión publicada.
        print(" [!] Ninguna fuente respondió; se conserva retos_hackatones.json anterior.")
        return
    with open(RETOS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f" [✓] {len(final)} retos y hackatones guardados en {RETOS_JSON_PATH}")


if __name__ == "__main__":
    main()
