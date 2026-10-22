"""
=============================================================================
PORTAL & BOT DE RASTREO DE PRÁCTICAS - INGENIERÍA FÍSICA (UNAL MEDELLÍN)
Autor: Jimmy Stebym Rosero Barrera
Descripción: Rastreador integral de convocatorias y vacantes para pregrado.
Prioriza automáticamente según el pénsum real de Ingeniería Física UNAL.
Incluye ícono de información [i] interactivo con nube flotante (tooltip).
(Cero emojis en la interfaz salvo el átomo superior)
=============================================================================
"""

import os
import sys
import json
import csv
import re
import time
from html import unescape
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
import requests

# Asegurar codificación UTF-8 en terminal de Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_RAMAS_PATH = os.path.join(BASE_DIR, "config_ramas.json")
CONVOCATORIAS_DESTACADAS_PATH = os.path.join(BASE_DIR, "convocatorias_destacadas.json")
OUTPUT_HTML = os.path.join(BASE_DIR, "dashboard_practicas.html")
OUTPUT_INDEX = os.path.join(BASE_DIR, "index.html")
OUTPUT_CSV = os.path.join(BASE_DIR, "vacantes_practicas.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "vacantes_practicas.json")

SEARCH_QUERIES = [
    # Tronco común y perfil UNAL Ingeniería Física
    "practicante ingenieria fisica",
    "practicante fisica",
    "estudiante ingenieria fisica pasantia",
    "intern engineering medellin",
    "practicante investigacion i+d",
    # Análisis de Datos, IA y Simulaciones
    "practicante datos",
    "practicante analitica",
    "practicante inteligencia artificial",
    "practicante python",
    "practicante machine learning",
    "practicante simulacion",
    # Electrónica Digital, Microcontroladores e IoT
    "practicante iot",
    "practicante embebidos",
    "practicante electronica digital",
    "practicante microcontroladores",
    # Electrónica Análoga y Circuitos
    "practicante electronica analoga",
    "practicante circuitos",
    # Instrumentación y Metrología Industrial
    "practicante instrumentacion",
    "practicante metrologia",
    "practicante automatizacion",
    # Diseño Mecánico y Dibujo Técnico
    "practicante diseno mecanico",
    "practicante cad solidworks",
    # Cuántica y Estado Sólido
    "practicante cuantica",
    "practicante semiconductores",
    # Física de Radiaciones y Física Médica
    "practicante radiaciones",
    "practicante fisica medica",
    # Óptica y Visión Artificial
    "practicante optica",
    "practicante vision artificial",
    # Ciencia de Materiales y Nanotecnología
    "practicante materiales",
    "practicante nanotecnologia",
    # Energía, Potencia y Renovables
    "practicante energia solar",
    "practicante protecciones electricas",
    "practicante potencia transformadores",
    # Mujeres en STEM
    "practicante mujeres stem",
    "programa mujer stem"
]

EXCLUDED_ROLES = [
    r"\brecepcionista\b",
    r"\benfermer[ao]\b",
    r"\brecursos\s+humanos\b",
    r"\btalento\s+humano\b",
    r"\bpsicolog[ao]\b",
    r"\blibranza\b",
    r"\bturismo\b",
    r"\babogad[ao]\b",
    r"\bderecho\b",
    r"\bcontabilidad\b",
    r"\bcontable\b",
    r"\boperario\s+(?:de\s+)?empaque\b",
    r"\bcajer[ao]\b",
    r"\bcocina\b",
    r"\bmeser[ao]\b",
    r"\basesor[a]?\s+comercial\b",
    r"\bejecutiv[ao]\s+comercial\b",
    r"\bvendedor[a]?\b",
    r"\bcall\s+center\b",
    r"\bcobranza\b"
]

TERMINOS_MUJERES_RE = re.compile(r'\b(mujer|mujeres|women|women in tech|femenin[ao]?|stem)\b', re.IGNORECASE)
TERMINOS_FISICA_RE = re.compile(r'\b(f[ií]sic[ao]s?|metrolog[ií]a|cu[aá]ntic[ao]s?|espectroscop[ií]a|difracci[oó]n|radiaci[oó]n|dosimetr[ií]a|nanotecnolog[ií]a)\b', re.IGNORECASE)

def matches_keyword(keyword, text):
    """Verifica si una palabra clave coincide respetando límites de palabra para términos cortos."""
    kw_clean = keyword.strip().lower()
    if len(kw_clean) <= 4 or kw_clean in ["stem", "datos", "data", "cad", "ia", "ai", "pcb", "daq", "plc", "gum", "iot", "spi", "i2c", "sql", "sem", "drx"]:
        return bool(re.search(r'(?:\b|_)' + re.escape(kw_clean) + r'(?:\b|_)', text, re.IGNORECASE))
    return kw_clean in text.lower()

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def scrape_linkedin_query(query, location="Medellin, Antioquia, Colombia"):
    """Consulta la API pública guest de LinkedIn Jobs para Medellín y Antioquia"""
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={quote(query)}&location={quote(location)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return []
        
        cards = re.findall(r'<div class="base-card[^"]*"[^>]*>(.*?)</li>', r.text, re.DOTALL)
        results = []
        for card in cards:
            title_m = re.search(r'<h3[^>]*class="[^"]*base-search-card__title[^"]*"[^>]*>\s*([^<]+)\s*</h3>', card)
            comp_m = re.search(r'<h4[^>]*class="[^"]*base-search-card__subtitle[^"]*"[^>]*>.*?<a[^>]*>\s*([^<]+)\s*</a>', card, re.DOTALL)
            if not comp_m:
                comp_m = re.search(r'<h4[^>]*class="[^"]*base-search-card__subtitle[^"]*"[^>]*>\s*([^<]+)\s*</h4>', card)
            loc_m = re.search(r'<span[^>]*class="[^"]*job-search-card__location[^"]*"[^>]*>\s*([^<]+)\s*</span>', card)
            link_m = re.search(r'<a[^>]*class="[^"]*base-card__full-link[^"]*"[^>]*href="([^"]+)"', card)
            date_m = re.search(r'<time[^>]*datetime="([^"]+)"[^>]*>\s*([^<]+)\s*</time>', card)
            
            title = title_m.group(1).strip() if title_m else ""
            company = comp_m.group(1).strip() if comp_m else "Empresa Confidencial"
            loc = loc_m.group(1).strip() if loc_m else "Medellín, Antioquia"
            link = link_m.group(1).split("?")[0] if link_m else ""
            pub_date = date_m.group(2).strip() if date_m else "Reciente"
            
            if title and link:
                results.append({
                    "titulo": title,
                    "empresa": company,
                    "ubicacion": loc,
                    "url": link,
                    "fecha_publicacion": pub_date,
                    "fuente": "LinkedIn Jobs"
                })
        return results
    except Exception as e:
        return []

def scrape_computrabajo_query(query):
    """Consulta convocatorias de prácticas en Computrabajo Antioquia"""
    url = f"https://co.computrabajo.com/empleos-en-antioquia?q={quote(query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return []
        offers = re.findall(r'<article[^>]*id="([^"]+)"[^>]*>(.*?)</article>', r.text, re.DOTALL)
        results = []
        for oid, content in offers:
            t_m = re.search(r'<a class="js-o-link fc_base"[^>]*href="([^"]+)"[^>]*>\s*([^<]+)\s*</a>', content)
            if not t_m:
                continue
            href = "https://co.computrabajo.com" + t_m.group(1).split("#")[0]
            title = unescape(t_m.group(2).strip())
            c_m = re.search(r'offer-grid-article-company-url[^>]*>\s*([^<]+)\s*</a>', content)
            comp = unescape(c_m.group(1).strip()) if c_m else "Empresa Confidencial"
            loc_m = re.search(r'<p class="fs16 fc_base mt5">\s*<span[^>]*>\s*([^<]+)\s*</span>', content)
            loc = unescape(loc_m.group(1).strip()) if loc_m else "Medellín, Antioquia"
            results.append({
                "titulo": title,
                "empresa": comp,
                "ubicacion": loc,
                "url": href,
                "fecha_publicacion": "Reciente",
                "fuente": "Computrabajo"
            })
        return results
    except Exception:
        return []

def scrape_magneto_query(query):
    """Consulta convocatorias de prácticas en la API pública de Magneto365 en Antioquia/Remoto."""
    api_url = "https://api.magneto365.com/jobs/v1/public/jobs/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.magneto365.com",
        "Referer": "https://www.magneto365.com/",
        "Accept": "application/json, text/plain, */*"
    }
    params = {
        "device": "desktop",
        "paginator[page]": 1,
        "paginator[pageSize]": 20,
        "order[field]": "publish_date",
        "order[order]": "DESC",
        "queries[0][field]": "all",
        "queries[0][term]": query,
        "country": "co"
    }
    antioquia_cities = {
        "medellín", "medellin", "envigado", "itagüí", "itagui", "bello", "sabaneta",
        "la estrella", "copacabana", "girardota", "caldas", "barbosa", "rionegro",
        "guarne", "marinilla", "apartadó", "apartado", "cisneros", "antioquia",
        "retiro", "el retiro", "el carmen de viboral", "carmen de viboral", "puerto berrío"
    }
    try:
        r = requests.get(api_url, params=params, headers=headers, timeout=6)
        if r.status_code != 200:
            return []
        data = r.json()
        rows = data.get("rows", [])
        results = []
        for row in rows:
            slug = row.get("jobSlug")
            title = (row.get("title") or "").strip()
            if not slug or not title:
                continue

            cities = row.get("cities") or []
            if isinstance(cities, list):
                city_str = ", ".join(cities)
                city_lower_list = [c.lower() for c in cities]
            else:
                city_str = str(cities)
                city_lower_list = [city_str.lower()]

            is_remote = bool(row.get("isRemote"))
            is_antioquia = any(any(ac in c for ac in antioquia_cities) for c in city_lower_list)

            # Aceptar si es en Antioquia, remoto, o programa multiciudad que incluye Antioquia
            if not (is_antioquia or is_remote):
                continue

            empresa = (row.get("companyName") or "Empresa Confidencial").strip()
            url = f"https://www.magneto365.com/co/empleos/{slug}"

            salary = row.get("salary") or 0
            comp = f"${salary:,.0f} COP".replace(",", ".") if salary and salary > 0 else ""

            pub_date = row.get("publishDate") or "Reciente"
            if "T" in pub_date:
                pub_date = pub_date.split("T")[0]

            raw_desc = row.get("description") or ""
            desc = re.sub(r'<[^>]+>', ' ', raw_desc)
            desc = re.sub(r'\s+', ' ', desc).strip()

            skills = row.get("skills") or []
            skills_names = [s.get("name") for s in skills if isinstance(s, dict) and s.get("name")]
            perfil = ", ".join(skills_names[:5]) if skills_names else ""

            results.append({
                "titulo": title,
                "empresa": empresa,
                "ubicacion": city_str if city_str else "Medellín / Antioquia",
                "url": url,
                "fecha_publicacion": pub_date,
                "fuente": "Magneto365",
                "compensacion": comp,
                "perfil": perfil,
                "mision": desc[:250] if desc else ""
            })
        return results
    except Exception:
        return []

def scrape_web_query(query):
    """Busca resultados web públicos con timeout corto para no congelar la ejecución."""
    url = f"https://html.duckduckgo.com/html/?q={quote(query + ' Medellín Antioquia empleo práctica')}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=4)
        if response.status_code != 200:
            return []
        results = []
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', response.text, re.DOTALL)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</', response.text, re.DOTALL)
        for index, (link, raw_title) in enumerate(links):
            if "uddg=" in link:
                m_uddg = re.search(r'[?&]uddg=([^&]+)', link)
                if m_uddg:
                    link = unquote(m_uddg.group(1))
            title = re.sub(r'<[^>]+>', ' ', unescape(raw_title))
            title = re.sub(r'\s+', ' ', title).strip()
            raw_snippet = snippets[index] if index < len(snippets) else ""
            snippet = re.sub(r'<[^>]+>', ' ', unescape(raw_snippet))
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            if not re.search(r'practic|práctic|estudian|ingenier|vacante|empleo|aprendiz|talento|convocatoria', f"{title} {snippet}", re.IGNORECASE):
                continue
            if title and link.startswith("http"):
                company_match = re.search(r'"([^"]+)"', query)
                results.append({
                    "titulo": title,
                    "empresa": company_match.group(1) if company_match else "Por identificar",
                    "ubicacion": "Medellín / Antioquia (verificar en la oferta)",
                    "url": link,
                    "fecha_publicacion": "Resultado web; verificar vigencia",
                    "fuente": f"Búsqueda web · {urlparse(link).netloc}",
                    "resumen_fuente": snippet
                })
        return results
    except Exception:
        return []

def classify_and_score_job(job, config_ramas):
    """Calcula el Score de Afinidad con el Pénsum UNAL con priorización y filtrado de roles no técnicos."""
    title_lower = job.get("titulo", "").lower()
    company_lower = job.get("empresa", "").lower()
    text_to_analyze = f"{title_lower} {company_lower}"

    # Descartar roles abiertamente no técnicos / administrativos de servicio que se cuelan en búsquedas amplias
    if any(re.search(p, title_lower) for p in EXCLUDED_ROLES):
        return None

    # Detección de programas especiales (con límites de palabra para evitar falsos positivos como 'systems' -> 'stem')
    es_impulso_liderazgo = bool(TERMINOS_MUJERES_RE.search(text_to_analyze))
    es_exclusiva_fisica = bool(TERMINOS_FISICA_RE.search(text_to_analyze))

    es_cierre_inminente = False
    pub_lower = job.get("fecha_publicacion", "").lower()
    if any(k in pub_lower for k in ["hora", "horas", "1 día", "2 días", "3 días", "4 días", "5 días", "hace 1", "hace 2"]):
        es_cierre_inminente = True
    elif "urgente" in text_to_analyze or "pipeline" in text_to_analyze:
        es_cierre_inminente = True

    total_score = 0
    if es_impulso_liderazgo:
        total_score += 160
    if es_exclusiva_fisica:
        total_score += 85

    ramas_coincidentes = []
    max_rama_score = 0
    mision_especifica = ""
    tareas_especificas = ""

    for rama_key, data in config_ramas.get("ramas", {}).items():
        if rama_key == "mujeres_stem":
            continue

        kw_hits = 0
        palabras = data.get("palabras_clave", [])
        for p in palabras:
            if matches_keyword(p, text_to_analyze):
                kw_hits += 1

        # Solo se considera rama afín si coincide al menos una palabra clave técnica real
        if kw_hits > 0:
            score = kw_hits * 3
            empresas_ref = [e.lower() for e in data.get("empresas_referencia", [])]
            for e in empresas_ref:
                if e in company_lower:
                    score += 4

            bonus = data.get("prioridad_bonus", 20)
            score += bonus
            ramas_coincidentes.append({
                "clave": rama_key,
                "nombre": data["nombre"],
                "color": data["color"],
                "score": score
            })
            if score > max_rama_score:
                max_rama_score = score
                mision_especifica = data.get("mision_tipica", "")
                tareas_especificas = data.get("actividades_clave", "")

    total_score += max_rama_score
    ramas_coincidentes.sort(key=lambda x: x["score"], reverse=True)

    if not ramas_coincidentes:
        ramas_coincidentes.append({
            "clave": "general",
            "nombre": "Ingeniería General / Operaciones",
            "color": "#64748b",
            "score": 5
        })
        afinidad = "General"
        mision_especifica = f"Apoyo en el área de ingeniería y operaciones técnicas en {job.get('empresa', 'la compañía')}."
        tareas_especificas = "Seguimiento de indicadores técnicos, soporte en optimización de procesos y documentación técnica de proyectos."
    elif es_exclusiva_fisica:
        afinidad = "Exclusiva Física"
    elif max_rama_score >= 50 or es_impulso_liderazgo:
        afinidad = "Alta Afinidad Pénsum"
    else:
        afinidad = "Afinidad Media"

    # Bonificación especial si es convocatoria verificada de alto impacto
    if job.get("compensacion"):
        total_score += 35

    job["ramas"] = ramas_coincidentes
    job["rama_principal"] = ramas_coincidentes[0]["nombre"]
    job["color_principal"] = ramas_coincidentes[0]["color"]
    job["clave_principal"] = ramas_coincidentes[0]["clave"]
    job["afinidad"] = afinidad
    job["es_exclusiva_fisica"] = es_exclusiva_fisica
    job["es_cierre_inminente"] = es_cierre_inminente
    job["score_pensum"] = total_score
    job["mision"] = job.get("mision") or job.get("resumen_fuente") or mision_especifica or f"Desarrollo de proyectos técnicos y operativos en {job.get('empresa', 'la empresa')}."
    job["tareas"] = job.get("tareas") or (tareas_especificas if tareas_especificas else "Apoyo en mediciones, modelado técnico, análisis de datos y reporte de resultados.")
    if job.get("resumen_fuente") and not job.get("tareas"):
        job["tareas"] = "Resumen de búsqueda web. Abre la publicación original para confirmar funciones, requisitos y vigencia."

    return job

def build_full_html(vacantes, config_ramas):
    """Genera el portal responsive para Ingeniería Física y conserva la página de GitHub Pages."""
    total_exclusivas = sum(1 for v in vacantes if v.get("es_exclusiva_fisica"))
    total_inminentes = sum(1 for v in vacantes if v.get("es_cierre_inminente"))
    vacantes_json = json.dumps(vacantes, ensure_ascii=False).replace("<", "\\u003c")

    html = f"""<!DOCTYPE html>
<html lang="es" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#f5f4ee">
  <meta name="description" content="Convocatorias de prácticas en Medellín y Antioquia, seleccionadas para Ingeniería Física. Explora vacantes, guarda tus postulaciones y conecta el pénsum con la industria.">
  <meta name="author" content="Jimmy Stebym Rosero Barrera">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%23173f39'/%3E%3Ctext x='50' y='72' text-anchor='middle' font-size='66' fill='%23d9f275' font-family='sans-serif'%3Eφ%3C/text%3E%3C/svg%3E">
  <title>Prácticas de Ingeniería Física | UNAL Medellín</title>
  <script>
    try {{
      const savedTheme = localStorage.getItem('ipf-theme');
      document.documentElement.dataset.theme = savedTheme === 'dark' || savedTheme === 'light' ? savedTheme : (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    }} catch {{}}
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="estilos.css">
  <script id="jobs-data" type="application/json">{vacantes_json}</script>
  <script src="app.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#contenido">Saltar al contenido</a>
  <header class="site-header">
    <a class="brand" href="#inicio" aria-label="Ingeniería Física, inicio">
      <span class="brand-mark" aria-hidden="true"><span>φ</span></span>
      <span class="brand-lockup"><strong>INGENIERÍA FÍSICA</strong><small>UNAL · MEDELLÍN</small></span>
    </a>
    <div class="header-actions">
      <span class="open-status"><span class="status-dot" aria-hidden="true"></span>Radar de oportunidades</span>
      <button class="theme-toggle" id="themeToggle" type="button" aria-pressed="false"><span class="theme-icon" aria-hidden="true">◐</span><span class="theme-label">Tema oscuro</span></button>
    </div>
  </header>

  <main id="contenido">
    <section class="hero" id="inicio" aria-labelledby="hero-title">
      <div class="hero-copy">
        <p class="eyebrow"><span class="eyebrow-rule" aria-hidden="true"></span>DE LA UNIVERSIDAD A LA INDUSTRIA</p>
        <h1 id="hero-title">La física también <em>se pone a trabajar.</em></h1>
        <p class="hero-description">Oportunidades donde lo que sabes de datos, materiales, electrónica y energía encuentra problemas reales que resolver.</p>
        <div class="hero-actions">
          <a class="button button-primary" href="#vacantes">Explorar oportunidades <span aria-hidden="true">↘</span></a>
          <button class="button button-quiet" type="button" data-open-guide>Ver guía de postulación <span aria-hidden="true">↗</span></button>
        </div>
        <p class="hero-signature">Hecho por un ingeniero físico, para quienes vienen detrás.</p>
      </div>
      <div class="hero-visual" aria-label="Áreas de aplicación de la ingeniería física">
        <div class="visual-topline"><span>CAMPO DE ACCIÓN</span><span>MEDELLÍN · 6°14′N</span></div>
        <div class="orbit-scene" aria-hidden="true">
          <span class="orbit orbit-one"></span><span class="orbit orbit-two"></span><span class="orbit orbit-three"></span>
          <span class="orbit-core">φ</span><span class="orbit-node node-one">λ</span><span class="orbit-node node-two">∿</span><span class="orbit-node node-three">+</span>
          <span class="axis axis-x"></span><span class="axis axis-y"></span>
        </div>
        <div class="visual-caption"><span>TEORÍA <i></i> MEDICIÓN <i></i> IMPACTO</span><span class="visual-index">01 — ∞</span></div>
        <div class="hero-note"><span class="note-symbol" aria-hidden="true">↗</span><span><strong>Tu pénsum sí tiene lugar.</strong><small>Encuentra dónde aplicarlo.</small></span></div>
      </div>
      <div class="hero-index" aria-hidden="true">IPF / 01</div>
    </section>

    <section class="signal-strip" aria-label="Resumen de convocatorias">
      <p><span class="signal-icon" aria-hidden="true">↗</span> CONVOCATORIAS PARA EL VALLE DE ABURRÁ</p>
      <div class="signal-stats">
        <span><strong id="activeCount">{len(vacantes)}</strong> oportunidades</span><b aria-hidden="true">/</b>
        <span><strong id="exclusiveCount">{total_exclusivas}</strong> afines a física</span><b aria-hidden="true">/</b>
        <span><strong id="urgentCount">{total_inminentes}</strong> por cerrar</span>
      </div>
    </section>

    <section class="opportunities" id="vacantes" aria-labelledby="section-title">
      <div class="section-heading">
        <div><p class="eyebrow eyebrow-dark">EL SIGUIENTE PASO</p><h2 id="section-title">Encuentra tu lugar.</h2></div>
        <p class="section-aside">Filtra por afinidad, explora las áreas<br class="desktop-break"> y guarda las postulaciones que te interesan.</p>
      </div>
      <div class="tabs-shell">
        <div class="tabs-nav" role="tablist" aria-label="Secciones de convocatorias">
          <button class="tab-link active" id="tab-todas" type="button" role="tab" aria-selected="true" aria-controls="jobsPanel" tabindex="0" data-tab="todas">Todas <span>{len(vacantes)}</span></button>
          <button class="tab-link" id="tab-exclusivas" type="button" role="tab" aria-selected="false" aria-controls="jobsPanel" tabindex="-1" data-tab="exclusivas">Afinidad física <span>{total_exclusivas}</span></button>
          <button class="tab-link" id="tab-inminentes" type="button" role="tab" aria-selected="false" aria-controls="jobsPanel" tabindex="-1" data-tab="inminentes">Cierre próximo <span>{total_inminentes}</span></button>
          <button class="tab-link" id="tab-consejos" type="button" role="tab" aria-selected="false" aria-controls="guidePanel" tabindex="-1" data-tab="consejos">Guía de postulación <span aria-hidden="true">↗</span></button>
        </div>
      </div>

      <div id="jobsPanel" role="tabpanel" aria-labelledby="tab-todas" tabindex="0">
        <div class="filter-panel" id="filterControls">
          <label class="search-field"><span class="search-icon" aria-hidden="true">⌕</span><span class="sr-only">Buscar oportunidades</span><input type="search" id="searchInput" placeholder="Busca una tecnología, empresa o materia…" autocomplete="off"><kbd>/</kbd></label>
          <label class="application-filter"><span class="sr-only">Filtrar por estado de postulación</span><select id="applicationFilter"><option value="all">Todas mis vacantes</option><option value="pending">Pendientes</option><option value="applied">Ya postuladas</option></select><span class="select-chevron" aria-hidden="true">⌄</span></label>
        </div>
        <div class="branch-pills" id="pillsContainer" aria-label="Filtrar por área">
          <button class="branch-pill active" type="button" aria-pressed="true" data-branch="TODOS">Todas las áreas</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Análisis de Datos, IA y Simulaciones">Datos e IA</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Electrónica Digital, Microcontroladores e IoT">Electrónica digital</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Electrónica Análoga y Circuitos">Electrónica análoga</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Instrumentación y Metrología Industrial">Instrumentación</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Diseño Mecánico y Dibujo Técnico">Diseño mecánico</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Cuántica, Estado Sólido y Nuevas Tecnologías">Cuántica</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Física de Radiaciones y Física Médica">Física médica</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Óptica, Fotónica y Visión Artificial">Óptica y fotónica</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Ciencia de Materiales y Nanotecnología">Materiales</button>
          <button class="branch-pill" type="button" aria-pressed="false" data-branch="Energía, Potencia y Renovables">Energía</button>
        </div>
        <div class="results-heading"><p id="resultsCount" role="status" aria-live="polite">Cargando convocatorias…</p><p id="applicationSummary"></p></div>
        <div class="jobs-grid" id="jobsContainer" aria-busy="false"></div>
      </div>

      <section class="guide-panel" id="guidePanel" role="tabpanel" aria-labelledby="tab-consejos" tabindex="0" hidden>
        <div class="guide-intro"><p class="eyebrow eyebrow-dark">TRADUCE LO QUE SABES</p><h2>La ingeniería física<br><em>habla muchos idiomas.</em></h2><p>Ayuda al equipo de selección a ver cómo tu formación resuelve sus retos. Nombra herramientas, proyectos y resultados concretos.</p></div>
        <div class="guide-grid">
          <article class="guide-card"><span class="guide-number">01 / PERFIL</span><h3>Cuenta lo que sabes hacer</h3><p>Instrumentación, adquisición de datos, microcontroladores, automatización, Python, MATLAB o caracterización de materiales: pon tus habilidades técnicas en el primer tercio de la hoja de vida.</p></article>
          <article class="guide-card"><span class="guide-number">02 / PROYECTOS</span><h3>Vuelve visible el pénsum</h3><p>Un proyecto de Taller V con ESP32, una curva de calibración en LabVIEW o una simulación numérica cuentan una historia más clara que una lista de asignaturas.</p></article>
          <article class="guide-card"><span class="guide-number">03 / POSTULACIÓN</span><h3>Aplica a perfiles afines</h3><p>Si piden electrónica, mecatrónica, materiales o áreas afines, explica tu enfoque: sistemas embebidos, análisis de datos, potencia o física médica.</p></article>
          <article class="guide-card guide-card-accent"><span class="guide-number">EL MOMENTO</span><h3>Anticipa las convocatorias.</h3><p>Prácticas de enero a junio: suele haber aperturas entre septiembre y noviembre. Para julio a diciembre, revisa desde marzo hasta mayo.</p></article>
        </div>
        <button class="button button-primary guide-back" type="button" data-back-to-jobs>Volver a las oportunidades <span aria-hidden="true">↗</span></button>
      </section>
    </section>
  </main>

  <footer class="site-footer"><a class="footer-brand" href="#inicio">φ <span>Ingeniería Física · UNAL Medellín</span></a><p>Una iniciativa independiente de Jimmy Stebym Rosero Barrera.</p><a class="back-top" href="#inicio">Volver arriba ↑</a></footer>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    with open(OUTPUT_INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f" [✓] Archivos HTML generados: {OUTPUT_HTML} y {OUTPUT_INDEX}")

def export_csv(vacantes):
    """Exporta las vacantes ordenadas a CSV para Excel"""
    fieldnames = ["titulo", "empresa", "ubicacion", "rama_principal", "afinidad", "score_pensum", "es_exclusiva_fisica", "es_cierre_inminente", "compensacion", "perfil", "mision", "tareas", "fecha_publicacion", "fuente", "url"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for v in vacantes:
            writer.writerow({
                "titulo": v["titulo"],
                "empresa": v["empresa"],
                "ubicacion": v["ubicacion"],
                "rama_principal": v["rama_principal"],
                "afinidad": v["afinidad"],
                "score_pensum": v.get("score_pensum", 0),
                "es_exclusiva_fisica": v.get("es_exclusiva_fisica", False),
                "es_cierre_inminente": v.get("es_cierre_inminente", False),
                "compensacion": v.get("compensacion", ""),
                "perfil": v.get("perfil", ""),
                "mision": v.get("mision", ""),
                "tareas": v.get("tareas", ""),
                "fecha_publicacion": v["fecha_publicacion"],
                "fuente": v["fuente"],
                "url": v["url"]
            })
    print(f" [✓] Archivo Excel/CSV generado: {OUTPUT_CSV}")

def main():
    print("="*70)
    print(" [ATOM] BOT DE RASTREO INTEGRAL - PRÁCTICAS DE INGENIERÍA FÍSICA")
    print("        Medellín, Valle de Aburrá & Antioquia • Autor: Jimmy Rosero")
    print("="*70)
    
    config_ramas = load_json(CONFIG_RAMAS_PATH)
    all_raw_jobs = []
    seen_urls = set()
    
    # 1. Cargar convocatorias destacadas verificadas (Magneto365, Jooble, Portales corporativos, Computrabajo)
    convocatorias_destacadas = load_json(CONVOCATORIAS_DESTACADAS_PATH)
    if isinstance(convocatorias_destacadas, list):
        print(f"[*] Cargando {len(convocatorias_destacadas)} convocatorias verificadas (Magneto365, Jooble, Portales de Antioquia)...")
        for c in convocatorias_destacadas:
            if c.get("url") and c["url"] not in seen_urls:
                seen_urls.add(c["url"])
                all_raw_jobs.append(c)

    # 2. Rastrear Computrabajo Antioquia
    computrabajo_queries = [
        "practicante ingenieria",
        "practicante electronica",
        "practicante mantenimiento",
        "practicante automatizacion",
        "practicante datos",
        "practicante electromecanico",
        "practicante instrumentacion",
        "practicante metrologia"
    ]
    print(f"\n[*] Rastreando Computrabajo Antioquia ({len(computrabajo_queries)} categorías)...")
    for q_ct in computrabajo_queries:
        ct_jobs = scrape_computrabajo_query(q_ct)
        added_ct = 0
        for j in ct_jobs:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_raw_jobs.append(j)
                added_ct += 1
        if added_ct > 0:
            print(f"    Computrabajo '{q_ct}': +{added_ct} ofertas")
        time.sleep(0.3)

    # 3. Rastrear Magneto365 en tiempo real (API Pública Oficial)
    magneto_queries = [
        "practicante ingenieria",
        "practica ingenieria",
        "practicante ingenieria fisica",
        "practicante electronica",
        "practicante automatizacion",
        "practicante mecatronica",
        "practicante datos",
        "practicante mantenimiento",
        "practica profesional corona",
        "practicante isa",
        "practicante epm",
        "practicante haceb"
    ]
    print(f"\n[*] Rastreando Magneto365 en tiempo real ({len(magneto_queries)} categorías)...")
    for q_mag in magneto_queries:
        mag_jobs = scrape_magneto_query(q_mag)
        added_mag = 0
        for j in mag_jobs:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_raw_jobs.append(j)
                added_mag += 1
        if added_mag > 0:
            print(f"    Magneto365 '{q_mag}': +{added_mag} ofertas")
        time.sleep(0.3)

    # 4. Rastrear LinkedIn Jobs para categorías del pénsum UNAL
    print(f"\n[*] Rastreando LinkedIn Jobs para {len(SEARCH_QUERIES)} categorías del pénsum UNAL...")
    for q in SEARCH_QUERIES:
        print(f" -> Buscando: '{q}'...")
        jobs = scrape_linkedin_query(q)
        added = 0
        for j in jobs:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_raw_jobs.append(j)
                added += 1
        print(f"    Encontradas {len(jobs)} ofertas (+{added} nuevas)")
        time.sleep(0.3)

    # 5. Rastrear convocatorias de practicantes en empresas líderes de Medellín y Antioquia
    company_directory = load_json(os.path.join(BASE_DIR, "empresas_antioquia.json"))
    top_companies = [item.get("empresa") for item in company_directory if isinstance(item, dict) and item.get("empresa")]
    top_companies.extend(["Haceb", "Corona", "ISA", "Sura", "Bancolombia", "Argos", "EPM", "CIDET", "XM", "Ruta N", "Mineros S.A.", "Continental Gold"])
    top_companies = list(dict.fromkeys(name.strip() for name in top_companies if name and name.strip()))

    print(f"\n[*] Rastreando vacantes en {len(top_companies)} empresas de Antioquia en LinkedIn...")
    for comp in top_companies:
        q_comp = f"practicante {comp}"
        jobs = scrape_linkedin_query(q_comp)
        added = 0
        for j in jobs:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_raw_jobs.append(j)
                added += 1
        if added > 0:
            print(f"    {comp:25s}: +{added} ofertas")
        time.sleep(0.2)
        
    print(f"\n[*] Total de vacantes únicas recolectadas: {len(all_raw_jobs)}")
    print("[*] Clasificando, filtrando y ordenando por afinidad al pénsum UNAL...")
    
    classified_jobs = []
    for j in all_raw_jobs:
        classified = classify_and_score_job(j, config_ramas)
        if classified:
            classified_jobs.append(classified)
        
    # Ordenar por Score de Afinidad del Pénsum
    classified_jobs.sort(key=lambda x: x.get("score_pensum", 0), reverse=True)
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(classified_jobs, f, ensure_ascii=False, indent=2)
    print(f" [✓] Datos JSON guardados en: {OUTPUT_JSON} ({len(classified_jobs)} vacantes afines)")
    
    export_csv(classified_jobs)
    build_full_html(classified_jobs, config_ramas)
    
    print("\n" + "="*70)
    print(" ¡RASTREO Y ACTUALIZACIÓN COMPLETADOS EXITOSAMENTE!")
    print(f" Dashboard listo para abrir:")
    print(f" {Path(OUTPUT_INDEX).as_uri()}")
    print("="*70)

if __name__ == "__main__":
    main()
