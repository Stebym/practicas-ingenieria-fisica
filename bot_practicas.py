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

def scrape_elempleo_query(query):
    """Consulta ofertas de prácticas de ingeniería en ElEmpleo.com para Antioquia y nacional."""
    url = f"https://www.elempleo.com/co/ofertas-empleo/antioquia?trabajo={quote(query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return []
        items = re.findall(r'data-ga4-offerdata="([^"]+)"', r.text)
        urls = re.findall(r'data-url="([^"]+)"', r.text)
        results = []
        seen = set()
        for raw_json, raw_url in zip(items, urls):
            try:
                data = json.loads(unescape(raw_json))
                clean_url = "https://www.elempleo.com" + raw_url.split("?")[0]
                if clean_url in seen:
                    continue
                seen.add(clean_url)
                title = data.get("title", "").strip()
                company = data.get("company", "").strip() or "Empresa Confidencial"
                loc = data.get("location", "").strip() or "Medellín / Antioquia"
                sal = data.get("salary", "").strip()
                comp = sal if sal and "confidencial" not in sal.lower() else ""

                if title and clean_url:
                    results.append({
                        "titulo": title,
                        "empresa": company,
                        "ubicacion": loc,
                        "url": clean_url,
                        "fecha_publicacion": "Reciente",
                        "fuente": "ElEmpleo.com",
                        "compensacion": comp
                    })
            except Exception:
                continue
        return results
    except Exception:
        return []

def scrape_firstjob_query(query):
    """Consulta convocatorias de prácticas y semilleros en FirstJob Colombia."""
    url = f"https://firstjob.me/ofertas?country[]=47&title={quote(query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return []
        cards = re.findall(r'<div class="card-job[^>]*>.*?<a href="(/oferta/[^"]+)".*?<h6[^>]*>([^<]+)</h6>.*?<span class="card-job-top--company[^"]*">([^<]+)</span>', r.text, re.DOTALL)
        results = []
        for link, raw_title, raw_comp in cards:
            title = re.sub(r'<[^>]+>', '', raw_title).strip()
            comp = re.sub(r'<[^>]+>', '', raw_comp).strip()
            url_job = "https://firstjob.me" + link
            results.append({
                "titulo": title,
                "empresa": comp,
                "ubicacion": "Colombia / Remoto",
                "url": url_job,
                "fecha_publicacion": "Reciente",
                "fuente": "FirstJob",
                "compensacion": ""
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
    perfil_lower = job.get("perfil", "").lower()
    mision_lower = job.get("mision", "").lower()
    text_to_analyze = f"{title_lower} {company_lower} {perfil_lower} {mision_lower}"

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
    """Genera el HTML semántico con diseño de laboratorio, blindaje XSS y estética de vanguardia"""
    vacantes_json_str = json.dumps(vacantes, ensure_ascii=False)
    
    convenios_path = os.path.join(BASE_DIR, "convenios_internacionales.json")
    becas_path = os.path.join(BASE_DIR, "becas_internacionales.json")
    convenios_data = load_json(convenios_path) if os.path.exists(convenios_path) else []
    becas_data = load_json(becas_path) if os.path.exists(becas_path) else []
    
    convenios_json_str = json.dumps(convenios_data, ensure_ascii=False)
    becas_json_str = json.dumps(becas_data, ensure_ascii=False)

    total_exclusivas = sum(1 for v in vacantes if v.get("es_exclusiva_fisica"))
    total_inminentes = sum(1 for v in vacantes if v.get("es_cierre_inminente"))
    total_convenios = len(convenios_data)
    total_becas = len(becas_data)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prácticas de Ingeniería Física • UNAL Medellín | Jimmy Rosero</title>
  <meta name="description" content="Portal inteligente de convocatorias de prácticas profesionales, pasantías y becas internacionales para estudiantes de Ingeniería Física de la Universidad Nacional de Colombia Sede Medellín. Creado por Jimmy Stebym Rosero Barrera.">
  <meta name="author" content="Jimmy Stebym Rosero Barrera">
  <meta name="color-scheme" content="light dark">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta http-equiv="X-Content-Type-Options" content="nosniff">
  
  <!-- OpenGraph y Metadatos para compartir en Redes y WhatsApp -->
  <meta property="og:title" content="Prácticas de Ingeniería Física • UNAL Medellín | Jimmy Rosero">
  <meta property="og:description" content="Radar inteligente de convocatorias de prácticas clasificadas por materias del pénsum y más de 1.150 convenios internacionales de la UNAL.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://stebym.github.io/practicas-ingenieria-fisica/">

  <!-- Favicon cuántico en formato SVG puro -->
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚛️</text></svg>">

  <script>
    try {{
      const storedTheme = localStorage.getItem('ipf-theme');
      const savedTheme = storedTheme === 'dark' || storedTheme === 'light' ? storedTheme : null;
      const preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      document.documentElement.dataset.theme = savedTheme || preferredTheme;
    }} catch {{ document.documentElement.dataset.theme = 'light'; }}
  </script>
  <link rel="stylesheet" href="estilos.css">
  <script src="estrellas.js" defer></script>
</head>
<body>
  <canvas id="constellationCanvas" aria-hidden="true"></canvas>

  <!-- HEADER SEMÁNTICO CON TELEMETRÍA Y BRANDING -->
  <header class="site-header">
    <div class="header-container">
      <div class="branding">
        <div class="brand-symbol" title="Ingeniería Física UNAL">⚛</div>
        <div class="brand-text">
          <h1>Prácticas de Ingeniería Física</h1>
          <p class="subtitle">Medellín y Antioquia • Convocatorias Industriales & Directorio de I+D</p>
          <div class="creator-tag">
            Creado por <strong>Jimmy Stebym Rosero Barrera</strong> • UNAL Sede Medellín
          </div>
        </div>
      </div>
      <div class="header-meta">
        <div class="status-beacon" title="Estado del bot y sincronización diaria">
          <span class="beacon-dot"></span>
          <span>SISTEMA ACTIVO</span>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('todas', document.querySelector('.tab-link:nth-child(1)'))" title="Ver todas las vacantes">
          💼 Vacantes: <strong style="color: var(--accent-cyan);">{len(vacantes)}</strong>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('exclusivas', document.querySelector('.tab-link.exclusive'))" title="Ver vacantes exclusivas para físicos">
          ⭐ Exclusivas: <strong style="color: var(--accent-amber);">{total_exclusivas}</strong>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('inminentes', document.querySelector('.tab-link.urgent'))" title="Ver convocatorias próximas a cerrar">
          ⏳ Cierres: <strong style="color: var(--accent-crimson);">{total_inminentes}</strong>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('becas', document.querySelector('.tab-link:nth-child(5)'))" title="Ver catálogo internacional y convenios">
          🌍 Internacional: <strong style="color: var(--accent-emerald);">{total_convenios + total_becas}</strong>
        </div>
        <button class="theme-toggle" id="themeToggle" type="button" aria-label="Cambiar a modo oscuro" aria-pressed="false">
          <span class="theme-toggle-icon" aria-hidden="true">◐</span><span class="theme-toggle-label">Modo oscuro</span>
        </button>
      </div>
    </div>
  </header>

  <main class="main-content">

    <section class="manifesto-box">
      <h2>📡 Radar de Oportunidades & Pasantías — Ingeniería Física (UNAL Medellín)</h2>
      <p>
        Plataforma automatizada desarrollada por <strong>Jimmy Stebym Rosero Barrera</strong>. El motor cruza las materias clave de nuestro pénsum oficial (<strong>Análisis de Datos & IA, Electrónica Digital / IoT / I2C, Electrónica Análoga, Metrología e Instrumentación, Simulación Numérica, Cuántica, Radiaciones y Diseño CAD</strong>) con las convocatorias del sector industrial, biomédico y tecnológico.
      </p>
    </section>

    <!-- NAVEGACIÓN POR PESTAÑAS (TABS) -->
    <nav class="tabs-nav" aria-label="Secciones de prácticas">
      <button class="tab-link active" onclick="switchMainTab('todas', this)">
        💼 Todas las Vacantes ({len(vacantes)})
      </button>
      <button class="tab-link exclusive" onclick="switchMainTab('exclusivas', this)">
        ⭐ Exclusivas: Piden Físico / Ing. Físico ({total_exclusivas})
      </button>
      <button class="tab-link urgent" onclick="switchMainTab('inminentes', this)">
        ⏳ Próximas a Finalizar (&lt; 5 Días) ({total_inminentes})
      </button>
      <button class="tab-link" onclick="switchMainTab('canales', this)">
        🚀 Ecosistema Nacional & Retos
      </button>
      <button class="tab-link" onclick="switchMainTab('becas', this)">
        🌍 Becas & Pasantías Internacionales ({total_becas})
      </button>
    </nav>

    <!-- CONTENEDOR DE FILTROS Y BÚSQUEDA -->
    <div id="filterControls">
      <div class="search-wrapper">
        <span class="search-icon-inside" aria-hidden="true">🔍</span>
        <input type="text" id="searchInput" class="search-bar" placeholder="Buscar por materia, software o tecnología (ej. I2C, Python, Taller V, CAD, PLC, Cuántica, Radiaciones)..." onkeyup="handleFilter()">
      </div>
      <div class="application-tracker">
        <label for="applicationFilter">Mis postulaciones <span>· se guarda en tu navegador</span></label>
        <select id="applicationFilter" onchange="handleFilter()">
          <option value="all">Todas las convocatorias</option>
          <option value="pending">Pendientes de postularme</option>
          <option value="applied">Ya me postulé</option>
        </select>
        <span id="applicationSummary" aria-live="polite"></span>
      </div>

      <div class="branch-pills" id="pillsContainer">
        <button class="branch-pill active" onclick="handlePill('TODOS', this)">Todas las ramas</button>
        <button class="branch-pill" onclick="handlePill('Análisis de Datos, IA y Simulaciones', this)">Datos, IA & Simulaciones</button>
        <button class="branch-pill" onclick="handlePill('Electrónica Digital, Microcontroladores e IoT', this)">Electrónica Digital & IoT (I2C)</button>
        <button class="branch-pill" onclick="handlePill('Electrónica Análoga y Circuitos', this)">Electrónica Análoga</button>
        <button class="branch-pill" onclick="handlePill('Instrumentación y Metrología Industrial', this)">Instrumentación & Metrología</button>
        <button class="branch-pill" onclick="handlePill('Diseño Mecánico y Dibujo Técnico', this)">Diseño Mecánico & CAD</button>
        <button class="branch-pill" onclick="handlePill('Cuántica, Estado Sólido y Nuevas Tecnologías', this)">Cuántica & Estado Sólido</button>
        <button class="branch-pill" onclick="handlePill('Física de Radiaciones y Física Médica', this)">Radiaciones & Física Médica</button>
        <button class="branch-pill" onclick="handlePill('Óptica, Fotónica y Visión Artificial', this)">Óptica & Visión Artificial</button>
        <button class="branch-pill" onclick="handlePill('Ciencia de Materiales y Nanotecnología', this)">Materiales & Nanotecnología</button>
        <button class="branch-pill" onclick="handlePill('Energía, Potencia y Renovables', this)">Energía & Potencia</button>
      </div>
    </div>

    <!-- GRILLA PRINCIPAL DE VACANTES (HTML SEMÁNTICO) -->
    <section class="jobs-grid" id="jobsContainer" aria-live="polite">
      <!-- Inyectado dinámicamente con etiquetas article sanitizadas -->
    </section>

    <!-- PESTAÑA: BECAS & PASANTÍAS INTERNACIONALES -->
    <section id="becasContainer" style="display: none;">
      <article class="editorial-card">
        <h3>Becas, Pasantías Internacionales y Convenios Oficiales UNAL</h3>
        <p>Oportunidades globales de alto impacto para estudiantes y egresados de <strong>Ingeniería Física</strong>: becas completas de posgrado (India, China, Europa), pasantías técnicas remuneradas (IAESTE, DAAD, CERN, Mitacs) y el catálogo oficial de más de <strong>{total_convenios} convenios vigentes suscritos por la Universidad Nacional de Colombia</strong> en más de 60 países.</p>

        <!-- SUBSECCIÓN 1: BECAS Y CONVOCATORIAS GLOBALES -->
        <h4 style="color: var(--accent-cyan); margin: 26px 0 14px; font-family: var(--font-display); font-size: 1.18rem; border-bottom: 1px solid var(--border-technical); padding-bottom: 8px;">
          🌐 Convocatorias Globales Activas (Europa, Asia y América)
        </h4>
        <div id="becasGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
          <!-- Inyectado dinámicamente -->
        </div>

        <!-- SUBSECCIÓN 2: BUSCADOR DE CONVENIOS UNAL DRE -->
        <h4 style="color: var(--accent-amber); margin: 38px 0 10px; font-family: var(--font-display); font-size: 1.18rem; border-bottom: 1px solid var(--border-technical); padding-bottom: 8px;">
          🏛️ Directorio de Convenios Internacionales Oficiales de la UNAL (DRE)
        </h4>
        <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 16px;">
          Convenios vigentes suscritos por la UNAL para <strong>movilidad académica, prácticas, investigación y doble titulación</strong> en facultades de ciencias e ingeniería. Selecciona un país o busca tu universidad de interés y abre el documento oficial suscrito en Google Drive.
        </p>

        <div class="convenios-controls">
          <input type="text" id="conveniosSearch" class="search-bar" style="flex: 1 1 240px; margin: 0; padding: 10px 14px;" placeholder="Buscar universidad o palabra clave (ej. RWTH Aachen, Munich, Sao Paulo, Toronto)..." onkeyup="handleConveniosFilter()">
          <select id="conveniosCountryFilter" onchange="handleConveniosFilter()">
            <option value="ALL">Todos los países ({total_convenios} convenios)</option>
          </select>
          <select id="conveniosTypeFilter" onchange="handleConveniosFilter()">
            <option value="ALL">Todos los tipos de convenio</option>
          </select>
        </div>
        <div id="conveniosCounter" style="font-family: var(--font-mono); font-size: 0.84rem; color: var(--accent-cyan); margin-bottom: 14px; font-weight: 600;"></div>
        <div id="conveniosList" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; max-height: 700px; overflow-y: auto; padding-right: 6px;">
          <!-- Inyectado dinámicamente -->
        </div>
      </article>
    </section>

    <!-- PESTAÑA: ECOSISTEMA & CANALES ESTRATÉGICOS -->
    <section id="canalesContainer" style="display: none;">
      <article class="editorial-card">
        <h3>Ecosistema de Plataformas & Canales Estratégicos en Colombia</h3>
        <p>Además de las convocatorias rastreadas en vivo por este portal, como estudiante de <strong>Ingeniería Física de la UNAL</strong> cuentas con plataformas clave donde las empresas reclutan directamente o plantean retos de ingeniería aplicada:</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 18px;">
          <div style="background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 12px; padding: 18px;">
            <h4 style="color: var(--accent-cyan); margin-bottom: 6px; font-family: var(--font-display);">1. Interacpedia (Retos Empresariales)</h4>
            <p style="font-size: 0.88rem; line-height: 1.45; color: var(--text-muted); margin-bottom: 12px;">
              Plataforma de innovación abierta nacida en Medellín. Empresas como <strong>Grupo Éxito, Haceb, ISA, Argos y Corona</strong> publican desafíos de ingeniería (visión artificial, optimización energética, sensores, IA). Quien plantea la mejor solución técnica es vinculado directamente como practicante.
            </p>
            <a href="https://interacpedia.com/" target="_blank" rel="noopener noreferrer" class="apply-link" style="display: inline-block; font-size: 0.8rem; padding: 6px 14px;">Explorar Retos en Interacpedia ↗</a>
          </div>

          <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 18px;">
            <h4 style="color: var(--accent-emerald); margin-bottom: 6px; font-family: var(--font-display);">2. Estado Joven (MinTrabajo)</h4>
            <p style="font-size: 0.88rem; line-height: 1.45; color: var(--text-muted); margin-bottom: 12px;">
              Programa oficial del Estado colombiano que financia prácticas universitarias (5 meses) en entidades públicas: <strong>IDEAM, MinCiencias, Secretarías de Medio Ambiente y Gobernación de Antioquia</strong>. Ofrecen <strong>1 SMMLV mensual pagado por el Estado</strong> y convalidación de experiencia laboral.
            </p>
            <a href="https://www.mintrabajo.gov.co/empleo-y-pensiones/movilidad-y-formacion/estado-joven" target="_blank" rel="noopener noreferrer" class="apply-link" style="display: inline-block; font-size: 0.8rem; padding: 6px 14px;">Ver Convocatoria Estado Joven ↗</a>
          </div>

          <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 12px; padding: 18px;">
            <h4 style="color: var(--accent-amber); margin-bottom: 6px; font-family: var(--font-display);">3. SENA SGVA (Contrato de Aprendizaje)</h4>
            <p style="font-size: 0.88rem; line-height: 1.45; color: var(--text-muted); margin-bottom: 12px;">
              Portal obligatorio de ley para contratos de aprendizaje. Solicita a la <strong>Oficina de Prácticas de la Facultad de Minas</strong> tu habilitación en el SGVA. Una vez activo, las empresas industriales de Antioquia te asignan cartas de presentación para vacantes obligatorias con 100% SMMLV + EPS + ARL.
            </p>
            <a href="https://caprendizaje.sena.edu.co/" target="_blank" rel="noopener noreferrer" class="apply-link" style="display: inline-block; font-size: 0.8rem; padding: 6px 14px;">Acceder al SGVA SENA ↗</a>
          </div>

          <div style="background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 12px; padding: 18px;">
            <h4 style="color: #a78bfa; margin-bottom: 6px; font-family: var(--font-display);">4. Torre.ai (Data Science & Física Computacional)</h4>
            <p style="font-size: 0.88rem; line-height: 1.45; color: var(--text-muted); margin-bottom: 12px;">
              Red especializada en talento tecnológico fundada por Alexander Torrenegra. Es el canal ideal para pasantías y roles remotos en <strong>Python, Machine Learning, Visión Artificial, Deep Learning y Modelado Numérico</strong> en startups tecnológicas.
            </p>
            <a href="https://torre.ai/" target="_blank" rel="noopener noreferrer" class="apply-link" style="display: inline-block; font-size: 0.8rem; padding: 6px 14px;">Buscar en Torre.ai ↗</a>
          </div>

          <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 18px;">
            <h4 style="color: #f87171; margin-bottom: 6px; font-family: var(--font-display);">5. FirstJob Colombia (Semilleros Multinacionales)</h4>
            <p style="font-size: 0.88rem; line-height: 1.45; color: var(--text-muted); margin-bottom: 12px;">
              Portal especializado en programas de <em>Early Careers</em> y pasantías en multinacionales como <strong>Schneider Electric, Schlumberger/SLB, Unilever, Nestlé y Galderma</strong>, con evaluación y ranking BIE de empresas para practicantes.
            </p>
            <a href="https://firstjob.me/ofertas?country[]=47" target="_blank" rel="noopener noreferrer" class="apply-link" style="display: inline-block; font-size: 0.8rem; padding: 6px 14px;">Ver Prácticas FirstJob ↗</a>
          </div>

          <div style="background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 18px;">
            <h4 style="color: #60a5fa; margin-bottom: 6px; font-family: var(--font-display);">6. Bolsa de Prácticas Facultad de Minas UNAL</h4>
            <p style="font-size: 0.88rem; line-height: 1.45; color: var(--text-muted); margin-bottom: 12px;">
              Convenios exclusivos gestionados directamente por la <strong>Dirección Académica y la Unidad de Prácticas de la Facultad de Minas Sede Medellín</strong>. Revisa periódicamente los boletines de correo institucional y el sistema interno universitario.
            </p>
            <a href="https://minas.medellin.unal.edu.co/" target="_blank" rel="noopener noreferrer" class="apply-link" style="display: inline-block; font-size: 0.8rem; padding: 6px 14px;">Portal Facultad de Minas ↗</a>
          </div>
        </div>
      </article>
    </section>

  </main>

  <!-- BOTÓN FLOTANTE VOLVER ARRIBA -->
  <button id="backToTop" class="back-to-top" aria-label="Volver arriba">↑</button>

  <!-- FOOTER SEMÁNTICO -->
  <footer class="site-footer">
    <p class="institution">Herramienta desarrollada para estudiantes de Ingeniería Física • UNAL Medellín, Colombia</p>
    <p class="schedule-note">Actualización automática todos los días a las 20:00 (Vacantes) y a las 07:00 (Becas y Convenios)</p>
  </footer>

  <script>
    /* ==========================================================================
       SEGURIDAD Y SANITIZACIÓN CLIENTE (Prevención XSS y Enlaces Maliciosos)
       ========================================================================== */
    function escapeHtml(str) {{
      if (str === null || str === undefined) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }}

    function sanitizeUrl(url) {{
      if (!url) return '#';
      const trimmed = String(url).trim();
      if (/^(https?:\\/\\/|mailto:)/i.test(trimmed)) {{
        return trimmed;
      }}
      return '#';
    }}

    function getCountryFlag(country) {{
      if (!country) return '🌐';
      const c = country.toLowerCase();
      if (c.includes('alemania')) return '🇩🇪';
      if (c.includes('austria')) return '🇦🇹';
      if (c.includes('reino unido')) return '🇬🇧';
      if (c.includes('suiza')) return '🇨🇭';
      if (c.includes('india')) return '🇮🇳';
      if (c.includes('china')) return '🇨🇳';
      if (c.includes('canadá') || c.includes('canada')) return '🇨🇦';
      if (c.includes('estados unidos') || c.includes('ee.uu') || c.includes('usa')) return '🇺🇸';
      if (c.includes('francia')) return '🇫🇷';
      if (c.includes('españa')) return '🇪🇸';
      if (c.includes('italia')) return '🇮🇹';
      if (c.includes('brasil')) return '🇧🇷';
      if (c.includes('méxico') || c.includes('mexico')) return '🇲🇽';
      if (c.includes('japón') || c.includes('japon')) return '🇯🇵';
      if (c.includes('chile')) return '🇨🇱';
      if (c.includes('argentina')) return '🇦🇷';
      return '🌍';
    }}

    const allJobs = {vacantes_json_str};
    const allBecas = {becas_json_str};
    const allConvenios = {convenios_json_str};
    let currentTab = 'todas';
    let currentBranch = 'TODOS';
    const appliedStorageKey = 'ipf-applied-jobs-v1';
    let appliedJobs = new Set();
    try {{ appliedJobs = new Set(JSON.parse(localStorage.getItem(appliedStorageKey) || '[]')); }} catch {{}}

    function renderBecas() {{
      const grid = document.getElementById('becasGrid');
      if (!grid || grid.children.length > 0) return;
      allBecas.forEach(b => {{
        const card = document.createElement('div');
        card.className = 'beca-card';
        const badgeColor = b.destacada ? 'var(--accent-amber)' : 'var(--accent-cyan)';
        const flag = getCountryFlag(b.pais);
        card.innerHTML = `
          <div>
            <div class="beca-header">
              <span class="beca-type-tag" style="background: ${{badgeColor}}22; color: ${{badgeColor}}; border: 1px solid ${{badgeColor}}44;">${{escapeHtml(b.tipo || 'Beca Global')}}</span>
              <span class="beca-country-tag">${{flag}} ${{escapeHtml(b.pais)}}</span>
            </div>
            <h4 class="beca-title">${{escapeHtml(b.titulo)}}</h4>
            <div class="beca-entity">${{escapeHtml(b.entidad)}}</div>
            ${{b.cobertura ? `<div class="beca-coverage"><strong>Cobertura:</strong> ${{escapeHtml(b.cobertura)}}</div>` : ''}}
            <p class="beca-desc">${{escapeHtml(b.descripcion || '')}}</p>
          </div>
          <a href="${{sanitizeUrl(b.url)}}" target="_blank" rel="noopener noreferrer" class="apply-link" style="text-align: center; font-size: 0.82rem; padding: 9px 14px;">
            <span>Ver Convocatoria Oficial</span> <span>↗</span>
          </a>
        `;
        grid.appendChild(card);
      }});
    }}

    let conveniosPopulated = false;
    function initConveniosFilters() {{
      if (conveniosPopulated) return;
      const countrySel = document.getElementById('conveniosCountryFilter');
      const typeSel = document.getElementById('conveniosTypeFilter');
      if (!countrySel || !typeSel) return;

      const countryCounts = {{}};
      allConvenios.forEach(c => {{
        if (c.pais) {{
          countryCounts[c.pais] = (countryCounts[c.pais] || 0) + 1;
        }}
      }});

      const countries = Object.keys(countryCounts).sort();
      countries.forEach(p => {{
        const opt = document.createElement('option');
        opt.value = p;
        const flag = getCountryFlag(p);
        opt.textContent = `${{flag}} ${{p}} (${{countryCounts[p]}})`;
        countrySel.appendChild(opt);
      }});

      const types = [...new Set(allConvenios.map(c => c.tipo).filter(Boolean))].sort();
      types.forEach(t => {{
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        typeSel.appendChild(opt);
      }});

      conveniosPopulated = true;
    }}

    function handleConveniosFilter() {{
      initConveniosFilters();
      const q = (document.getElementById('conveniosSearch')?.value || '').toLowerCase();
      const country = document.getElementById('conveniosCountryFilter')?.value || 'ALL';
      const type = document.getElementById('conveniosTypeFilter')?.value || 'ALL';
      const list = document.getElementById('conveniosList');
      const counter = document.getElementById('conveniosCounter');
      if (!list) return;

      const filtered = allConvenios.filter(c => {{
        if (country !== 'ALL' && c.pais !== country) return false;
        if (type !== 'ALL' && c.tipo !== type) return false;
        if (q && !c.institucion.toLowerCase().includes(q) && !c.pais.toLowerCase().includes(q) && !c.tipo.toLowerCase().includes(q) && !c.nombre.toLowerCase().includes(q)) return false;
        return true;
      }});

      if (counter) counter.textContent = `Mostrando ${{filtered.length}} de ${{allConvenios.length}} convenios vigentes`;
      list.innerHTML = '';

      if (filtered.length === 0) {{
        list.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 30px; color: var(--text-muted); font-family: var(--font-mono);">No se encontraron convenios con este criterio.</div>';
        return;
      }}

      filtered.slice(0, 120).forEach(c => {{
        const card = document.createElement('div');
        card.className = 'convenio-card';
        const flag = getCountryFlag(c.pais);
        card.innerHTML = `
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <span style="font-size: 0.72rem; font-family: var(--font-mono); font-weight: 700; padding: 2px 8px; border-radius: 999px; background: rgba(0,240,160,0.12); color: var(--accent-emerald);">${{flag}} ${{escapeHtml(c.pais)}}</span>
              <span style="font-size: 0.72rem; font-family: var(--font-mono); color: var(--text-dim);">Suscrito: ${{escapeHtml(c.ano)}}</span>
            </div>
            <h5 style="font-family: var(--font-display); font-size: 0.96rem; color: var(--text-main); margin-bottom: 6px; line-height: 1.35;">${{escapeHtml(c.institucion)}}</h5>
            <div style="font-size: 0.78rem; color: var(--accent-cyan); margin-bottom: 6px; font-weight: 500;">${{escapeHtml(c.tipo)}}</div>
            <div style="font-size: 0.76rem; color: var(--text-muted); line-height: 1.35; margin-bottom: 12px;">${{escapeHtml(c.area)}}</div>
          </div>
          ${{c.link ? `<a href="${{sanitizeUrl(c.link)}}" target="_blank" rel="noopener noreferrer" class="apply-link" style="text-align: center; font-size: 0.76rem; padding: 6px 12px; border-radius: 8px;"><span>Ver Convenio Oficial (Drive)</span> <span>↗</span></a>` : ''}}
        `;
        list.appendChild(card);
      }});
      if (filtered.length > 120) {{
        const notice = document.createElement('div');
        notice.style.cssText = 'grid-column: 1/-1; text-align: center; padding: 12px; font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted);';
        notice.textContent = `Mostrando los primeros 120 resultados de ${{filtered.length}}. Usa el buscador o filtro de país para afinar.`;
        list.appendChild(notice);
      }}
    }}

    function renderJobs(list) {{
      const container = document.getElementById('jobsContainer');
      container.innerHTML = '';

      if (list.length === 0) {{
        container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 50px; color: var(--text-muted); font-family: var(--font-mono);">No se encontraron vacantes bajo este criterio. Prueba con otra palabra clave o rama.</div>';
        return;
      }}

      list.forEach(j => {{
        const card = document.createElement('article');
        card.className = 'job-card';
        if (j.es_cierre_inminente) card.classList.add('urgent');
        if (j.es_exclusiva_fisica) card.classList.add('exclusive');

        const tagsHtml = j.ramas.map(r => `<span class="job-tag" style="border-left: 2px solid ${{r.color}}">${{escapeHtml(r.nombre)}}</span>`).join('');

        let badgeColor = j.color_principal;
        let badgeText = j.afinidad.toUpperCase();
        if (j.es_cierre_inminente) {{
          badgeText = 'CIERRE INMINENTE (< 5 DIAS)';
          badgeColor = 'var(--accent-crimson)';
        }} else if (j.es_exclusiva_fisica) {{
          badgeText = 'EXCLUSIVA FISICA';
          badgeColor = 'var(--accent-amber)';
        }}

        const isApplied = appliedJobs.has(j.url);
        card.innerHTML = `
          <div>
            <header class="job-card-header">
              <span class="affinity-badge" style="background: ${{badgeColor}}22; color: ${{badgeColor}}; border: 1px solid ${{badgeColor}}55;">
                ${{escapeHtml(badgeText)}}
              </span>
              <div class="header-right">
                <time class="job-date">${{escapeHtml(j.fecha_publicacion)}}</time>
                <div class="info-trigger" tabindex="0">
                  <span class="info-icon" title="Pasa el cursor para ver la misión de la práctica">+</span>
                  <div class="floating-cloud">
                    <div class="cloud-title">Misión & Contexto</div>
                    <div class="cloud-body">${{escapeHtml(j.mision)}}</div>
                    ${{j.perfil ? `<div style="margin-top: 8px; font-size: 0.80rem; color: var(--accent-cyan); line-height: 1.35;"><strong>Perfil sugerido:</strong> ${{escapeHtml(j.perfil)}}</div>` : ''}}
                    <div class="cloud-tasks-section">
                      <strong>¿Qué te tocará hacer?</strong>
                      <p>${{escapeHtml(j.tareas)}}</p>
                    </div>
                  </div>
                </div>
              </div>
            </header>
            <h3 class="job-title">${{escapeHtml(j.titulo)}}</h3>
            <div class="job-company">🏢 ${{escapeHtml(j.empresa)}}</div>
            <div class="job-specs">
              <span>📍 ${{escapeHtml(j.ubicacion)}}</span>
              <span>💼 Portal: ${{escapeHtml(j.fuente)}}</span>
            </div>
            ${{j.compensacion ? `<div class="salary-highlight"><span>💰</span> ${{escapeHtml(j.compensacion)}}</div>` : ''}}
            <div class="job-tags">${{tagsHtml}}</div>
          </div>
          <footer class="job-card-footer">
            <a href="${{sanitizeUrl(j.url)}}" target="_blank" class="apply-link" rel="noopener noreferrer">
              <span>Postularme a la Oferta</span> <span aria-hidden="true">↗</span>
            </a>
            <button type="button" class="application-toggle${{isApplied ? ' is-applied' : ''}}" aria-pressed="${{isApplied}}">${{isApplied ? '✓ Ya me postulé' : 'Marcar como postulada'}}</button>
          </footer>
        `;
        card.querySelector('.application-toggle').addEventListener('click', () => toggleApplied(j.url));
        container.appendChild(card);
      }});
    }}

    function handleFilter() {{
      const query = (document.getElementById('searchInput')?.value || '').toLowerCase();
      const applicationFilter = document.getElementById('applicationFilter')?.value || 'all';
      const appliedCount = allJobs.filter(j => appliedJobs.has(j.url)).length;
      const pendingCount = allJobs.length - appliedCount;
      const summaryEl = document.getElementById('applicationSummary');
      if (summaryEl) summaryEl.textContent = `${{appliedCount}} postuladas · ${{pendingCount}} pendientes`;

      const filtered = allJobs.filter(j => {{
        if (currentTab === 'exclusivas' && !j.es_exclusiva_fisica) return false;
        if (currentTab === 'inminentes' && !j.es_cierre_inminente) return false;
        if (applicationFilter === 'pending' && appliedJobs.has(j.url)) return false;
        if (applicationFilter === 'applied' && !appliedJobs.has(j.url)) return false;

        const matchesBranch = (currentBranch === 'TODOS') || j.ramas.some(r => r.nombre === currentBranch);
        if (!matchesBranch) return false;

        const matchesText = j.titulo.toLowerCase().includes(query) ||
                            j.empresa.toLowerCase().includes(query) ||
                            j.ubicacion.toLowerCase().includes(query) ||
                            j.mision.toLowerCase().includes(query) ||
                            j.tareas.toLowerCase().includes(query) ||
                            (j.perfil && j.perfil.toLowerCase().includes(query)) ||
                            (j.compensacion && j.compensacion.toLowerCase().includes(query)) ||
                            j.ramas.some(r => r.nombre.toLowerCase().includes(query));
        return matchesText;
      }});

      renderJobs(filtered);
    }}

    function toggleApplied(url) {{
      if (appliedJobs.has(url)) appliedJobs.delete(url);
      else appliedJobs.add(url);
      try {{ localStorage.setItem(appliedStorageKey, JSON.stringify([...appliedJobs])); }} catch {{}}
      handleFilter();
    }}

    function handlePill(branchName, btn) {{
      currentBranch = branchName;
      document.querySelectorAll('.branch-pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      handleFilter();
    }}

    function switchMainTab(tabId, btn) {{
      document.querySelectorAll('.tab-link').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');

      currentTab = tabId;
      const filterBox = document.getElementById('filterControls');
      const jobsBox = document.getElementById('jobsContainer');
      const canalesBox = document.getElementById('canalesContainer');
      const becasBox = document.getElementById('becasContainer');

      if (tabId === 'canales') {{
        filterBox.style.display = 'none';
        jobsBox.style.display = 'none';
        if (canalesBox) canalesBox.style.display = 'block';
        if (becasBox) becasBox.style.display = 'none';
      }} else if (tabId === 'becas') {{
        filterBox.style.display = 'none';
        jobsBox.style.display = 'none';
        if (canalesBox) canalesBox.style.display = 'none';
        if (becasBox) {{
          becasBox.style.display = 'block';
          renderBecas();
          handleConveniosFilter();
        }}
      }} else {{
        filterBox.style.display = 'block';
        jobsBox.style.display = 'grid';
        if (canalesBox) canalesBox.style.display = 'none';
        if (becasBox) becasBox.style.display = 'none';
        handleFilter();
      }}
    }}

    function setTheme(theme) {{
      document.documentElement.dataset.theme = theme;
      try {{ localStorage.setItem('ipf-theme', theme); }} catch {{}}
      const toggle = document.getElementById('themeToggle');
      const isDark = theme === 'dark';
      toggle.setAttribute('aria-pressed', String(isDark));
      toggle.setAttribute('aria-label', isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
      toggle.querySelector('.theme-toggle-label').textContent = isDark ? 'Modo claro' : 'Modo oscuro';
      toggle.querySelector('.theme-toggle-icon').textContent = isDark ? '☼' : '◐';
    }}

    document.getElementById('themeToggle')?.addEventListener('click', () => {{
      setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
    }});

    // Botón flotante Volver Arriba
    const backBtn = document.getElementById('backToTop');
    window.addEventListener('scroll', () => {{
      if (window.scrollY > 350) {{
        backBtn?.classList.add('visible');
      }} else {{
        backBtn?.classList.remove('visible');
      }}
    }}, {{ passive: true }});
    backBtn?.addEventListener('click', () => {{
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});

    setTheme(document.documentElement.dataset.theme || 'light');
    handleFilter();
  </script>
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
    if "--render-only" in sys.argv:
        print("[*] Modo render-only: regenerando HTML y CSV desde vacantes_practicas.json...")
        config_ramas = load_json(CONFIG_RAMAS_PATH)
        vacantes = load_json(OUTPUT_JSON)
        build_full_html(vacantes, config_ramas)
        export_csv(vacantes)
        return

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

    # 4. Rastrear ElEmpleo.com (Antioquia / Pasantías de Ingeniería)
    elempleo_queries = [
        "practicante ingenieria",
        "practicante automatizacion",
        "practicante electromecanico",
        "practicante datos"
    ]
    print(f"\n[*] Rastreando ElEmpleo.com ({len(elempleo_queries)} categorías)...")
    for q_ee in elempleo_queries:
        ee_jobs = scrape_elempleo_query(q_ee)
        added_ee = 0
        for j in ee_jobs:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_raw_jobs.append(j)
                added_ee += 1
        if added_ee > 0:
            print(f"    ElEmpleo '{q_ee}': +{added_ee} ofertas")
        time.sleep(0.3)

    # 5. Rastrear FirstJob Colombia (Semilleros Multinacionales)
    firstjob_queries = [
        "practicante",
        "intern",
        "ingenieria"
    ]
    print(f"\n[*] Rastreando FirstJob Colombia ({len(firstjob_queries)} búsquedas)...")
    for q_fj in firstjob_queries:
        fj_jobs = scrape_firstjob_query(q_fj)
        added_fj = 0
        for j in fj_jobs:
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_raw_jobs.append(j)
                added_fj += 1
        if added_fj > 0:
            print(f"    FirstJob '{q_fj}': +{added_fj} ofertas")
        time.sleep(0.3)

    # 6. Rastrear LinkedIn Jobs para categorías del pénsum UNAL
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

    # 7. Rastrear convocatorias de practicantes en empresas líderes de Medellín y Antioquia
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
