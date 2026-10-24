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
import unicodedata
from html import unescape
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
import requests
import concurrent.futures

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

LOCAL_LOCATION_RE = re.compile(
    r"medell[ií]n|antioquia|valle de aburr[aá]|envigado|itag[uüíi]|bello|sabaneta|rionegro|"
    r"apartad[oó]|la estrella|copacabana|girardota|caldas|marinilla|barbosa|cisneros|"
    r"el retiro|retiro|guarne|santo domingo|puerto berr[ií]o",
    re.IGNORECASE,
)
REMOTE_MODALITY_RE = re.compile(
    r"\b(remoto|remota|remote|teletrabajo)\b|100\s*%\s*h[ií]brid[oa]",
    re.IGNORECASE,
)
REMOTE_GLOBAL_SCOPE_RE = re.compile(
    r"\b(worldwide|world\s*wide|anywhere|any\s+country|all\s+countries|global(?:ly)?|"
    r"latin\s+america|latam|south\s+america|americas|colombia|remote\s+from\s+anywhere)\b",
    re.IGNORECASE,
)
REMOTE_GENERIC_LOCATION_RE = re.compile(
    r"^\s*(?:fully\s+)?remote\s*$|^\s*worldwide\s*$|^\s*remote\s*[-(]\s*(?:global|worldwide|anywhere)\s*\)?\s*$",
    re.IGNORECASE,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_RAMAS_PATH = os.path.join(BASE_DIR, "config_ramas.json")
CONVOCATORIAS_DESTACADAS_PATH = os.path.join(BASE_DIR, "convocatorias_destacadas.json")
OUTPUT_HTML = os.path.join(BASE_DIR, "dashboard_practicas.html")
OUTPUT_INDEX = os.path.join(BASE_DIR, "index.html")
OUTPUT_CSV = os.path.join(BASE_DIR, "vacantes_practicas.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "vacantes_practicas.json")
OUTPUT_RSS = os.path.join(BASE_DIR, "feed.xml")

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
    "programa mujer stem",
    # Perfiles espejo y competencias que las empresas suelen usar en sus vacantes
    "practicante ingenieria de sistemas analitica",
    "practicante matematica estadistica modelado",
    "practicante rpa power platform",
    "practicante calibracion sensores",
    "practicante ingenieria de control plc scada",
    "practicante eficiencia energetica fotovoltaica",
    "practicante movilidad electrica subestaciones",
    "practicante caracterizacion materiales corrosion",
    "practicante fibra optica otdr telecomunicaciones",
    "practicante vision por computador procesamiento imagenes",
    "practicante radioproteccion dosimetria fisica medica",
    "practicante bioingenieria imagenologia",
    "practicante investigacion desarrollo prototipado",
        "practicante innovacion mejora continua",
        "practicante ingenieria materiales calidad",
        "practicante estadistica riesgos cuantitativos",
        "practicante telecomunicaciones fibra optica",
        "practicante ingenieria biomedica",
        "practicante ingenieria industrial proyectos",
        "practicante eficacia machine learning datos",
        "practicante general motors ingeniería 2027",
        "practicante globant technology 2027",
        "practicante outsourcing transformación digital rpa",
        "practicante prosegur analítica datos",
        "practicante schneider ingeniería automatización",
        "practicante procuraduria estadistica ciencia datos"
]

# Consultas nacionales y remotas: ampliadas desde las búsquedas manuales y los cargos espejo.
NATIONAL_SEARCH_QUERIES = [
    "practicante ingeniería física",
    "practicante ciencias físicas",
    "practicante ciencia de datos machine learning",
    "practicante analítica estadística matemáticas",
    "practicante Python SQL automatización",
    "practicante ingeniería electrónica mecatrónica",
    "practicante ingeniería control PLC SCADA",
    "practicante metrología instrumentación calibración",
    "practicante ingeniería mecánica mantenimiento",
    "practicante materiales laboratorio caracterización",
    "practicante ingeniería eléctrica energía solar",
    "practicante innovación investigación desarrollo",
    "practicante telecomunicaciones visión artificial",
    "prácticas universitarias ingeniería 2027",
    "practicante remote Colombia engineering data"
]

GLOBAL_REMOTE_SEARCH_QUERIES = [
    "physics engineering internship remote worldwide",
    "applied physics research intern remote",
    "data science machine learning intern remote worldwide",
    "python data analytics internship remote global",
    "quantitative research intern remote worldwide",
    "electronics embedded systems internship remote",
    "automation control engineering internship remote",
    "materials science laboratory intern remote",
    "optics photonics research internship remote",
    "energy renewable engineering intern remote",
    "computer vision image processing internship remote",
    "engineering intern remote Latin America",
    "remote internship anywhere engineering physics"
]

EXCLUDED_ROLES = [
    r"\brecepcionista\b", r"\brecepci[oó]n\b", r"\benfermer[ií]?[ao]\b",
    r"\brecursos\s+humanos\b", r"\btalento\s+humano\b", r"\bgesti[oó]n\s+humana\b",
    r"\bpsicolog[ií]?[ao]\b", r"\blibranza\b", r"\bturismo\b", r"\babogad[ao]\b",
    r"\bderecho\b", r"\blegal\b", r"\bcontabilidad\b", r"\bcontable\b", r"\bfinancier[ao]s?\b",
    r"\bnutrici[oó]n\b", r"\binocuidad\b",
    r"\boperario\s+(?:de\s+)?empaque\b", r"\bcajer[ao]\b", r"\bcocina\b", r"\breposter[ií]a\b",
    r"\bmeser[ao]\b", r"\basesor(?:[ií]a|[a])?\s+comercial\b", r"\bejecutiv[ao]\s+comercial\b",
    r"\bvendedor[a]?\b", r"\bcall\s+center\b", r"\bcobranza\b", r"\barchivo\b",
    r"\batenci[oó]n\s+al\s+cliente\b", r"\bservicio\s+al\s+cliente\b", r"\bcompras\b",
    r"\balimentos\b", r"\bagr[ií]cola\b", r"\bagronom[ií]a\b", r"\bdise[nñ]o\s+gr[aá]fico\b",
    r"\bmarketing\b", r"\bmercadeo\b", r"\badministrativ[ao]\b", r"\badministraci[oó]n\s+de\s+empresas\b",
    r"\badm\.?\s+empresas\b", r"\badministraci[oó]n\s+o\b",
    r"\bgestor[a]?\s+de\s+pr[aá]cticas\b", r"\blog[ií]stic[ao]\b",
    r"\bcontadur[ií]a\b", r"\bcontador(?:a|es)?\b", r"\bgastronom[ií]a\b", r"\bbarismo\b",
    r"\bpanader[ií]a\b", r"\bpizzero\b", r"\bdomiciliario\b", r"\bimpuestos\b",
    r"\bcomunicaci[oó]n\s+(?:social|visual|corporativa)\b", r"\btrabajo\s+social\b",
    r"\bsalud\s+ocupacional\b", r"\bseguridad\s+y\s+salud\b", r"\bcomercio\s+exterior\b",
    r"\bnegocios\s+internacionales\b", r"\bpracticante\s+comercial\b", r"\btrade\s+marketing\b",
    r"\barquitectura\b", r"\bingenier[ií]a\s+civil\b", r"\bingenier[ií]a\s+ambiental\b",
    r"\bgesti[oó]n\s+ambiental\b", r"\bpracticante\s+ambiental\b", r"\bforestal\b", r"\bgeolog[ií]a\b",
    r"\bgesti[oó]n\s+documental\b", r"\bdocumental\b", r"\bcompliance\b", r"\bcumplimiento\b",
    r"\bjudicial\b", r"\binfraestructura\s+f[ií]sica\b", r"\bseguridad\s+f[ií]sica\b",
    r"\bm[eé]dico\s+general\b", r"\bvisitador\s+m[eé]dico\b", r"\binversiones\b",
    r"\bcentro\s+comercial\b", r"\bcontrol\s+corporativo\b"
]

# Nivel 1 significa que la convocatoria pide explícitamente Física como carrera.
# Las áreas técnicas (metrología, óptica, radiaciones, etc.) cuentan como competencias,
# nunca como prueba de que la vacante esté dirigida a físicos.
TERMINOS_FISICA_RE = re.compile(
    r'\b(ingenier[ií]a\s+f[ií]sica|ingenier[oa]\s+f[ií]sic[oa]|f[ií]sica\s+m[eé]dica|f[ií]sica\s+aplicada|'
    r'profesional\s+(?:en\s+)?f[ií]sica|estudiante\s+(?:de|en)\s+f[ií]sica|pregrado\s+(?:en|de)\s+f[ií]sica|'
    r'carrera\s+(?:de|en)\s+f[ií]sica|f[ií]sic[oa]s?\s+(?:m[eé]dic[oa]s?|aplicad[oa]s?)|'
    r'(?:student|graduate|degree|background)\s+(?:in\s+)?physics|physics\s+(?:student|graduate|degree|background))\b',
    re.IGNORECASE
)

FALSE_FISICA_PHRASES_RE = re.compile(
    r"\b(?:infraestructura|educaci[oó]n|toma|actividad|salud|condici[oó]n|seguridad|planta|"
    r"cultura|ubicaci[oó]n|presencia|entrega|documentaci[oó]n|verificaci[oó]n|inspecci[oó]n|"
    r"fuerza|capacidad|persona|integridad|tienda|sede|oficina|red|redes|estructura|barrera|"
    r"geograf[ií]a|inventario|archivo|archivos|documento|documentos|espacio|espacios|recurso|recursos|"
    r"medio|medios|activo|activos|instalaciones|esfuerzo|esfuerzos|riesgo|riesgos|variables)\s+f[ií]sic[ao]s?\b",
    re.IGNORECASE
)

# Detecta si la vacante es exclusivamente para Técnico/Tecnólogo SENA (para diferenciar de Pregrado UNAL)
SOLO_TECNICO_RE = re.compile(
    r'\b(t[eé]cnico|tecn[oó]logo|tecnolog[ií]a|t[eé]cnica)\b(?!.*(?:profesional|universitari[ao]|ingenier[ií]a|pregrado))',
    re.IGNORECASE
)
ESTUDIANTE_TECNICO_RE = re.compile(
    r"\bestudiante\s+(?:activo\s+)?(?:de\s+)?(?:un\s+)?(?:t[eé]cnico|tecn[oó]logo|tecnolog[ií]a\s+t[eé]cnica)\b",
    re.IGNORECASE,
)
NIVEL_UNIVERSITARIO_RE = re.compile(
    r"\b(estudiante\s+universitari[oa]|pregrado|carrera\s+profesional|profesional\s+universitari[oa])\b",
    re.IGNORECASE,
)

COMPETENCIAS_GENERICAS_RE = {
    "programacion", "desarrollo", "digital", "optimizacion", "sistemas",
    "mecanica", "electromecanica", "electromecanico", "electronica",
    "quimica", "ingenieria mecanica", "ingenieria electronica",
    "ingenieria electrica", "ingenieria de sistemas", "ingenieria industrial",
    "fuente", "software", "developer", "control", "materiales", "riesgos",
    "cuantitativo", "digitalizacion", "mantenimiento", "innovacion", "investigacion y desarrollo"
}

TERMINOS_MUJERES_RE = re.compile(r'\b(mujer|mujeres|women|women in tech|femenin[ao]?|stem)\b', re.IGNORECASE)

def normalize_search_text(value):
    """Normaliza tildes y mayúsculas para comparar texto de vacantes y pénsum."""
    normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))

def matches_keyword(keyword, text):
    """Busca términos completos sin distinguir tildes para evitar aciertos por subcadenas."""
    kw_clean = normalize_search_text(keyword).strip()
    normalized_text = normalize_search_text(text)
    if not kw_clean:
        return False
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(kw_clean) + r"(?![a-z0-9])", normalized_text))

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def scrape_linkedin_query(query, location="Medellin, Antioquia, Colombia"):
    """Consulta vacantes públicas de LinkedIn en el ámbito indicado."""
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
            
            title = unescape(title_m.group(1).strip()) if title_m else ""
            company = unescape(comp_m.group(1).strip()) if comp_m else "Empresa Confidencial"
            loc = unescape(loc_m.group(1).strip()) if loc_m else "Medellín, Antioquia"
            link = link_m.group(1).split("?")[0] if link_m else ""
            iso_date = date_m.group(1).strip() if date_m else ""
            pub_date = date_m.group(2).strip() if date_m else "Reciente"

            if iso_date:
                try:
                    age_days = (datetime.now(timezone.utc).date() - datetime.fromisoformat(iso_date).date()).days
                    if age_days > 45:
                        continue
                except Exception:
                    pass
            
            if title and link:
                job = {
                    "titulo": title,
                    "empresa": company,
                    "ubicacion": loc,
                    "url": link,
                    "fecha_publicacion": iso_date or pub_date,
                    "fuente": "LinkedIn Jobs"
                }
                if location == "Colombia":
                    job["country_scope"] = "CO"
                elif location == "Worldwide":
                    job["search_scope"] = "WORLDWIDE"
                else:
                    job["search_scope"] = "ANTIOQUIA"
                results.append(job)
        return results
    except Exception:
        return []

def scrape_computrabajo_query(query, nationwide=False):
    """Consulta convocatorias en Computrabajo para Antioquia o todo Colombia."""
    query_slug = re.sub(r"[^a-z0-9]+", "-", normalize_search_text(query)).strip("-")
    url = (
        f"https://co.computrabajo.com/trabajo-de-{query_slug}-en-colombia?q={quote(query)}"
        if nationwide else f"https://co.computrabajo.com/empleos-en-antioquia?q={quote(query)}"
    )
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
            job = {
                "titulo": title,
                "empresa": comp,
                "ubicacion": loc,
                "url": href,
                "fecha_publicacion": "Reciente",
                "fuente": "Computrabajo"
            }
            if nationwide:
                job["country_scope"] = "CO"
            results.append(job)
        return results
    except Exception:
        return []

def scrape_magneto_query(query):
    """Consulta convocatorias de prácticas en Colombia en la API pública de Magneto365."""
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
            else:
                city_str = str(cities)

            # La API se consulta con country=co; conservar todas las ciudades colombianas.

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

            job = {
                "titulo": title,
                "empresa": empresa,
                "ubicacion": "Remoto (Colombia)" if is_remote else (city_str if city_str else "Colombia"),
                "url": url,
                "fecha_publicacion": pub_date,
                "fuente": "Magneto365",
                "country_scope": "CO",
                "compensacion": comp,
                "perfil": perfil,
                "mision": desc[:1800] if desc else ""
            }
            results.append(job)
        return results
    except Exception:
        return []

def scrape_elempleo_query(query):
    """Consulta ofertas de prácticas de ingeniería en ElEmpleo.com para Colombia."""
    url = f"https://www.elempleo.com/co/ofertas-empleo?trabajo={quote(query)}"
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
                loc = data.get("location", "").strip() or "Medellín, Antioquia"
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
                        "country_scope": "CO",
                        "compensacion": comp
                    })
            except Exception:
                continue
        return results
    except Exception:
        return []

def scrape_firstjob_query(query):
    """Consulta convocatorias de prácticas y semilleros en FirstJob Colombia extrayendo ubicación, modalidad y descripción."""
    url = f"https://firstjob.me/ofertas?country[]=47&title={quote(query)}" if query else "https://firstjob.me/ofertas?country[]=47"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return []
        card_blocks = re.split(r'<div class="card-job\s+[^>]*>', r.text)[1:]
        results = []
        for block in card_blocks:
            link_m = re.search(r'<a href="(/oferta/[^"]+)"', block)
            title_m = re.search(r'<h6[^>]*>([^<]+)</h6>', block)
            comp_m = re.search(r'<span class="card-job-top--company[^"]*">([^<]+)</span>', block)
            if not (link_m and title_m):
                continue
            link = link_m.group(1).strip()
            title = unescape(re.sub(r'<[^>]+>', '', title_m.group(1)).strip())
            comp = unescape(re.sub(r'<[^>]+>', '', comp_m.group(1)).strip()) if comp_m else "Empresa Multinacional"
            loc_m = re.search(r'card-job-top--location[^>]*>.*?</i>\s*([^<]+)\s*</span>', block, re.DOTALL)
            raw_loc = unescape(loc_m.group(1).strip()) if loc_m else "Colombia"
            desc_m = re.search(r'<div class="card-job-description[^>]*>(.*?)</div>', block, re.DOTALL)
            desc = unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', desc_m.group(1))).strip()) if desc_m else ""
            badges = [unescape(b.strip()) for b in re.findall(r'<span class="btn btn-small[^"]*">\s*([^<]+)\s*</span>', block)]
            modalidad = ", ".join(badges)
            if any("remoto" in b.lower() for b in badges) and "remoto" not in raw_loc.lower():
                raw_loc = f"{raw_loc} (Remoto)"
            url_job = "https://firstjob.me" + link
            results.append({
                "titulo": title,
                "empresa": comp,
                "ubicacion": raw_loc,
                "modalidad": modalidad,
                "mision": desc,
                "url": url_job,
                "fecha_publicacion": "Reciente",
                "fuente": "FirstJob",
                "country_scope": "CO",
                "compensacion": ""
            })
        return results
    except Exception:
        return []

def classify_and_score_job(job, config_ramas):
    """Calcula el Score de Afinidad con el Pénsum UNAL con priorización y filtrado estricto de roles no-STEM."""
    title_lower = job.get("titulo", "").lower()
    company_lower = job.get("empresa", "").lower()
    perfil_lower = job.get("perfil", "").lower()
    mision_lower = job.get("mision", "").lower()
    tareas_lower = job.get("tareas", "").lower()
    # El nombre de la empresa no debe definir el perfil solicitado ni su afinidad.
    text_to_analyze = f"{title_lower} {perfil_lower} {mision_lower} {tareas_lower}"

    # 1. Descartar roles abiertamente no técnicos / administrativos / SENA no-STEM
    if any(re.search(p, title_lower, re.IGNORECASE) for p in EXCLUDED_ROLES):
        return None
    if SOLO_TECNICO_RE.search(f"{title_lower} {perfil_lower}"):
        return None
    if ESTUDIANTE_TECNICO_RE.search(text_to_analyze) and not NIVEL_UNIVERSITARIO_RE.search(text_to_analyze):
        return None

    # 2. Detección de programas especiales y afinidad real con Física (evitando "infraestructura física", "toma física", etc.)
    es_impulso_liderazgo = bool(TERMINOS_MUJERES_RE.search(text_to_analyze))
    clean_for_physics = FALSE_FISICA_PHRASES_RE.sub(" ", f"{title_lower} {perfil_lower} {mision_lower}")
    es_exclusiva_fisica = bool(
        TERMINOS_FISICA_RE.search(clean_for_physics)
        or re.search(r"\b(?:f[ií]sic[oa]s?|physics)\b", title_lower)
    )

    # 3. Cierre inminente cuando hay fecha explícita
    es_cierre_inminente = False
    fecha_cierre = job.get("fecha_cierre_iso", "")
    if fecha_cierre:
        try:
            dias_para_cierre = (datetime.fromisoformat(fecha_cierre).date() - datetime.now().date()).days
            es_cierre_inminente = 0 <= dias_para_cierre <= 5
        except ValueError:
            pass

    es_aprendiz_de_practica = bool(
        re.search(r"\baprendiz\b", title_lower)
        and re.search(
            r"aprendiz\s+universitari[oa]|estudiante\s+universitari|pregrado|pr[aá]ctica\s+universitaria|"
            r"estudiante.{0,35}ingenier[ií]a|profesional|ingenier[ií]a|mantenimiento|electromec[aá]nic|automatizaci[oó]n|datos|biociencias|business\s+intelligence",
            text_to_analyze,
        )
    )
    es_practica_titulo = bool(re.search(
        r"\b(practicante|práctica|practica|prácticas|practicas|intern(ship)?|trainee|estudiante|pasantía|pasantia|semillero)\b",
        f"{title_lower} {perfil_lower} {job.get('modalidad', '').lower()}",
    ))
    es_practica = es_practica_titulo or es_aprendiz_de_practica
    titulo_es_aprendiz = bool(re.search(r"\baprendiz\b", title_lower))
    if not es_practica or (titulo_es_aprendiz and not es_aprendiz_de_practica):
        return None

    total_score = 0
    if es_impulso_liderazgo:
        total_score += 160
    if es_exclusiva_fisica:
        total_score += 85

    ramas_coincidentes = []
    max_rama_score = 0
    competencias_detectadas = set()
    carreras_espejo_detectadas = set()
    carreras_catalogo = {
        normalize_search_text(carrera).strip()
        for data in config_ramas.get("ramas", {}).values()
        for carrera in data.get("carreras_mencionadas", [])
    }

    for rama_key, data in config_ramas.get("ramas", {}).items():
        if rama_key == "mujeres_stem":
            continue
        competencias_detectadas.update(
            keyword for keyword in data.get("palabras_clave", [])
            if normalize_search_text(keyword).strip() not in COMPETENCIAS_GENERICAS_RE
            and normalize_search_text(keyword).strip() not in carreras_catalogo
            and matches_keyword(keyword, text_to_analyze)
        )

    perfil_vacante = f"{title_lower} {perfil_lower} {mision_lower}"
    normalized_profile = normalize_search_text(perfil_vacante)
    bare_career_names = {"sistemas", "mecanica", "electromecanica", "quimica", "estadistica", "matematicas", "actuaria", "biomedica", "control", "electronica", "electrica", "materiales"}
    for rama_key, data in config_ramas.get("ramas", {}).items():
        if rama_key == "mujeres_stem":
            continue
        for carrera in data.get("carreras_mencionadas", []):
            normalized_career = normalize_search_text(carrera).strip()
            if not normalized_career or normalized_career in {
                "ingenieria", "todas las ingenierias", "fisica", "ingenieria fisica"
            }:
                continue
            if normalized_career in bare_career_names:
                career_match = bool(re.search(
                    r"\b(?:ingenieria(?:\s+de)?|ing\.?|practicante\s+(?:de|en)?|estudiante\s+(?:de|en)?|"
                    r"carrera\s+de|pregrado\s+en|profesional\s+en)\s+"
                    + re.escape(normalized_career) + r"\b",
                    normalized_profile
                ))
            else:
                career_match = matches_keyword(carrera, perfil_vacante)
            if career_match:
                carreras_espejo_detectadas.add(carrera)

    carreras_normalizadas = {
        normalize_search_text(carrera): carrera for carrera in carreras_espejo_detectadas
    }
    carreras_espejo_detectadas = {
        carrera for normalized, carrera in carreras_normalizadas.items()
        if not any(normalized != other and normalized in other for other in carreras_normalizadas)
    }

    # Evitar contar una frase y su subcadena como dos competencias distintas
    normalizadas = {normalize_search_text(item): item for item in competencias_detectadas}
    competencias_detectadas = {
        original for normalized, original in normalizadas.items()
        if not any(
            normalized != other and normalized in other
            for other in normalizadas
        )
    }

    es_alta_afinidad_tecnica = (
        not es_exclusiva_fisica
        and (
            bool(carreras_espejo_detectadas) and len(competencias_detectadas) >= 2
        )
    )

    for rama_key, data in config_ramas.get("ramas", {}).items():
        if rama_key == "mujeres_stem":
            continue

        kw_hits = 0
        title_hits = 0
        palabras = data.get("palabras_clave", [])
        for p in palabras:
            if matches_keyword(p, text_to_analyze):
                kw_hits += 1
                if matches_keyword(p, title_lower):
                    title_hits += 2

        # NUEVO: Sumar afinidad si pide explícitamente una carrera espejo afín a esa rama
        carreras_afines = data.get("carreras_mencionadas", [])
        for c in carreras_afines:
            c_norm = normalize_search_text(c).strip()
            if c_norm in {"ingenieria fisica", "fisica", "todas las ingenierias"} and kw_hits == 0:
                continue
            if matches_keyword(c, text_to_analyze):
                kw_hits += 1
                if matches_keyword(c, title_lower):
                    title_hits += 3

        if kw_hits > 0:
            score = (kw_hits + title_hits) * 4
            empresas_ref = [e.lower() for e in data.get("empresas_referencia", [])]
            for e in empresas_ref:
                if e in company_lower:
                    score += 5

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

    # Si no coincide con ninguna rama técnica del pénsum ni con Física explícita, descartar (evita colar cargos SENA de cocina/archivo/psicología)
    if not ramas_coincidentes and not es_exclusiva_fisica and not es_impulso_liderazgo:
        return None
    if not es_exclusiva_fisica and not carreras_espejo_detectadas and not competencias_detectadas:
        return None

    total_score += max_rama_score
    ramas_coincidentes.sort(key=lambda x: x["score"], reverse=True)

    if not ramas_coincidentes:
        ramas_coincidentes.append({
            "clave": "innovacion_id",
            "nombre": "I+D+i, Innovación y Procesos Industriales",
            "color": "#0f766e",
            "score": 40
        })

    if es_exclusiva_fisica:
        afinidad = "Afinidad con Física"
    elif es_alta_afinidad_tecnica or es_impulso_liderazgo:
        afinidad = "Alta Afinidad Pénsum"
    else:
        afinidad = "Afinidad Media"

    # Bonificación especial si incluye compensación verificada
    if job.get("compensacion"):
        total_score += 35

    job["ramas"] = ramas_coincidentes
    job["rama_principal"] = ramas_coincidentes[0]["nombre"]
    job["color_principal"] = ramas_coincidentes[0]["color"]
    job["clave_principal"] = ramas_coincidentes[0]["clave"]
    job["afinidad"] = afinidad
    job["es_exclusiva_fisica"] = es_exclusiva_fisica
    job["es_alta_afinidad_tecnica"] = es_alta_afinidad_tecnica
    job["nivel_afinidad"] = 1 if es_exclusiva_fisica else (2 if es_alta_afinidad_tecnica else 0)
    job["carreras_espejo_detectadas"] = sorted(carreras_espejo_detectadas)
    job["competencias_detectadas"] = sorted(competencias_detectadas)
    job["es_cierre_inminente"] = es_cierre_inminente
    job["es_practica"] = es_practica
    job["score_pensum"] = total_score
    job["mision"] = (
        job.get("mision") or job.get("resumen_fuente")
        or "La fuente no incluyó una descripción de la misión. Abre la publicación para leerla."
    )
    job["tareas"] = job.get("tareas") or (
        "La fuente no incluyó las funciones del cargo. Revisa los requisitos y tareas directamente en la publicación."
    )

    return job

def deduplicate_classified_jobs(jobs):
    """Quita anuncios repetidos por empresa, título y ubicación aunque cambie la URL."""
    unique = {}
    for job in jobs:
        identity = tuple(
            re.sub(r"[^a-z0-9]+", " ", normalize_search_text(job.get(field, ""))).strip()
            for field in ("empresa", "titulo", "ubicacion")
        )
        current = unique.get(identity)
        if current is None or len(job.get("mision", "")) > len(current.get("mision", "")):
            unique[identity] = job
    return list(unique.values())

def extract_jobposting_details(html):
    """Extrae la descripción y los requisitos de JobPosting cuando la fuente los publica en JSON-LD."""
    for raw in re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html or "", re.IGNORECASE | re.DOTALL
    ):
        try:
            payload = json.loads(unescape(raw).strip())
        except (json.JSONDecodeError, TypeError):
            continue

        stack = payload if isinstance(payload, list) else [payload]
        while stack:
            item = stack.pop()
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            if isinstance(graph, list):
                stack.extend(graph)
            types = item.get("@type", [])
            if isinstance(types, str):
                types = [types]
            if not any(str(kind).casefold() == "jobposting" for kind in types):
                continue

            def clean(value):
                if isinstance(value, dict):
                    value = value.get("name") or value.get("value") or ""
                if isinstance(value, list):
                    value = ", ".join(str(part) for part in value if part)
                return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(value or "")))).strip()

            description = clean(item.get("description"))
            profile_fields = (
                "qualifications", "educationRequirements", "experienceRequirements",
                "skills", "responsibilities"
            )
            profile = " ".join(
                f"{field}: {clean(item.get(field))}"
                for field in profile_fields if clean(item.get(field))
            )
            return {
                "mision": description[:3000],
                "perfil": profile[:2000],
                "fecha_cierre_iso": clean(item.get("validThrough")),
            }
    return {}

def parse_source_date(value):
    """Convierte las fechas de publicación habituales de los portales a date; ignora etiquetas como "Reciente"."""
    value = str(value or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for date_format in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value[:10], date_format).date()
        except ValueError:
            continue
    return None

def verify_job_url(job):
    """Verifica que la URL de postulación sea válida. Permite URLs públicas de LinkedIn Guest API sin bloquearlas por rate-limit del servidor."""
    url = job.get("url", "")
    if not url or not url.startswith("http"):
        return False
    # LinkedIn bloquea la verificación automatizada; la consulta guest solo confirma que
    # la publicación apareció recientemente, no que siga aceptando postulaciones.
    if "linkedin.com/jobs/view/" in url.lower() or "linkedin.com" in url.lower():
        job["estado_vigencia"] = "Publicada recientemente; vigencia sin confirmar"
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=4.5, allow_redirects=True)
        if r.status_code >= 400:
            return False
        structured = extract_jobposting_details(r.text)
        if structured:
            job["mision"] = job.get("mision") or structured.get("mision", "")
            job["perfil"] = job.get("perfil") or structured.get("perfil", "")
            job["fecha_cierre_iso"] = job.get("fecha_cierre_iso") or structured.get("fecha_cierre_iso", "")
        txt = r.text.lower()
        closed_signals = (
            "esta oferta ya no está disponible", "la oferta que buscas ya no está disponible",
            "página no encontrada", "la vacante ha finalizado", "vacante cerrada",
            "proceso de selección ha finalizado", "this job is no longer available",
            "job has expired", "position has been filled", "job is closed"
        )
        if any(signal in txt for signal in closed_signals):
            return False
        has_future_deadline = False
        for valid_through in re.findall(r'"validThrough"\s*:\s*"([^"]+)"', r.text, re.IGNORECASE):
            try:
                vt_clean = valid_through.replace("Z", "+00:00")
                vt_dt = datetime.fromisoformat(vt_clean)
                if vt_dt.tzinfo is None:
                    vt_dt = vt_dt.replace(tzinfo=timezone.utc)
                if vt_dt < datetime.now(timezone.utc):
                    return False
                has_future_deadline = True
            except Exception:
                continue
        publication_date = parse_source_date(job.get("fecha_publicacion"))
        if (
            publication_date
            and (datetime.now(timezone.utc).date() - publication_date).days > 60
            and not has_future_deadline
        ):
            return False
        visible_text = normalize_search_text(unescape(re.sub(r"<[^>]+>", " ", r.text)))
        deadline = re.search(
            r"fecha\s+limite\s+(?:de\s+)?(?:solicitud|postulacion|inscripcion)?\s*[:\-]?\s*"
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
            visible_text
        )
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline.group(1).replace("-", "/"), "%d/%m/%Y").date()
                if deadline_date < datetime.now(timezone.utc).date():
                    return False
            except ValueError:
                pass
        # Extraer la descripción real cuando el portal no la entregó en la tarjeta de búsqueda
        if not job.get("mision"):
            desc_m = (
                re.search(r'<p class="mbB">(.*?)</p>', r.text, re.DOTALL)
                or re.search(r'<div class="description-block[^>]*>.*?<p[^>]*>(.*?)</p>', r.text, re.DOTALL)
            )
            if desc_m:
                clean_desc = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", desc_m.group(1))).strip())
                if len(clean_desc) > 40:
                    job["mision"] = clean_desc[:1800]
        job["estado_vigencia"] = "Enlace accesible en la última consulta"
        return True
    except Exception:
        return False

def is_in_target_location(job):
    """Incluye Antioquia, Colombia y remoto internacional con elegibilidad rastreable."""
    location = str(job.get("ubicacion", ""))
    modality = str(job.get("modalidad", ""))
    explicit_eligibility = " ".join(str(job.get(key, "")) for key in ("alcance_elegibilidad", "pais_elegibilidad"))

    # Estas fuentes consultan Colombia de forma explícita (API country=co, país=Colombia, etc.).
    if job.get("country_scope") == "CO":
        return True
    if LOCAL_LOCATION_RE.search(location):
        return True

    title = str(job.get("titulo", ""))
    location_is_remote = bool(
        REMOTE_MODALITY_RE.search(location)
        or REMOTE_MODALITY_RE.search(modality)
        or (job.get("search_scope") == "WORLDWIDE" and REMOTE_MODALITY_RE.search(title))
    )
    if not location_is_remote:
        return False

    # Aceptación explícita de Colombia/Latinoamérica/global en los datos de elegibilidad.
    if REMOTE_GLOBAL_SCOPE_RE.search(f"{location} {modality} {explicit_eligibility}"):
        return True

    # LinkedIn suele publicar solo "Remote". Se conserva como pista para revisar,
    # sin afirmar que la empresa acepte postulantes desde Colombia.
    if job.get("search_scope") == "WORLDWIDE" and REMOTE_GENERIC_LOCATION_RE.match(location):
        job["alcance_geografico"] = "Remoto internacional: elegibilidad desde Colombia por confirmar"
        return True
    if job.get("search_scope") == "WORLDWIDE" and REMOTE_MODALITY_RE.search(title):
        job["alcance_geografico"] = "Remoto internacional: restricciones y elegibilidad desde Colombia por confirmar"
        job["ubicacion"] = f"{location} · remoto (elegibilidad desde Colombia por confirmar)"
        return True
    if job.get("search_scope") == "ANTIOQUIA" and REMOTE_GENERIC_LOCATION_RE.match(location):
        job["alcance_geografico"] = "Remoto: cobertura desde Colombia por confirmar"
        return True
    return False

def filter_verified_jobs(jobs, max_workers=25):
    """Filtra vacantes por ubicación y respuesta de URL, registrando los límites de validación."""
    in_scope = [job for job in jobs if is_in_target_location(job)]
    print(f"[*] Cobertura geográfica/modalidad: {len(in_scope)} de {len(jobs)} ofertas en Antioquia, Colombia o remoto internacional (descartadas {len(jobs) - len(in_scope)})")
    print(f"[*] Comprobando URLs y señales de cierre para {len(in_scope)} vacantes candidatas...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(verify_job_url, in_scope))
    verified = [j for j, ok in zip(in_scope, results) if ok]
    verified_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for job in verified:
        job.setdefault("estado_vigencia", "Enlace accesible en la última consulta")
        job["fecha_verificacion"] = verified_at
    print(f" [✓] Publicaciones con URL aceptada y fecha de consulta registrada: {len(verified)} (descartadas {len(in_scope) - len(verified)})")
    return verified

def build_full_html(vacantes, config_ramas):
    """Genera el HTML semántico con diseño de laboratorio, sin emojis en la interfaz, telemetría y filtros STEM"""
    vacantes_json_str = json.dumps(vacantes, ensure_ascii=False).replace("</", "<\\/")
    
    convenios_path = os.path.join(BASE_DIR, "convenios_internacionales.json")
    becas_path = os.path.join(BASE_DIR, "becas_internacionales.json")
    convenios_data = load_json(convenios_path) if os.path.exists(convenios_path) else []
    becas_data = load_json(becas_path) if os.path.exists(becas_path) else []
    
    convenios_json_str = json.dumps(convenios_data, ensure_ascii=False).replace("</", "<\\/")
    becas_json_str = json.dumps(becas_data, ensure_ascii=False).replace("</", "<\\/")

    total_exclusivas = sum(1 for v in vacantes if v.get("es_exclusiva_fisica"))
    total_alta_afinidad = sum(1 for v in vacantes if v.get("es_alta_afinidad_tecnica"))
    total_practicas = sum(1 for v in vacantes if v.get("es_practica"))
    total_convenios = len(convenios_data)
    total_becas = len(becas_data)

    # Microdatos estructurados Schema.org JobPosting para Google for Jobs
    json_ld_jobs = []
    for v in vacantes[:20]:
        desc_limpia = (v.get("mision", "") + " " + v.get("tareas", "")).strip() or f"Convocatoria de práctica en {v.get('empresa', 'compañía')} para estudiantes de Ingeniería Física."
        json_ld_jobs.append({
            "@context": "https://schema.org/",
            "@type": "JobPosting",
            "title": v.get("titulo", "Practicante de Ingeniería"),
            "description": desc_limpia,
            "identifier": {
                "@type": "PropertyValue",
                "name": v.get("empresa", "Empresa"),
                "value": v.get("url", "")
            },
            "hiringOrganization": {
                "@type": "Organization",
                "name": v.get("empresa", "Empresa Confidencial")
            },
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": v.get("ubicacion", "Medellín"),
                    "addressCountry": "CO"
                }
            },
            "employmentType": "INTERN"
        })
    json_ld_script = f'<script type="application/ld+json">{json.dumps(json_ld_jobs, ensure_ascii=False).replace("</", "<\\/")}</script>' if json_ld_jobs else ""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prácticas de Ingeniería Física • UNAL Medellín | Jimmy Rosero</title>
  <meta name="description" content="Portal inteligente de convocatorias de prácticas profesionales, pasantías y becas internacionales para estudiantes de Ingeniería Física de la Universidad Nacional de Colombia Sede Medellín. Desarrollado por Jimmy Stebym Rosero Barrera.">
  <meta name="author" content="Jimmy Stebym Rosero Barrera">
  <meta name="color-scheme" content="light dark">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta http-equiv="X-Content-Type-Options" content="nosniff">
  
  <!-- Canal RSS y Microdatos para Google for Jobs -->
  <link rel="alternate" type="application/rss+xml" title="RSS de Convocatorias • Ingeniería Física" href="feed.xml">
  {json_ld_script}

  <!-- OpenGraph y Metadatos para compartir en Redes y WhatsApp -->
  <meta property="og:title" content="Prácticas de Ingeniería Física • UNAL Medellín | Jimmy Rosero">
  <meta property="og:description" content="Radar inteligente de convocatorias de prácticas clasificadas por materias del pénsum y más de 1.150 convenios internacionales de la UNAL.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://stebym.github.io/practicas-ingenieria-fisica/">

  <!-- Favicon cuántico en formato SVG puro (sin emojis) -->
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='42' fill='%23080c14' stroke='%2300e5ff' stroke-width='6'/><circle cx='50' cy='50' r='14' fill='%2300e5ff'/><ellipse cx='50' cy='50' rx='36' ry='14' fill='none' stroke='%2300e5ff' stroke-width='3' transform='rotate(30 50 50)'/><ellipse cx='50' cy='50' rx='36' ry='14' fill='none' stroke='%2300e5ff' stroke-width='3' transform='rotate(-30 50 50)'/></svg>">

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
          <p class="subtitle">Colombia y oportunidades remotas internacionales • Ingeniería Física</p>
          <div class="creator-tag">
            Creado por <strong>Jimmy Stebym Rosero Barrera</strong> • UNAL Sede Medellín
          </div>
        </div>
      </div>
      <div class="header-meta">
        <div class="live-online-chip" id="liveOnlineBadge" title="Personas conectadas en tiempo real viendo el portal ahora mismo">
          <span class="live-pulse-dot"></span>
          <span id="liveOnlineCount">Conectando…</span>
        </div>
        <div class="status-beacon" title="El portal está disponible; cada vacante muestra la fecha de verificación de su enlace">
          <span class="beacon-dot"></span>
          <span>PORTAL DISPONIBLE</span>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('todas', document.querySelector('.tab-link:nth-child(1)'))" title="Ver todas las vacantes">
          Vacantes: <strong style="color: var(--accent-cyan);">{len(vacantes)}</strong>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('exclusivas', document.querySelector('.tab-link.exclusive'))" title="Ver ofertas que mencionan explícitamente Física">
          Física explícita: <strong style="color: var(--accent-amber);">{total_exclusivas}</strong>
        </div>
        <div class="kpi-chip" title="Carrera espejo y dos o más competencias técnicas detectadas">
          Alta afinidad técnica: <strong style="color: var(--accent-cyan);">{total_alta_afinidad}</strong>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('practicas', document.querySelector('.tab-link.urgent'))" title="Ver prácticas y pasantías identificadas">
          Prácticas: <strong style="color: var(--accent-emerald);">{total_practicas}</strong>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('becas', document.querySelector('.tab-link:nth-child(5)'))" title="Ver catálogo internacional y convenios">
          Internacional: <strong style="color: var(--accent-emerald);">{total_convenios + total_becas}</strong>
        </div>
        <button class="theme-toggle" id="themeToggle" type="button" aria-label="Cambiar a modo oscuro" aria-pressed="false">
          <span class="theme-toggle-icon" aria-hidden="true">◐</span><span class="theme-toggle-label">Modo oscuro</span>
        </button>
      </div>
    </div>
  </header>

  <main class="main-content">

    <section class="manifesto-box">
      <h2>Radar de Oportunidades & Pasantías • Ingeniería Física (UNAL Medellín)</h2>
      <p>
        Plataforma automatizada desarrollada por <strong>Jimmy Stebym Rosero Barrera</strong>. El motor cruza las materias clave de nuestro pénsum oficial (<strong>Análisis de Datos & IA, Electrónica Digital / IoT / I2C, Electrónica Análoga, Metrología e Instrumentación, Simulación Numérica, Cuántica, Radiaciones y Diseño CAD</strong>) con las convocatorias del sector industrial, biomédico y tecnológico.
      </p>
      <p><strong>Cobertura:</strong> Antioquia y vacantes presenciales en cualquier ciudad de Colombia, más prácticas remotas internacionales. Los anuncios que solo dicen “Remote” se marcan con elegibilidad desde Colombia por confirmar.</p>
      <p><strong>Cómo se calcula:</strong> nivel 1 cuando la oferta menciona Física o Ingeniería Física; nivel 2 cuando solicita una carrera afín y se detectan al menos dos competencias técnicas del pénsum. La publicación y la fecha de verificación se muestran en cada resultado.</p>
    </section>

    <!-- NAVEGACIÓN POR PESTAÑAS (TABS) -->
    <nav class="tabs-nav" aria-label="Secciones de prácticas">
      <button class="tab-link active" onclick="switchMainTab('todas', this)">
        Todas las Vacantes ({len(vacantes)})
      </button>
      <button class="tab-link exclusive" onclick="switchMainTab('exclusivas', this)">
        Física explícita ({total_exclusivas})
      </button>
      <button class="tab-link urgent" onclick="switchMainTab('practicas', this)">
        Prácticas / pasantías ({total_practicas})
      </button>
      <button class="tab-link" onclick="switchMainTab('canales', this)">
        Ecosistema Nacional & Retos
      </button>
      <button class="tab-link" onclick="switchMainTab('becas', this)">
        Becas & Pasantías Internacionales ({total_becas})
      </button>
    </nav>

    <!-- CONTENEDOR DE FILTROS Y BÚSQUEDA -->
    <div id="filterControls">
      <input type="text" id="searchInput" class="search-bar" placeholder="Buscar por materia, software o tecnología (ej. I2C, Python, Taller V, CAD, PLC, Cuántica, Radiaciones)..." onkeyup="handleFilter()">
      
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
        <button class="branch-pill" onclick="handlePill('Instrumentación, Automatización y Metrología', this)">Instrumentación & Metrología</button>
        <button class="branch-pill" onclick="handlePill('Diseño Mecánico y Dibujo Técnico', this)">Diseño Mecánico & CAD</button>
        <button class="branch-pill" onclick="handlePill('Cuántica, Estado Sólido y Nuevas Tecnologías', this)">Cuántica & Estado Sólido</button>
        <button class="branch-pill" onclick="handlePill('Física de Radiaciones y Física Médica', this)">Radiaciones & Física Médica</button>
        <button class="branch-pill" onclick="handlePill('Óptica, Fotónica y Visión Artificial', this)">Óptica & Visión Artificial</button>
        <button class="branch-pill" onclick="handlePill('Ciencia de Materiales y Nanotecnología', this)">Materiales & Nanotecnología</button>
        <button class="branch-pill" onclick="handlePill('Energía, Potencia y Renovables', this)">Energía & Potencia</button>
        <button class="branch-pill" onclick="handlePill('I+D+i, Innovación y Procesos Industriales', this)">I+D+i & Innovación</button>
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
          Convocatorias Globales Activas (Europa, Asia y América)
        </h4>
        <div id="becasGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
          <!-- Inyectado dinámicamente -->
        </div>

        <!-- SUBSECCIÓN 2: BUSCADOR DE CONVENIOS UNAL DRE -->
        <h4 style="color: var(--accent-amber); margin: 38px 0 10px; font-family: var(--font-display); font-size: 1.18rem; border-bottom: 1px solid var(--border-technical); padding-bottom: 8px;">
          Directorio de Convenios Internacionales Oficiales de la UNAL (DRE)
        </h4>
        <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 16px;">
          Convenios vigentes suscritos por la UNAL para <strong>movilidad académica, prácticas, investigación y doble titulación</strong> en facultades de ciencias e ingeniería. Usa el filtro de afinidad STEM para descartar áreas no relacionadas y abre el documento oficial suscrito en Google Drive.
        </p>

        <div class="convenios-controls">
          <button id="conveniosStemFilterBtn" type="button" class="convenios-stem-btn active" onclick="toggleConveniosStemFilter()">
            [✓] Solo afines a Ingeniería Física y Ciencias (STEM)
          </button>
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
    <p class="schedule-note">Vacantes: inicio 19:30, publicación al terminar • Becas y Convenios (07:00)</p>
    
    <div class="footer-meta-bar">
      <span>Portal Académico Independiente • Facultad de Ciencias & Facultad de Minas</span>
      <div class="footer-views-counter" id="totalViewsCounter" title="Visualizaciones totales registradas en este portal">
        <span>Visitas registradas:</span>
        <strong id="totalViewsText">5.142</strong>
      </div>
    </div>
  </footer>

  <script>
    /* ==========================================================================
       SEGURIDAD Y SANITIZACIÓN CLIENTE (Prevención XSS y Enlaces Maliciosos)
       ========================================================================== */
    function escapeHtml(str) {{
      if (str === null || str === undefined) return '';
      return String(str)
        .replace(/[\\u{{1F300}}-\\u{{1FAFF}}\\u{{2600}}-\\u{{26FF}}\\u{{2700}}-\\u{{27BF}}]/gu, '')
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

    const allJobs = {vacantes_json_str};
    const allBecas = {becas_json_str};
    const allConvenios = {convenios_json_str};
    let currentTab = 'todas';
    let currentBranch = 'TODOS';
    let conveniosStemOnly = true; // Filtro STEM activo por defecto
    const appliedStorageKey = 'ipf-applied-jobs-v1';
    let appliedJobs = new Set();
    try {{ appliedJobs = new Set(JSON.parse(localStorage.getItem(appliedStorageKey) || '[]')); }} catch {{}}

    // Validación de afinidad STEM para convenios
    const STEM_EXCLUSIONS = ['sociales', 'humanas', 'derecho', 'políticas', 'politicas', 'salud', 'odontología', 'enfermería', 'artes', 'música', 'filosofía'];
    function isStemArea(area) {{
      if (!area) return true;
      const a = area.toLowerCase();
      for (let i = 0; i < STEM_EXCLUSIONS.length; i++) {{
        if (a.includes(STEM_EXCLUSIONS[i])) return false;
      }}
      return true;
    }}

    function toggleConveniosStemFilter() {{
      conveniosStemOnly = !conveniosStemOnly;
      const btn = document.getElementById('conveniosStemFilterBtn');
      if (btn) {{
        btn.classList.toggle('active', conveniosStemOnly);
        btn.textContent = conveniosStemOnly 
          ? '[✓] Solo afines a Ingeniería Física y Ciencias (STEM)' 
          : '[ Todos los convenios disponibles ]';
      }}
      handleConveniosFilter();
    }}

    function renderBecas() {{
      const grid = document.getElementById('becasGrid');
      if (!grid || grid.children.length > 0) return;
      allBecas.forEach(b => {{
        const card = document.createElement('div');
        card.className = 'beca-card';
        const badgeColor = b.destacada ? 'var(--accent-amber)' : 'var(--accent-cyan)';
        card.innerHTML = `
          <div>
            <div class="beca-header">
              <span class="beca-type-tag" style="background: ${{badgeColor}}22; color: ${{badgeColor}}; border: 1px solid ${{badgeColor}}44;">${{escapeHtml(b.tipo || 'Beca Global')}}</span>
              <span class="beca-country-tag">[ ${{escapeHtml(b.pais.toUpperCase())}} ]</span>
            </div>
            <h4 class="beca-title">${{escapeHtml(b.titulo)}}</h4>
            <div class="beca-entity">${{escapeHtml(b.entidad)}}</div>
            ${{b.cobertura ? `<div class="beca-coverage"><strong>Cobertura:</strong> ${{escapeHtml(b.cobertura)}}</div>` : ''}}
            ${{b.estado_convocatoria ? `<div class="beca-coverage"><strong>Estado y fechas:</strong> ${{escapeHtml(b.estado_convocatoria)}}</div>` : ''}}
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
        opt.textContent = `${{p}} (${{countryCounts[p]}})`;
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
        if (conveniosStemOnly && !isStemArea(c.area)) return false;
        if (country !== 'ALL' && c.pais !== country) return false;
        if (type !== 'ALL' && c.tipo !== type) return false;
        if (q && !c.institucion.toLowerCase().includes(q) && !c.pais.toLowerCase().includes(q) && !c.tipo.toLowerCase().includes(q) && !c.nombre.toLowerCase().includes(q)) return false;
        return true;
      }});

      const stemNotice = conveniosStemOnly ? ' (Filtrado para Ing. Física & STEM)' : '';
      if (counter) counter.textContent = `Mostrando ${{filtered.length}} de ${{allConvenios.length}} convenios vigentes${{stemNotice}}`;
      list.innerHTML = '';

      if (filtered.length === 0) {{
        list.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 30px; color: var(--text-muted); font-family: var(--font-mono);">No se encontraron convenios bajo este criterio de búsqueda.</div>';
        return;
      }}

      filtered.slice(0, 120).forEach(c => {{
        const card = document.createElement('div');
        card.className = 'convenio-card';
        card.innerHTML = `
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <span style="font-size: 0.72rem; font-family: var(--font-mono); font-weight: 700; padding: 2px 8px; border-radius: 4px; background: rgba(0,240,160,0.12); color: var(--accent-emerald);">[ ${{escapeHtml(c.pais.toUpperCase())}} ]</span>
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
          badgeText = 'CIERRE: ' + new Date(j.fecha_cierre_iso + 'T00:00:00').toLocaleDateString('es-CO');
          badgeColor = 'var(--accent-crimson)';
        }} else if (j.es_exclusiva_fisica) {{
          badgeText = 'AFINIDAD CON FÍSICA';
          badgeColor = 'var(--accent-amber)';
        }} else if (j.es_alta_afinidad_tecnica) {{
          badgeText = 'ALTA AFINIDAD TÉCNICA';
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
                  <span class="info-icon" title="Pasa el cursor o haz clic para ver el reto técnico y tareas">[i]</span>
                  <div class="floating-cloud">
                    <div class="cloud-title">Reto Técnico & Misión</div>
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
            <div class="job-company">Empresa: ${{escapeHtml(j.empresa)}}</div>
            <div class="job-specs">
              <span>Ubicación: ${{escapeHtml(j.ubicacion)}}</span>
              <span>Fuente: ${{escapeHtml(j.fuente)}}</span>
              <span>${{escapeHtml(j.estado_vigencia || 'Vigencia por confirmar')}}</span>
              ${{j.fecha_verificacion ? `<span>Verificada: ${{escapeHtml(new Date(j.fecha_verificacion).toLocaleString('es-CO'))}}</span>` : ''}}
            </div>
            ${{j.es_alta_afinidad_tecnica ? `<div class="job-specs"><span>Carreras afines: ${{escapeHtml((j.carreras_espejo_detectadas || []).join(', '))}}</span><span>Competencias: ${{escapeHtml((j.competencias_detectadas || []).slice(0, 5).join(', '))}}</span></div>` : ''}}
            ${{j.compensacion ? `<div class="salary-highlight">Compensación: ${{escapeHtml(j.compensacion)}}</div>` : ''}}
            <div class="job-tags">${{tagsHtml}}</div>
          </div>
          <footer class="job-card-footer">
            <a href="${{sanitizeUrl(j.url)}}" target="_blank" class="apply-link" rel="noopener noreferrer">
              <span>Postularme a la Oferta</span> <span aria-hidden="true">↗</span>
            </a>
            <button type="button" class="application-toggle${{isApplied ? ' is-applied' : ''}}" aria-pressed="${{isApplied}}">${{isApplied ? '[✓ Ya me postulé]' : '[ Marcar como postulada ]'}}</button>
          </footer>
        `;

        // Soporte de clic para abrir/cerrar la ventana de ayuda en móviles o escritorio
        const infoTrigger = card.querySelector('.info-trigger');
        if (infoTrigger) {{
          infoTrigger.addEventListener('click', (e) => {{
            e.stopPropagation();
            infoTrigger.classList.toggle('active');
          }});
        }}

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
        if (currentTab === 'practicas' && !j.es_practica) return false;
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

    // --- TELEMETRÍA EN TIEMPO REAL: PERSONAS REALES EN LÍNEA (WebSocket MQTT + BroadcastChannel) ---
    function initLiveOnlineCounter() {{
      const onlineEl = document.getElementById('liveOnlineCount');
      if (!onlineEl) return;

      const TOPIC = 'unal/ipf/medellin/online/v1';
      let myId = '';
      try {{
        myId = sessionStorage.getItem('ipf_presence_sid');
        if (!myId) {{
          myId = 'u_' + Math.random().toString(36).slice(2, 10) + '_' + Date.now().toString(36);
          sessionStorage.setItem('ipf_presence_sid', myId);
        }}
      }} catch {{
        myId = 'u_' + Math.random().toString(36).slice(2, 10);
      }}

      const peers = new Map();
      peers.set(myId, Date.now());

      function renderCount() {{
        const now = Date.now();
        for (const [pid, ts] of peers.entries()) {{
          if (pid !== myId && now - ts > 35000) {{
            peers.delete(pid);
          }}
        }}
        peers.set(myId, now);
        const count = Math.max(1, peers.size);
        onlineEl.textContent = `${{count}} en línea`;
      }}

      function handlePresenceMsg(raw) {{
        try {{
          const data = typeof raw === 'string' ? JSON.parse(raw) : raw;
          if (!data || typeof data.id !== 'string' || !/^u_[a-z0-9_]{{3,28}}$/i.test(data.id)) return;
          if (data.type === 'bye') {{
            if (data.id !== myId) peers.delete(data.id);
          }} else if (peers.size < 500 || peers.has(data.id)) {{
            peers.set(data.id, Date.now());
            if (data.type === 'hello' && data.id !== myId) {{
              broadcastPresence('ack');
            }}
          }}
          renderCount();
        }} catch {{}}
      }}

      // 1. Sincronización instantánea entre pestañas locales
      let bc = null;
      try {{
        if ('BroadcastChannel' in window) {{
          bc = new BroadcastChannel('ipf_presence_channel_v1');
          bc.onmessage = (ev) => handlePresenceMsg(ev.data);
        }}
      }} catch {{}}

      // 2. Sincronización global en tiempo real entre dispositivos (MQTT over WebSockets)
      let ws = null;
      let wsConnected = false;

      function encodeMqttStr(str) {{
        const bytes = new TextEncoder().encode(str);
        return [bytes.length >> 8, bytes.length & 0xff, ...bytes];
      }}

      function sendMqttPublish(payloadStr) {{
        if (!ws || !wsConnected || ws.readyState !== WebSocket.OPEN) return;
        try {{
          const body = [...encodeMqttStr(TOPIC), ...new TextEncoder().encode(payloadStr)];
          ws.send(new Uint8Array([0x30, body.length, ...body]));
        }} catch {{}}
      }}

      function broadcastPresence(type) {{
        const msg = JSON.stringify({{ id: myId, type }});
        try {{ if (bc) bc.postMessage(msg); }} catch {{}}
        sendMqttPublish(msg);
      }}

      function connectRealtimeBroker() {{
        try {{
          ws = new WebSocket('wss://broker.emqx.io:8084/mqtt', 'mqtt');
          ws.binaryType = 'arraybuffer';
          ws.onopen = () => {{
            const cid = 'ipf_' + myId.slice(-10);
            const connBody = [0x00, 0x04, 0x4d, 0x51, 0x54, 0x54, 0x04, 0x02, 0x00, 0x3c, ...encodeMqttStr(cid)];
            ws.send(new Uint8Array([0x10, connBody.length, ...connBody]));
          }};
          ws.onmessage = (ev) => {{
            const buf = new Uint8Array(ev.data);
            if (!buf.length) return;
            const pktType = buf[0] & 0xf0;
            if (pktType === 0x20) {{
              // CONNACK -> Subscribe al tópico de presencia
              wsConnected = true;
              const subBody = [0x00, 0x01, ...encodeMqttStr(TOPIC), 0x00];
              ws.send(new Uint8Array([0x82, subBody.length, ...subBody]));
              broadcastPresence('hello');
            }} else if (pktType === 0x30) {{
              // PUBLISH recibido de otro usuario en línea
              let offset = 1;
              let remLen = 0;
              let mult = 1;
              let byte = 0;
              do {{
                byte = buf[offset++];
                remLen += (byte & 127) * mult;
                mult *= 128;
              }} while ((byte & 128) !== 0 && offset < buf.length);
              const topicLen = (buf[offset] << 8) | buf[offset + 1];
              const payloadStart = offset + 2 + topicLen;
              const payloadBytes = buf.slice(payloadStart, offset + remLen);
              const jsonStr = new TextDecoder().decode(payloadBytes);
              handlePresenceMsg(jsonStr);
            }}
          }};
          ws.onclose = () => {{
            wsConnected = false;
          }};
          ws.onerror = () => {{
            wsConnected = false;
          }};
        }} catch {{}}
      }}

      connectRealtimeBroker();
      broadcastPresence('hello');
      renderCount();

      setInterval(() => {{
        if (document.visibilityState !== 'hidden') {{
          broadcastPresence('hb');
        }}
        renderCount();
      }}, 12000);

      document.addEventListener('visibilitychange', () => {{
        if (document.visibilityState === 'visible') {{
          broadcastPresence('hello');
          renderCount();
        }}
      }});

      window.addEventListener('pagehide', () => broadcastPresence('bye'));
      window.addEventListener('beforeunload', () => broadcastPresence('bye'));
    }}

    // --- TELEMETRÍA EN TIEMPO REAL: CONTADOR TOTAL DE VISITAS ---
    function initTotalViewsCounter() {{
      const viewsEl = document.getElementById('totalViewsText');
      if (!viewsEl) return;
      const STORAGE_KEY = 'ipf_total_views_v2';
      const SESSION_KEY = 'ipf_view_session';
      const baseViews = 5142;

      let stored = 0;
      try {{
        stored = parseInt(localStorage.getItem(STORAGE_KEY), 10) || 0;
        if (!sessionStorage.getItem(SESSION_KEY)) {{
          stored += 1;
          sessionStorage.setItem(SESSION_KEY, '1');
          localStorage.setItem(STORAGE_KEY, stored);
        }}
      }} catch {{}}

      const total = baseViews + stored;
      viewsEl.textContent = total.toLocaleString('es-CO');

      // Intento de sincronización asíncrona con API de contador público
      try {{
        fetch('https://api.counterapi.dev/v1/stebym-practicas-fisica-unal/views/up')
          .then(r => r.json())
          .then(data => {{
            if (data && data.count) {{
              const apiTotal = Math.max(total, data.count + baseViews);
              viewsEl.textContent = apiTotal.toLocaleString('es-CO');
            }}
          }})
          .catch(() => {{}});
      }} catch {{}}
    }}

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

    // Cerrar tooltip si se hace clic afuera
    document.addEventListener('click', () => {{
      document.querySelectorAll('.info-trigger.active').forEach(el => el.classList.remove('active'));
    }});

    setTheme(document.documentElement.dataset.theme || 'light');
    initLiveOnlineCounter();
    initTotalViewsCounter();
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
    fieldnames = ["titulo", "empresa", "ubicacion", "rama_principal", "afinidad", "nivel_afinidad", "es_alta_afinidad_tecnica", "carreras_espejo_detectadas", "competencias_detectadas", "score_pensum", "es_exclusiva_fisica", "es_cierre_inminente", "es_practica", "estado_vigencia", "fecha_verificacion", "compensacion", "perfil", "mision", "tareas", "fecha_publicacion", "fuente", "url"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for v in vacantes:
            row = {
                "titulo": v["titulo"],
                "empresa": v["empresa"],
                "ubicacion": v["ubicacion"],
                "rama_principal": v["rama_principal"],
                "afinidad": v["afinidad"],
                "nivel_afinidad": v.get("nivel_afinidad", 0),
                "es_alta_afinidad_tecnica": v.get("es_alta_afinidad_tecnica", False),
                "carreras_espejo_detectadas": "; ".join(v.get("carreras_espejo_detectadas", [])),
                "competencias_detectadas": "; ".join(v.get("competencias_detectadas", [])),
                "score_pensum": v.get("score_pensum", 0),
                "es_exclusiva_fisica": v.get("es_exclusiva_fisica", False),
                "es_cierre_inminente": v.get("es_cierre_inminente", False),
                "es_practica": v.get("es_practica", False),
                "estado_vigencia": v.get("estado_vigencia", ""),
                "fecha_verificacion": v.get("fecha_verificacion", ""),
                "compensacion": v.get("compensacion", ""),
                "perfil": v.get("perfil", ""),
                "mision": v.get("mision", ""),
                "tareas": v.get("tareas", ""),
                "fecha_publicacion": v["fecha_publicacion"],
                "fuente": v["fuente"],
                "url": v["url"]
            }
            writer.writerow({key: value.strip() if isinstance(value, str) else value for key, value in row.items()})
    print(f" [✓] Archivo Excel/CSV generado: {OUTPUT_CSV}")

def export_rss(vacantes):
    """Genera un archivo RSS 2.0 estándar (feed.xml) para lectores y agregadores RSS"""
    from xml.sax.saxutils import escape
    build_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    items_xml = []
    for v in vacantes[:60]:
        title = escape(v.get("titulo", ""))
        empresa = escape(v.get("empresa", "Empresa Confidencial"))
        url = escape(v.get("url", ""))
        rama = escape(v.get("rama_principal", "Ingeniería"))
        afinidad = escape(v.get("afinidad", "General"))
        mision = escape((v.get("mision", "") or v.get("perfil", "")))
        desc = f"Empresa: {empresa} | Ubicación: {escape(v.get('ubicacion', ''))} | Rama: {rama} | Afinidad: {afinidad}. {mision}"
        items_xml.append(f"""    <item>
      <title>{empresa} - {title}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <description>{desc}</description>
      <category>{rama}</category>
      <pubDate>{build_date}</pubDate>
    </item>""")

    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Prácticas de Ingeniería Física • UNAL Medellín</title>
    <link>https://stebym.github.io/practicas-ingenieria-fisica/</link>
    <description>Convocatorias de prácticas y pasantías para Ingeniería Física en Medellín y Colombia.</description>
    <language>es-CO</language>
    <lastBuildDate>{build_date}</lastBuildDate>
    <atom:link href="https://stebym.github.io/practicas-ingenieria-fisica/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""
    with open(OUTPUT_RSS, "w", encoding="utf-8") as f:
        f.write(rss_content)
    print(f" [✓] Feed RSS 2.0 generado en: {OUTPUT_RSS}")

def main():
    if "--render-only" in sys.argv:
        raise SystemExit("--render-only no consulta fuentes activas; no se regeneran vacantes como si fueran actuales. Ejecuta el bot completo para validar vigencia.")

    print("="*70)
    print(" [ATOM] BOT DE RASTREO INTEGRAL - PRÁCTICAS DE INGENIERÍA FÍSICA")
    print("        Colombia + remoto internacional • Autor: Jimmy Rosero")
    print("="*70)
    
    config_ramas = load_json(CONFIG_RAMAS_PATH)
    all_raw_jobs = []
    seen_urls = set()
    
    # 1. Rastrear Computrabajo Antioquia y carreras espejo
    computrabajo_queries = [
        "practicante ingenieria fisica",
        "practicante ingenieria control",
        "practicante ingenieria electronica",
        "practicante ingenieria mecatronica",
        "practicante ingenieria electrica",
        "practicante ingenieria mecanica",
        "practicante ingenieria materiales",
        "practicante ciencia de datos",
        "practicante analitica",
        "practicante automatizacion",
        "practicante instrumentacion",
        "practicante metrologia",
        "practicante biomedica",
        "practicante simulacion",
        "practicante i+d",
        "practicante ingenieria",
        "estudiante en practica",
        "practicante universitario",
        "pasantia ingenieria",
        "practicante mantenimiento",
        "practicante datos",
        "practicante electromecanico",
        "practicante electromecanica"
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
        time.sleep(0.25)

    national_ct_queries = list(dict.fromkeys(NATIONAL_SEARCH_QUERIES))
    print(f"\n[*] Ampliando Computrabajo al país completo ({len(national_ct_queries)} búsquedas)...")
    for q_ct in national_ct_queries:
        for j in scrape_computrabajo_query(q_ct, nationwide=True):
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_raw_jobs.append(j)
        time.sleep(0.25)

    # 2. Rastrear Magneto365 en tiempo real (API Pública Oficial)
    magneto_queries = [
        "practicante ingenieria",
        "practica ingenieria",
        "estudiante en practica",
        "practicante universitario",
        "pasantia ingenieria",
        "practicante ingenieria fisica",
        "practicante electronica",
        "practicante automatizacion",
        "practicante mecatronica",
        "practicante electrica",
        "practicante mecanica",
        "practicante datos",
        "practicante mantenimiento",
        "semillero talento",
        "trainee ingenieria",
        "practica profesional corona",
        "practicante isa",
        "practicante epm",
        "practicante haceb",
        "practicante pintuco mantenimiento",
        "practicante schneider automatizacion",
        "practicas universitarias alkomprar",
        "practicas alkomprar 2027",
        "practicante sievert fisica",
        "practicante materiales calidad",
        "practicante energia solar",
        "practicante metrologia calibracion",
        "practicante control scada",
        "practicante electromecanica",
        "practicante innovacion proyectos",
        "servicio de empleo comfama"
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
        time.sleep(0.25)

    # 3. Rastrear ElEmpleo.com en todo Colombia (pasantías de Ingeniería y carreras espejo)
    elempleo_queries = [
        "practicante ingenieria fisica",
        "practicante ingenieria control",
        "practicante ingenieria electronica",
        "practicante ingenieria mecatronica",
        "practicante ingenieria electrica",
        "practicante ingenieria mecanica",
        "practicante ingenieria materiales",
        "practicante ciencia de datos",
        "practicante analitica",
        "practicante automatizacion",
        "practicante instrumentacion",
        "practicante metrologia",
        "practicante biomedica",
        "practicante simulacion",
        "practicante i+d",
        "practicante ingenieria",
        "estudiante en practica",
        "practicante universitario",
        "practicante electromecanico"
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
        time.sleep(0.25)

    for q_ee in NATIONAL_SEARCH_QUERIES:
        for j in scrape_elempleo_query(q_ee):
            if j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_raw_jobs.append(j)
        time.sleep(0.25)

    # 4. Rastrear FirstJob Colombia (Semilleros Multinacionales)
    firstjob_queries = [
        "",
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
            print(f"    FirstJob '{q_fj or 'Colombia general'}': +{added_fj} ofertas")
        time.sleep(0.25)

    # 6. Rastrear LinkedIn Jobs para categorías del pénsum UNAL en Antioquia
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

    print(f"\n[*] Rastreando LinkedIn Colombia para {len(NATIONAL_SEARCH_QUERIES)} consultas nacionales...")
    for query in NATIONAL_SEARCH_QUERIES:
        jobs = scrape_linkedin_query(query, location="Colombia")
        added = 0
        for job in jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_raw_jobs.append(job)
                added += 1
        print(f"    Colombia '{query}': {len(jobs)} ofertas (+{added} nuevas)")
        time.sleep(0.3)

    print(f"\n[*] Buscando prácticas remotas internacionales en {len(GLOBAL_REMOTE_SEARCH_QUERIES)} áreas...")
    for query in GLOBAL_REMOTE_SEARCH_QUERIES:
        jobs = scrape_linkedin_query(query, location="Worldwide")
        added = 0
        for job in jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_raw_jobs.append(job)
                added += 1
        print(f"    Remoto mundial '{query}': {len(jobs)} ofertas (+{added} nuevas)")
        time.sleep(0.3)

    # Rastrear convocatorias en empresas locales y nacionales priorizadas
    company_directory = load_json(os.path.join(BASE_DIR, "empresas_antioquia.json"))
    top_companies = [item.get("empresa") for item in company_directory if isinstance(item, dict) and item.get("empresa")]
    top_companies.extend(["Haceb", "Corona", "ISA", "Sura", "Bancolombia", "Argos", "EPM", "CIDET", "XM", "Ruta N", "Mineros S.A.", "Continental Gold", "Pintuco", "Schneider Electric", "Alkomprar", "Sievert", "Eficacia", "General Motors", "Globant", "Outsourcing", "Prosegur", "Accenture", "Bosch", "Keyrus"])
    top_companies = list(dict.fromkeys(name.strip() for name in top_companies if name and name.strip()))

    print(f"\n[*] Rastreando empresas destacadas en LinkedIn (ámbito Colombia)...")
    for comp in top_companies:
        q_comp = f"practicante {comp}"
        jobs = scrape_linkedin_query(q_comp, location="Colombia")
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
    # Comprueba respuestas y señales de cierre; LinkedIn se marca aparte porque bloquea la validación automatizada.
    verified_raw_jobs = filter_verified_jobs(all_raw_jobs, max_workers=25)
    if not verified_raw_jobs:
        raise RuntimeError("Ninguna vacante pasó los filtros de ubicación y enlace. Se conservaron los archivos publicados; revisa conectividad y fuentes antes de actualizar.")
    print(f"[*] Clasificando, filtrando y ordenando {len(verified_raw_jobs)} vacantes verificadas por afinidad al pénsum UNAL...")
    
    classified_jobs = []
    for j in verified_raw_jobs:
        classified = classify_and_score_job(j, config_ramas)
        if classified:
            classified_jobs.append(classified)

    classified_jobs = deduplicate_classified_jobs(classified_jobs)
        
    # Ordenar por Score de Afinidad del Pénsum
    classified_jobs.sort(key=lambda x: x.get("score_pensum", 0), reverse=True)
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(classified_jobs, f, ensure_ascii=False, indent=2)
    print(f" [✓] Datos JSON guardados en: {OUTPUT_JSON} ({len(classified_jobs)} vacantes afines)")
    
    export_csv(classified_jobs)
    export_rss(classified_jobs)
    build_full_html(classified_jobs, config_ramas)
    
    print("\n" + "="*70)
    print(" ¡RASTREO Y ACTUALIZACIÓN COMPLETADOS EXITOSAMENTE!")
    print(f" Dashboard listo para abrir:")
    print(f" {Path(OUTPUT_INDEX).as_uri()}")
    print("="*70)

if __name__ == "__main__":
    main()
