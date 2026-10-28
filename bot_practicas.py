"""
=============================================================================
BOT DE RASTREO DE PRÁCTICAS - INGENIERÍA FÍSICA (UNAL MEDELLÍN) · PORTAL IPF
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Licencia: PolyForm Noncommercial 1.0.0 con descargo de responsabilidad (ver LICENSE)
=============================================================================
Rastrea prácticas en LinkedIn, Magneto365, Computrabajo, ElEmpleo, FirstJob,
portales corporativos y búsqueda web, y las prioriza según el pénsum de
Ingeniería Física UNAL.
Alcance: Antioquia con cualquier modalidad; fuera de Antioquia solo remoto o
híbrido; en el exterior solo remoto.
Salida: vacantes_practicas.json y vacantes_practicas.csv (la página la arma
bot_pagina.py).
"""

import os
import sys
import json
import csv
import re
import time
import threading
import unicodedata
from collections import Counter
from html import unescape
from datetime import datetime
from urllib.parse import quote, unquote, urlparse
import requests
import concurrent.futures

from busqueda_web import buscar_web
from firma import encabezado_bot, sellar_registros

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

# Antioquia se acepta con cualquier modalidad. "Caldas" solo cuenta junto a
# Antioquia para no confundir el municipio con el departamento de Caldas.
LOCAL_LOCATION_RE = re.compile(
    r"medell[ií]n|antioquia|valle de aburr[aá]|envigado|itag[uüíi]|\bbello\b|sabaneta|rionegro|"
    r"apartad[oó]|la estrella|copacabana|girardota|caldas,?\s*antioquia|marinilla|barbosa|cisneros|"
    r"el retiro|guarne|santo domingo|puerto berr[ií]o|la ceja|carmen de viboral|el santuario|"
    r"santa fe de antioquia|segovia|remedios|caucasia|yarumal|turbo|carepa|chigorod[oó]|"
    r"salgar|sons[oó]n|amag[aá]|fredonia|jeric[oó]|andes|urrao|zaragoza|el bagre|yond[oó]|"
    r"puerto nare|la uni[oó]n|san pedro de los milagros|donmat[ií]as|entrerr[ií]os|"
    r"santa rosa de osos|san jer[oó]nimo|sopetr[aá]n|buritic[aá]|briceño|ituango",
    re.IGNORECASE,
)
# Fuera de Antioquia (resto de Colombia o exterior) solo sirven prácticas
# remotas o híbridas.
REMOTE_MODALITY_RE = re.compile(
    r"\b(?:remot[oa]s?|remote|teletrabajo|trabajo\s+(?:en\s+casa|desde\s+casa)|home[\s-]?office|"
    r"work\s+from\s+home|h[ií]brid[oa]s?|hybrid|anywhere)\b",
    re.IGNORECASE,
)
REMOTE_ONLY_RE = re.compile(r"\b(?:remot[oa]s?|remote|teletrabajo|work\s+from\s+home|anywhere)\b", re.IGNORECASE)
REMOTE_WORLDWIDE_DESC_RE = re.compile(
    r"\b(?:fully\s+remote|100\s*%\s*remote|remote[\s-]first|remote\s+(?:position|role|internship|opportunity)|"
    r"work\s+remotely\s+from\s+anywhere|this\s+(?:is\s+a|role\s+is|position\s+is)\s+(?:fully\s+)?remote|"
    r"open\s+to\s+(?:candidates\s+in\s+)?latin\s+america|latam)\b",
    re.IGNORECASE,
)
REMOTE_NEGATION_RE = re.compile(
    r"\b(?:not\s+(?:a\s+)?remote|non[\s-]remote|no\s+remote|not\s+eligible\s+for\s+remote|"
    r"must\s+(?:be\s+)?(?:located|based|reside)\s+in\s+(?:the\s+)?(?:u\.?s\.?|united\s+states|india|china|canada|europe|germany)|"
    r"work\s+authori[sz]ation\s+in\s+the\s+(?:u\.?s|united\s+states))\b",
    re.IGNORECASE,
)
REMOTE_GLOBAL_SEARCH_QUERIES = [
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
    "remote internship anywhere engineering physics",
]

CARRERAS_ESPEJO_QUERIES = [
    "practicante ingenieria de control afines",
    "practicante ingenieria electronica afines",
    "practicante ingenieria mecatronica afines",
    "practicante ingenieria electrica afines",
    "practicante ingenieria mecanica afines",
    "practicante ingenieria materiales afines",
    "practicante ciencia de datos afines",
    "practicante analitica estadistica matematicas afines",
    "practicante automatizacion control afines",
    "practicante instrumentacion metrologia afines",
    "practicante ingenieria biomedica bioingenieria afines",
    "practicante simulacion modelado cuantitativo afines",
    "practicante ingenieria quimica materiales afines",
    "practicante telecomunicaciones optica afines",
]

# Búsquedas en todo Colombia: solo se publican si el aviso dice remoto o
# híbrido (se confirma leyendo la descripción completa de cada oferta).
REMOTE_COLOMBIA_QUERIES = [
    "practicante remoto",
    "practicante hibrido",
    "practicante ingenieria remoto",
    "practicante ingenieria hibrido",
    "practicante datos remoto",
    "practicante analitica hibrido",
    "practicante desarrollo python remoto",
    "practicante ingenieria fisica",
    "practicante fisica",
    "pasantia remota ingenieria",
    "intern remote Colombia",
    "practicante teletrabajo",
]

# Búsquedas web abiertas para encontrar convocatorias fuera de los portales
# que exponen APIs o páginas de resultados fáciles de rastrear.
WEB_SEARCH_QUERIES = [
    ("practicante ingeniería física Medellín", "LOCAL"),
    ("práctica profesional ingeniería carreras afines Medellín", "LOCAL"),
    ("practicante instrumentación automatización metrología Antioquia", "LOCAL"),
    ("practicante datos simulación ingeniería Antioquia afines", "LOCAL"),
    ("Nutresa aprendices practicantes 2027-1 Colombia", "LOCAL"),
    ("Alkomprar prácticas universitarias 2027-1 Medellín", "LOCAL"),
    ("convocatoria prácticas Distrito Medellín 2027-1", "LOCAL"),
    ("practicante ingeniería física remoto Colombia", "COLOMBIA"),
    ("práctica profesional ingeniería híbrida Colombia afines", "COLOMBIA"),
    ("internship engineering physics remote worldwide", "WORLDWIDE"),
    ("remote engineering internship Latin America", "WORLDWIDE"),
    ("remote internship Python data science international", "WORLDWIDE"),
    ("remote internship materials optics applied physics", "WORLDWIDE"),
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_RAMAS_PATH = os.path.join(BASE_DIR, "config_ramas.json")
CONVOCATORIAS_DESTACADAS_PATH = os.path.join(BASE_DIR, "convocatorias_destacadas.json")
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
    "programa mujer stem",
    # Convocatorias académicas con distintas etiquetas en Colombia y fuera.
    "practica profesional ingenieria",
    "practica academica ingenieria",
    "estudiante etapa practica ingenieria",
    "pasantia ingenieria",
    "engineering intern Colombia",
    "engineering internship student",
    "engineering co-op student",
    *CARRERAS_ESPEJO_QUERIES,
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
CONVOCATORIA_MUJERES_RE = re.compile(
    r"\b(?:solo|exclusiv[oa]mente|dirigid[oa]s?\s+(?:a|para)|women\s+only|for\s+women)\b.{0,60}\b(?:mujeres|women|femenin[ao]?)\b|"
    r"\b(?:mujeres|women|femenin[ao]?)\b.{0,60}\b(?:solo|exclusiv[oa]mente|only)\b",
    re.IGNORECASE,
)
PRACTICE_RE = re.compile(
    r"\b(?:practicantes?|pr[aá]ctica(?:s)?(?:\s+(?:profesional(?:es)?|acad[eé]mica(?:s)?|universitaria(?:s)?|formativa(?:s)?))?|"
    r"estudiante\s+en\s+(?:etapa\s+)?pr[aá]ctica|etapa\s+productiva|pasant[ií]a(?:s)?|"
    r"intern(?:ship)?s?|trainee|co[\s-]?op|industrial\s+placement|aprendiz|aprendices|estudiantes?\s+(?:de|en|universitari[oa]s?)\b)\b",
    re.IGNORECASE,
)
# Carreras o áreas que no corresponden a un ingeniero físico cuando el título
# las nombra sin mencionar ninguna carrera afín.
CARRERA_NO_AFIN_RE = re.compile(
    r"\b(?:administrativ|administraci[oó]n\s+de\s+empresas|adm\s+empresas|psicolog|contab|contadur|mercade|marketing|trade\b|dise[ñn]o\s+gr[aá]fico|"
    r"comunicaci[oó]n|periodis|deport|archivo|documental|compensaci[oó]n|vigilan|escolta|jur[ií]dic|derecho|recepci[oó]n|reservas|gesti[oó]n\s+documental|"
    r"contrataci[oó]n|servicio\s+al\s+cliente|cumplimiento|comercial|ventas|selecci[oó]n|n[oó]mina|"
    r"cocina|barismo|hotel|finanz|negocios\s+internacionales|auditor|tributari|riesgos|cr[eé]dito|seguros|bienestar|sst\b|"
    r"seguridad\s+y\s+salud|salud\s+ocupacional|talento|gesti[oó]n\s+humana|"
    r"corporativ|eventos|m[eé]dic[oa]s?\s+(?:general|especialista)|visitador|"
    r"sales|business\s+development|finance|accounting|legal\b|human\s+resources|\bhr\b|recruit|talent|"
    r"communications|customer|fraud|disputes|risk\b|conservation|events?\b|social\s+media|content\b|"
    r"partnerships|operations\s+intern|real\s+estate)",
    re.IGNORECASE,
)
CARRERA_AFIN_RE = re.compile(
    r"\b(?:f[ií]sic|electr[oó]nic|el[eé]ctric|electricidad|mecatr[oó]nic|mec[aá]nic|electromec[aá]nic|automatizaci|"
    r"instrumentaci|control\s+(?:autom|de\s+procesos|industrial|el[eé]ctric|electr[oó]nic)|ingenier[ií]a\s+de\s+control|materiales|metal[uú]rg|metrolog|datos|data\b|anal[ií]tic|estad[ií]stic|matem[aá]tic|"
    r"biom[eé]dic|bioingenier|telecomunicaci|energ[ií]a|renovable|solar|ciencias|stem\b|"
    r"todas\s+las\s+ingenier[ií]as|cualquier\s+ingenier[ií]a|python|programaci|software|desarroll|sistemas|"
    r"inteligencia\s+artificial|machine\s+learning|\bia\b|\bai\b|iot\b|embebid|rob[oó]tic|[oó]ptic|"
    r"l[aá]ser|qu[ií]mic|nanotecnolog|simulaci|investigaci|i\+d|innovaci|laboratorio|mantenimiento|"
    r"engineer|physics|scien|developer|software\s+development|infraestructura|infrastructure|hardware|research|electrical|mechanical|"
    r"r&d|tecnolog[ií]a|technolog|automation|robotics|optics|photonics|semiconductor|quantum|cu[aá]ntic)",
    re.IGNORECASE,
)
# Áreas técnicas genéricas: no rescatan un título de otra carrera, pero sí
# permiten conservar un aviso técnico sin rama específica.
AREA_TECNICA_RE = re.compile(r"\b(?:ingenier|calidad|procesos|producci|proyectos|planta|t[eé]cnic)", re.IGNORECASE)

# Otras carreras técnicas: el aviso entra si, además, nombra una carrera afín
# ("Practicante de ingeniería industrial, mecatrónica o electrónica").
CARRERA_OTRA_RE = re.compile(
    r"\b(?:ambiental|alimentos|agr[ií]col|agron[oó]m|agroindustri|civil(?:es)?\b|obras\s+civiles|arquitect|"
    r"industrial\b|log[ií]stic|costos|abastecimiento|compras|zootecn|veterinari|nutrici|odontolog|"
    r"fisioterap|farmac|econom)",
    re.IGNORECASE,
)
CARRERA_AFIN_EXPLICITA_RE = re.compile(
    r"\b(?:ingenier[ií]a\s+(?:f[ií]sica|electr[oó]nica|el[eé]ctrica|mecatr[oó]nica|mec[aá]nica|electromec[aá]nica|"
    r"de\s+control|de\s+materiales|biom[eé]dica|de\s+telecomunicaciones|de\s+sistemas|qu[ií]mica)|"
    r"f[ií]sica|f[ií]sicos?|electr[oó]nica|mecatr[oó]nica|electromec[aá]nica|el[eé]ctrica|automatizaci[oó]n|"
    r"instrumentaci[oó]n|todas\s+las\s+ingenier[ií]as|cualquier\s+ingenier[ií]a|physics|electrical|"
    r"mechanical|mechatronics|electronics)\b",
    re.IGNORECASE,
)

# "Física" que no es la ciencia: seguridad física (vigilancia), educación física...
FISICA_FALSA_RE = re.compile(
    r"\b(?:seguridad|educaci[oó]n|actividad|terapia|preparaci[oó]n|condici[oó]n|cultura|persona)\s+f[ií]sica\b|"
    r"\bf[ií]sico\s+(?:deportiv|culturista)|\bentrenamiento\s+f[ií]sico\b",
    re.IGNORECASE,
)

def title_is_out_of_profile(title, descripcion=None):
    """True si el aviso es ajeno al perfil.

    Roles no técnicos (administrativo, ventas, psicología...) se descartan por
    el título. Si el título nombra otra carrera técnica (industrial,
    ambiental...), el aviso entra cuando él mismo o su descripción mencionan una
    carrera afín; con `descripcion=None` (aún sin leer) se deja pasar.
    """
    if any(re.search(p, title, re.IGNORECASE) for p in EXCLUDED_ROLES):
        return True
    if FISICA_FALSA_RE.search(title):
        return True
    if CARRERA_AFIN_RE.search(title):
        return False
    if CARRERA_NO_AFIN_RE.search(title):
        return True
    if CARRERA_OTRA_RE.search(title):
        return descripcion is not None and not CARRERA_AFIN_EXPLICITA_RE.search(descripcion)
    return False

GENERIC_TITLE_FILLER_RE = re.compile(
    r"\b(?:universitari[oa]s?|profesional(?:es)?|programa|convocatoria|semillero|talento\s+joven|"
    r"de|del|en|para|y|o|la|el|los|las|a|e|intern(?:ship)?s?|student|summer|fall|spring|fy\d+|"
    r"20\d\d(?:-[12i]+)?|i{1,2})\b|[\d\W_]+",
    re.IGNORECASE,
)

def title_is_generic_program(title):
    """True si el título solo dice 'practicante(s)/programa/año/ciudad' sin un área concreta."""
    rest = PRACTICE_RE.sub(" ", title)
    rest = LOCAL_LOCATION_RE.sub(" ", rest)
    rest = re.sub(r"\bcolombia\b", " ", rest, flags=re.IGNORECASE)
    rest = GENERIC_TITLE_FILLER_RE.sub(" ", rest)
    return not rest.strip()

TERMINOS_FISICA_RE = re.compile(r'\b(f[ií]sic[ao]s?|metrolog[ií]a|cu[aá]ntic[ao]s?|espectroscop[ií]a|difracci[oó]n|radiaci[oó]n|dosimetr[ií]a|nanotecnolog[ií]a)\b', re.IGNORECASE)

def matches_keyword(keyword, text):
    """Verifica si una palabra clave coincide respetando límites de palabra para términos cortos."""
    kw_clean = keyword.strip().lower()
    if len(kw_clean) <= 4 or kw_clean in ["stem", "datos", "data", "cad", "ia", "ai", "pcb", "daq", "plc", "gum", "iot", "spi", "i2c", "sql", "sem", "drx"]:
        return bool(re.search(r'(?:\b|_)' + re.escape(kw_clean) + r'(?:\b|_)', text, re.IGNORECASE))
    return kw_clean in text.lower()

def normalize_match_text(value):
    normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))

def career_is_requested_as_related(career, text):
    """Solo habilita una carrera espejo cuando el aviso la vincula con afines/relacionadas."""
    normalized_career = normalize_match_text(career).strip()
    normalized_text = normalize_match_text(text)
    if not normalized_career or normalized_career in {"fisica", "ingenieria fisica", "todas las ingenierias"}:
        return False
    career_pattern = re.compile(
        r"(?<![a-z0-9])" + re.escape(normalized_career) + r"(?![a-z0-9])"
    )
    related_pattern = re.compile(
        r"\b(?:afines?|relacionad[oa]s?|similares?|related\s+(?:field|fields|discipline|disciplines|major|majors)|or\s+equivalent)\b"
    )
    for match in career_pattern.finditer(normalized_text):
        start = max(0, match.start() - 90)
        end = min(len(normalized_text), match.end() + 110)
        if related_pattern.search(normalized_text[start:end]):
            return True
    return False

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def canonical_job_url(url):
    """Normaliza enlaces para evitar perder o duplicar una vacante por tracking."""
    parsed = urlparse(str(url or "").strip())
    host = parsed.netloc.lower().removeprefix("www.")
    path = unquote(parsed.path).rstrip("/")
    # co.linkedin.com y www.linkedin.com apuntan al mismo aviso: se usa su id.
    linkedin_id = re.search(r"(\d{8,})$", path) if host.endswith("linkedin.com") else None
    if linkedin_id:
        return f"linkedin.com/jobs/view/{linkedin_id.group(1)}"
    return f"{host}{path}".lower()

# Días que se conserva una vacante que dejó de aparecer en las búsquedas
# (sigue sujeta a la verificación del enlace en cada corrida).
DIAS_RETENCION_SIN_REAPARECER = 21

def merge_job_snapshots(current_jobs, previous_jobs):
    """Conserva vacantes previas si el portal no las devolvió en esta corrida."""
    today = datetime.now().date()
    merged = {}
    detail_fields = (
        "perfil", "compensacion", "resumen_fuente", "descripcion_fuente",
        "fecha_publicacion", "fecha_cierre_iso", "tipo_empleo", "modalidad",
        "alcance_geografico", "estado_vigencia",
    )
    for source in current_jobs:
        key = canonical_job_url(source.get("url"))
        if not key:
            continue
        if key not in merged:
            item = dict(source)
            merged[key] = item
        else:
            item = merged[key]
            for field, value in source.items():
                if value not in (None, "", [], {}):
                    item[field] = value
        item["encontrada_ultima_corrida"] = True
        item["ultima_deteccion"] = today.isoformat()

    for source in previous_jobs if isinstance(previous_jobs, list) else []:
        key = canonical_job_url(source.get("url"))
        if not key:
            continue
        if key not in merged:
            try:
                last_seen = datetime.fromisoformat(source.get("ultima_deteccion", "")).date()
            except ValueError:
                last_seen = today
            if (today - last_seen).days > DIAS_RETENCION_SIN_REAPARECER:
                continue
            item = dict(source)
            item["encontrada_ultima_corrida"] = False
            item["ultima_deteccion"] = last_seen.isoformat()
            item["estado_vigencia"] = "No reapareció en esta búsqueda; revisar vigencia en la fuente"
            merged[key] = item
        else:
            item = merged[key]
            item.setdefault("primera_deteccion", source.get("primera_deteccion"))
            for field in detail_fields:
                if item.get(field) in (None, "", [], {}) and source.get(field) not in (None, "", [], {}):
                    item[field] = source[field]
    for item in merged.values():
        if not item.get("primera_deteccion"):
            item["primera_deteccion"] = today.isoformat()
    return list(merged.values())

EMPRESAS_OBJETIVO_PATH = os.path.join(BASE_DIR, "empresas_objetivo.json")
EMPRESAS_ANTIOQUIA_PATH = os.path.join(BASE_DIR, "empresas_antioquia.json")
_target_company_re = None

def load_target_companies():
    """Empresas objetivo (empresas_objetivo.json) más el directorio de Antioquia."""
    names = [item.get("empresa") for item in load_json(EMPRESAS_OBJETIVO_PATH) or [] if isinstance(item, dict)]
    for item in load_json(EMPRESAS_ANTIOQUIA_PATH) or []:
        if isinstance(item, dict) and item.get("empresa"):
            names.append(re.sub(r"\s*\(.*?\)", "", item["empresa"]).strip())
    return list(dict.fromkeys(name.strip() for name in names if name and name.strip()))

def company_is_target(company):
    global _target_company_re
    if _target_company_re is None:
        alternatives = sorted({normalize_match_text(n) for n in load_target_companies()}, key=len, reverse=True)
        pattern = "|".join(re.escape(n) for n in alternatives if n)
        _target_company_re = re.compile(rf"(?<![a-z0-9])(?:{pattern})(?![a-z0-9])") if pattern else re.compile(r"(?!x)x")
    return bool(_target_company_re.search(normalize_match_text(company)))

# Presupuesto global de tiempo (4 h 45 min, dentro del límite de 5 h de GitHub Actions)
# para recorrer absolutamente todas las búsquedas y empresas sin recortar nada.
BOT_START_TIME = time.time()
MAX_RUNTIME_SECONDS = 285 * 60

def time_budget_exceeded(margin_seconds=0):
    return (time.time() - BOT_START_TIME) >= (MAX_RUNTIME_SECONDS - margin_seconds)

# LinkedIn responde 429 si recibe más de ~10 consultas seguidas. Antes el bot
# tomaba ese 429 como "cero resultados" y perdía casi todas sus búsquedas.
LINKEDIN_MIN_INTERVAL = 2.2
LINKEDIN_STATS = Counter()
_linkedin_lock = threading.Lock()
_linkedin_next_allowed = [0.0]
LINKEDIN_CLOSED_RE = re.compile(
    r"no longer accepting applications|ya no se aceptan solicitudes|ya no acepta solicitudes",
    re.IGNORECASE,
)

def linkedin_get(url, retries=3):
    """GET a LinkedIn respetando el intervalo mínimo sin apilar esperas entre hilos."""
    for attempt in range(retries):
        if time_budget_exceeded():
            LINKEDIN_STATS["omitida por presupuesto de tiempo"] += 1
            return None
        with _linkedin_lock:
            now = time.time()
            slot = max(now, _linkedin_next_allowed[0])
            _linkedin_next_allowed[0] = slot + LINKEDIN_MIN_INTERVAL
            wait = slot - now
        if wait > 0:
            time.sleep(wait)
        try:
            response = requests.get(url, headers=HEADERS, timeout=12)
        except requests.RequestException:
            LINKEDIN_STATS["error de red"] += 1
            continue
        if response.status_code == 429:
            LINKEDIN_STATS["429 (reintento)"] += 1
            backoff = 15 * (attempt + 1)
            with _linkedin_lock:
                _linkedin_next_allowed[0] = max(_linkedin_next_allowed[0], time.time() + backoff)
            continue
        LINKEDIN_STATS[f"HTTP {response.status_code}"] += 1
        return response
    LINKEDIN_STATS["perdida tras reintentos"] += 1
    return None

def html_to_text(raw_html):
    text = re.sub(r"<(?:script|style)[^>]*>.*?</(?:script|style)>", " ", raw_html or "", flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>|</p>|</li>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()

def _company_matches_query(card_company, card_title, required_company):
    """Verifica que una búsqueda por empresa en LinkedIn corresponda realmente a esa empresa."""
    if not required_company:
        return True
    req_norm = normalize_match_text(required_company).strip()
    if not req_norm:
        return True
    haystack = f"{normalize_match_text(card_company)} {normalize_match_text(card_title)}"
    if req_norm in haystack:
        return True
    tokens = [t for t in re.split(r"\s+", req_norm) if len(t) >= 4 and t not in {"colombia", "grupo", "empresas", "compania", "corporacion", "antioquia", "medellin"}]
    return bool(tokens) and all(t in haystack for t in tokens[:2])

def scrape_linkedin_query(query, location="Medellin, Antioquia, Colombia", pages=1, required_company=None):
    """Consulta la API pública guest de LinkedIn Jobs (10 avisos por página)."""
    results = []
    for start in range(0, pages * 10, 10):
        if time_budget_exceeded(margin_seconds=300):
            break
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={quote(query)}&location={quote(location)}&start={start}"
        )
        r = linkedin_get(url, retries=2)
        if r is None or r.status_code != 200:
            break
        cards = re.findall(r'<div class="base-card[^"]*"[^>]*>(.*?)</li>', r.text, re.DOTALL)
        if not cards:
            break
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
            loc = unescape(loc_m.group(1).strip()) if loc_m else "Ubicación por confirmar"
            link = link_m.group(1).split("?")[0] if link_m else ""
            iso_date = date_m.group(1).strip() if date_m else ""
            pub_date = date_m.group(2).strip() if date_m else "Reciente"
            if not title or not link:
                continue
            if required_company and not _company_matches_query(company, title, required_company):
                continue
            # Se descartan desde el título los roles ajenos para no gastar
            # consultas de detalle en ellos.
            if title_is_out_of_profile(title):
                continue

            if location == "Worldwide":
                if not re.search(r"\b(intern(?:ship)?|trainee|practicante|pasant[ií]a|pr[aá]ctica|student|co-?op)\b", title, re.IGNORECASE):
                    continue
                if iso_date:
                    try:
                        if (datetime.now().date() - datetime.fromisoformat(iso_date).date()).days > 45:
                            continue
                    except ValueError:
                        pass

            job = {
                "titulo": title,
                "empresa": company,
                "ubicacion": loc,
                "url": link,
                "fecha_publicacion": iso_date or pub_date,
                "fuente": "LinkedIn Jobs",
            }
            id_m = re.search(r"(\d{8,})$", link)
            if id_m:
                job["linkedin_id"] = id_m.group(1)
            if location == "Worldwide":
                job["search_scope"] = "WORLDWIDE"
            elif location == "Colombia":
                job["search_scope"] = "COLOMBIA"
            results.append(job)
        # Si LinkedIn devolvió menos de 10 tarjetas, no existen más páginas para esta consulta.
        if len(cards) < 10:
            break
    return results

def enrich_linkedin_job(job):
    """Lee el detalle público del aviso: confirma que sigue abierto y trae la descripción.

    Si el aviso acaba de aparecer en las búsquedas de esta corrida y ya cuenta con
    descripción de una corrida previa, se conserva sin gastar otra petición a LinkedIn.
    Si LinkedIn limita la tasa (HTTP 429) o hay falla temporal de red, nunca se descarta
    una vacante activa: se conserva con los datos disponibles para no perder ninguna oferta.
    """
    job_id = job.get("linkedin_id") or (re.search(r"(\d{8,})", job.get("url", "")) or [None, None])[1]
    if not job_id:
        return False
    if job.get("encontrada_ultima_corrida") and job.get("descripcion_fuente"):
        job["estado_vigencia"] = "Aviso abierto en LinkedIn al momento del rastreo"
        LINKEDIN_STATS["detalle en caché (activo)"] += 1
        return True
    if time_budget_exceeded():
        if job.get("encontrada_ultima_corrida") or job.get("descripcion_fuente") or job.get("curada"):
            job.setdefault("estado_vigencia", "Aviso detectado en LinkedIn (verificación diferida por tiempo)")
            return True
        return False
    r = linkedin_get(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}", retries=2)
    if r is not None and r.status_code in (404, 410):
        return False
    if r is None or r.status_code != 200:
        # Ante bloqueo 429 o error transitorio de red, no perder la vacante.
        if job.get("encontrada_ultima_corrida") or job.get("descripcion_fuente") or job.get("curada"):
            job.setdefault("estado_vigencia", "Aviso detectado en LinkedIn (detalle pendiente por límite de tasa)")
            LINKEDIN_STATS["conservada ante 429/red"] += 1
            return True
        return False
    page = r.text
    if LINKEDIN_CLOSED_RE.search(page):
        return False
    desc_m = re.search(r'show-more-less-html__markup[^>]*>(.*?)</div>', page, re.DOTALL)
    if desc_m:
        job["descripcion_fuente"] = html_to_text(desc_m.group(1))[:2500]
    criteria = re.findall(
        r'description__job-criteria-subheader[^>]*>\s*([^<]+?)\s*</h3>\s*<span[^>]*>\s*([^<]+?)\s*</span>',
        page,
    )
    for label, value in criteria:
        if re.search(r"tipo de empleo|employment type", label, re.IGNORECASE):
            job["tipo_empleo"] = value.strip()
    job["estado_vigencia"] = "Aviso abierto en LinkedIn al momento del rastreo"
    return True

def scrape_computrabajo_query(query, pages=2):
    """Consulta prácticas en Computrabajo Antioquia (20 avisos por página)."""
    results = []
    for page in range(1, pages + 1):
        url = f"https://co.computrabajo.com/empleos-en-antioquia?q={quote(query)}&p={page}"
        page_results = _scrape_computrabajo_page(url)
        results.extend(page_results)
        if len(page_results) < 20:
            break
        time.sleep(0.3)
    return results

def _scrape_computrabajo_page(url):
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

def scrape_magneto_query(query, pages=4):
    """Consulta Magneto365 en todo Colombia; el filtro de ubicación/modalidad se aplica después."""
    results = []
    for page in range(1, pages + 1):
        page_results = _scrape_magneto_page(query, page)
        results.extend(page_results)
        if len(page_results) < 20:
            break
        time.sleep(0.3)
    return results

def _scrape_magneto_page(query, page):
    api_url = "https://api.magneto365.com/jobs/v1/public/jobs/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.magneto365.com",
        "Referer": "https://www.magneto365.com/",
        "Accept": "application/json, text/plain, */*"
    }
    params = {
        "device": "desktop",
        "paginator[page]": page,
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

            # En Magneto isRemote=True cubre ofertas remotas e híbridas.
            is_remote = bool(row.get("isRemote"))
            departments = row.get("departments") or []
            is_antioquia = "antioquia" in " ".join(departments).lower() or any(
                any(ac in c for ac in antioquia_cities) for c in city_lower_list
            )

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
                "ubicacion": (
                    f"{city_str or 'Colombia'}, Antioquia" if is_antioquia and "antioquia" not in city_str.lower()
                    else city_str or "Colombia"
                ) + (" · remoto o híbrido" if is_remote else ""),
                "modalidad": "Remoto o híbrido" if is_remote else "",
                "url": url,
                "fecha_publicacion": pub_date,
                "fuente": "Magneto365",
                "compensacion": comp,
                "perfil": perfil,
                "mision": desc[:250] if desc else "",
                "descripcion_fuente": desc[:2500] if desc else "",
            }
            if row.get("expirationDate"):
                job["fecha_cierre_iso"] = str(row["expirationDate"]).split("T")[0]
            results.append(job)
        return results
    except Exception:
        return []

def scrape_elempleo_query(query):
    """Consulta ofertas de prácticas de ingeniería en ElEmpleo.com para Antioquia y nacional."""
    # La ruta /antioquia no filtra (devuelve casi todo Bogotá); /medellin sí.
    url = f"https://www.elempleo.com/co/ofertas-empleo/medellin?trabajo={quote(query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return []
        # data-url y data-ga4-offerdata vienen en el mismo elemento; emparejarlos
        # por separado (zip de dos listas) mezclaba títulos y enlaces.
        pairs = re.findall(r'data-url="([^"]+)"\s+data-ga4-offerdata="([^"]+)"', r.text)
        results = []
        seen = set()
        for raw_url, raw_json in pairs:
            try:
                data = json.loads(unescape(raw_json))
                clean_url = "https://www.elempleo.com" + raw_url.split("?")[0]
                if clean_url in seen:
                    continue
                seen.add(clean_url)
                title = data.get("title", "").strip()
                company = data.get("company", "").strip() or "Empresa Confidencial"
                loc = unescape(data.get("location", "").strip()) or "Ubicación por confirmar"
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
                "ubicacion": "Ubicación por confirmar",
                "url": url_job,
                "fecha_publicacion": "Reciente",
                "fuente": "FirstJob",
                "compensacion": "",
                "search_scope": "COLOMBIA",
                "alcance_geografico": "Oferta nacional; ciudad por confirmar"
            })
        return results
    except Exception:
        return []

PORTALES_WORKDAY_PATH = os.path.join(BASE_DIR, "portales_workday.json")
WORKDAY_BUSQUEDAS = ["intern", "internship", "practicante", "pasantia", "trainee", "aprendiz", "estudiante"]

def scrape_workday_portal(portal):
    """Prácticas publicadas directamente en el portal Workday de una empresa.

    Para agregar empresas, edita portales_workday.json: la dirección de su
    portal tiene la forma https://<tenant>.<servidor>.myworkdayjobs.com/<sitio>.
    """
    base = f"https://{portal['tenant']}.{portal['servidor']}.myworkdayjobs.com"
    api = f"{base}/wday/cxs/{portal['tenant']}/{portal['sitio']}"
    headers = {**HEADERS, "Accept": "application/json", "Content-Type": "application/json"}
    rutas = {}
    for termino in WORKDAY_BUSQUEDAS:
        try:
            r = requests.post(f"{api}/jobs", json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": termino},
                              headers=headers, timeout=12)
            postings = r.json().get("jobPostings", []) if r.status_code == 200 else []
        except (requests.RequestException, ValueError):
            postings = []
        for posting in postings:
            if PRACTICE_RE.search(posting.get("title", "")):
                rutas[posting["externalPath"]] = posting
        time.sleep(0.3)
    results = []
    for ruta, posting in rutas.items():
        try:
            info = requests.get(f"{api}{ruta}", headers=headers, timeout=12).json().get("jobPostingInfo", {})
        except (requests.RequestException, ValueError):
            continue
        ubicacion = info.get("location") or posting.get("locationsText") or ""
        modalidad = {"Remote": "Remoto", "Hybrid": "Híbrido", "On-site": "Presencial"}.get(info.get("remoteType", ""), "")
        results.append({
            "titulo": posting.get("title", "").strip(),
            "empresa": portal["empresa"],
            "ubicacion": f"{ubicacion} · {modalidad.lower()}" if modalidad in ("Remoto", "Híbrido") else ubicacion,
            "modalidad": modalidad,
            "url": info.get("externalUrl") or f"{base}/{portal['sitio']}{ruta}",
            "fecha_publicacion": info.get("startDate") or "Reciente",
            "fecha_cierre_iso": info.get("endDate", ""),
            "fuente": f"Portal corporativo {portal['empresa']} (Workday)",
            "descripcion_fuente": html_to_text(info.get("jobDescription", ""))[:2500],
            "search_scope": "LOCAL" if LOCAL_LOCATION_RE.search(ubicacion) or "colombia" in ubicacion.lower() else "WORLDWIDE",
        })
        time.sleep(0.3)
    return results

def scrape_web_query(query, search_scope="LOCAL"):
    """Busca resultados web públicos; para internacional exige práctica e indicio remoto."""
    suffix = {
        "LOCAL": " Medellín Antioquia empleo práctica",
        "COLOMBIA": " Colombia práctica remota híbrida",
        "WORLDWIDE": " remote internship",
    }.get(search_scope, " Colombia práctica remota híbrida")
    try:
        results = []
        for link, title, snippet in buscar_web(query + suffix):
            evidence = f"{title} {snippet}"
            if not PRACTICE_RE.search(evidence):
                continue
            if search_scope == "WORLDWIDE" and not REMOTE_MODALITY_RE.search(evidence):
                continue
            if title and link.startswith("http"):
                company_match = re.search(r'"([^"]+)"', query)
                job = {
                    "titulo": title,
                    "empresa": company_match.group(1) if company_match else "Por identificar",
                    "ubicacion": (
                        "Remoto internacional (elegibilidad por confirmar)" if search_scope == "WORLDWIDE"
                        else "Colombia (ciudad por confirmar)" if search_scope == "COLOMBIA"
                        else "Medellín / Antioquia (resultado web; confirmar ubicación)"
                    ),
                    "url": link,
                    "fecha_publicacion": "Resultado web; verificar vigencia",
                    "fuente": f"Búsqueda web · {urlparse(link).netloc}",
                    "resumen_fuente": snippet
                }
                if search_scope in {"WORLDWIDE", "COLOMBIA"}:
                    job["search_scope"] = search_scope
                    job["alcance_geografico"] = (
                        "Remoto internacional; confirmar elegibilidad desde Colombia"
                        if search_scope == "WORLDWIDE"
                        else "Oferta nacional; confirmar ciudad y modalidad"
                    )
                results.append(job)
        return results
    except Exception:
        return []

def classify_and_score_job(job, config_ramas):
    """Calcula el Score de Afinidad con el Pénsum UNAL con priorización y filtrado de roles no técnicos."""
    title_lower = job.get("titulo", "").lower()
    company_lower = job.get("empresa", "").lower()
    perfil_lower = job.get("perfil", "").lower()
    # La misión/tareas generadas desde plantillas en corridas anteriores no
    # deben volver a puntuar como si vinieran del aviso.
    mision_lower = "" if job.get("_mision_generada") else str(job.get("mision", "")).lower()
    tareas = "" if job.get("_tareas_generadas") else str(job.get("tareas", "")).lower()
    resumen = str(job.get("resumen_fuente", "")).lower()
    descripcion = str(job.get("descripcion_fuente", "")).lower()
    tipo_empleo = str(job.get("tipo_empleo", "")).lower()
    text_to_analyze = f"{title_lower} {company_lower} {perfil_lower} {mision_lower} {tareas} {resumen} {descripcion} {tipo_empleo}"
    career_text = f"{title_lower} {perfil_lower} {mision_lower} {tareas} {resumen} {descripcion}"
    es_curada = bool(job.get("curada"))

    # Descartar roles no técnicos u orientados a otras carreras
    if not es_curada and title_is_out_of_profile(job.get("titulo", ""), f"{perfil_lower} {mision_lower} {resumen} {descripcion}"):
        return None

    # Detección de programas especiales (con límites de palabra para evitar falsos positivos como 'systems' -> 'stem')
    programa_genero = bool(TERMINOS_MUJERES_RE.search(text_to_analyze))
    convocatoria_exclusiva_mujeres = bool(CONVOCATORIA_MUJERES_RE.search(text_to_analyze))
    es_exclusiva_fisica = bool(TERMINOS_FISICA_RE.search(FISICA_FALSA_RE.sub(" ", text_to_analyze)))

    # La antigüedad de publicación no revela la fecha límite de postulación.
    # Solo indicar cierre inminente cuando el rastreador obtenga una fecha explícita.
    es_cierre_inminente = False
    fecha_cierre = job.get("fecha_cierre_iso", "")
    if fecha_cierre:
        try:
            dias_para_cierre = (datetime.fromisoformat(fecha_cierre).date() - datetime.now().date()).days
            es_cierre_inminente = 0 <= dias_para_cierre <= 5
        except ValueError:
            pass

    # La descripción completa menciona "prácticas" en otros sentidos (buenas
    # prácticas, prácticas de desarrollo); solo cuentan título, tipo de empleo
    # y los campos cortos que entrega la fuente.
    es_practica = bool(PRACTICE_RE.search(f"{title_lower} {tipo_empleo}")) or bool(
        PRACTICE_RE.search(f"{perfil_lower} {mision_lower} {resumen}")
        and not re.search(r"buenas\s+pr[aá]cticas", f"{mision_lower} {resumen}")
    )
    # El portal es de prácticas: los empleos regulares no se publican.
    if not es_curada and not es_practica:
        return None

    total_score = 0
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
        carreras = data.get("carreras_mencionadas", [])
        carreras_afines_candidatas = [
            carrera for carrera in carreras
            if career_is_requested_as_related(carrera, career_text)
        ]
        carreras_afines_unicas = {
            normalize_match_text(carrera): carrera for carrera in carreras_afines_candidatas
        }
        carreras_afines = [
            carrera for normalized, carrera in carreras_afines_unicas.items()
            if not any(
                normalized != otra and normalized in otra
                for otra in carreras_afines_unicas
            )
        ]
        palabras_carrera_afines = {
            normalize_match_text(palabra)
            for palabra in data.get("palabras_clave_carreras_afines", [])
        }
        for p in palabras:
            palabra_normalizada = normalize_match_text(p)
            # Las menciones de una carrera se puntúan solo mediante la regla explícita de "afines".
            if palabra_normalizada in palabras_carrera_afines and not carreras_afines:
                continue
            if matches_keyword(p, text_to_analyze):
                kw_hits += 1
        kw_hits += len(carreras_afines)

        # Una coincidencia técnica o una carrera espejo con "afines" activa la rama.
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

    # Sin ninguna rama técnica ni mención de física, solo se conserva si el
    # título pide perfiles de ingeniería o de áreas técnicas afines.
    titulo = job.get("titulo", "")
    titulo_tecnico = bool(CARRERA_AFIN_RE.search(titulo) or AREA_TECNICA_RE.search(titulo))
    if not titulo_tecnico and not es_exclusiva_fisica and not es_curada:
        # Un título sin área ("Practicantes 2027 Medellín") vale si la
        # descripción encaja en una rama; uno con área ajena ("Practicante de
        # Eventos") no.
        if not ramas_coincidentes or not title_is_generic_program(titulo):
            return None

    es_empresa_objetivo = company_is_target(job.get("empresa", ""))
    if es_empresa_objetivo:
        total_score += 15

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
        afinidad = "Afinidad con Física"
    elif max_rama_score >= 50:
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
    job["programa_inclusion_genero"] = programa_genero
    job["convocatoria_exclusiva_mujeres"] = convocatoria_exclusiva_mujeres
    job["es_cierre_inminente"] = es_cierre_inminente
    job["es_practica"] = es_practica
    job["score_pensum"] = total_score
    job["empresa_objetivo"] = es_empresa_objetivo
    mision_fuente = "" if job.get("_mision_generada") else job.get("mision")
    descripcion_corta = str(job.get("descripcion_fuente", ""))[:400]
    if mision_fuente or job.get("resumen_fuente") or descripcion_corta:
        job["mision"] = mision_fuente or job.get("resumen_fuente") or descripcion_corta
        job.pop("_mision_generada", None)
    else:
        job["mision"] = mision_especifica or f"Desarrollo de proyectos técnicos y operativos en {job.get('empresa', 'la empresa')}."
        job["_mision_generada"] = True
    if not job.get("tareas") or job.get("_tareas_generadas"):
        job["tareas"] = tareas_especificas if tareas_especificas else "Apoyo en mediciones, modelado técnico, análisis de datos y reporte de resultados."
        job["_tareas_generadas"] = True
    if job.get("resumen_fuente") and not job.get("tareas"):
        job["tareas"] = "Resumen de búsqueda web. Abre la publicación original para confirmar funciones, requisitos y vigencia."

    return job

DESCRIPTION_ANCHOR_RE = re.compile(
    r"Descripci[oó]n de la oferta|Descripci[oó]n del cargo|Descripci[oó]n general|Job description|"
    r"Acerca del empleo|Funciones del cargo|Responsabilidades",
    re.IGNORECASE,
)

def extract_page_description(page_html):
    """Texto del aviso: JSON-LD JobPosting o el bloque tras 'Descripción de la oferta'."""
    for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page_html, re.DOTALL):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("@type") == "JobPosting" and item.get("description"):
                return html_to_text(str(item["description"]))[:2500]
    anchor = DESCRIPTION_ANCHOR_RE.search(page_html)
    if anchor:
        return html_to_text(page_html[anchor.start():anchor.start() + 6000])[:2500]
    return ""

def verify_job_url(job):
    """Confirma que el aviso sigue abierto (HTTP 200, sin login ni 'oferta finalizada') y lee su descripción."""
    url = job.get("url", "")
    if not url or not url.startswith("http"):
        return False
    url_lower = url.lower()
    if "linkedin.com" in url_lower:
        return enrich_linkedin_job(job)
    # Si la oferta proviene de la API en vivo de Magneto365 o Workday en esta misma corrida
    # y ya tiene su descripción completa, no requiere descargar el HTML otra vez.
    if (
        job.get("encontrada_ultima_corrida")
        and job.get("descripcion_fuente")
        and ("magneto365.com" in url_lower or "myworkdayjobs.com" in url_lower)
    ):
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if r.status_code in (404, 410):
            return False
        if r.status_code >= 400:
            return bool(job.get("encontrada_ultima_corrida") or job.get("curada") or job.get("descripcion_fuente"))
        txt = r.text.lower()
        if (
            "esta oferta ya no está disponible" in txt
            or "la oferta que buscas ya no está disponible" in txt
            or "página no encontrada" in txt
            or "la vacante ha finalizado" in txt
        ):
            return False
        if not job.get("curada") and not job.get("descripcion_fuente"):
            descripcion = extract_page_description(r.text)
            if descripcion:
                job["descripcion_fuente"] = descripcion
        return True
    except Exception:
        return bool(job.get("encontrada_ultima_corrida") or job.get("curada") or job.get("descripcion_fuente"))

def is_in_target_location(job):
    """Antioquia con cualquier modalidad; fuera de Antioquia solo remoto o híbrido explícito."""
    location = str(job.get("ubicacion", ""))
    if job.get("search_scope") != "WORLDWIDE" and LOCAL_LOCATION_RE.search(location):
        return True

    # FirstJob no proporciona modalidad en la tarjeta rastreada; no confiar en el
    # antiguo valor genérico "Colombia / Remoto" que se asignaba a todos sus avisos.
    if job.get("fuente") == "FirstJob" and location.strip().lower() == "colombia / remoto":
        return False

    details = " ".join(str(job.get(key, "")) for key in (
        "titulo", "ubicacion", "modalidad", "perfil", "resumen_fuente", "descripcion_fuente"
    ))
    if not job.get("_mision_generada"):
        details += " " + str(job.get("mision", ""))
    if job.get("search_scope") == "WORLDWIDE":
        # En el exterior lo híbrido no sirve: se exige remoto en el título o la
        # ubicación, o una frase inequívoca en la descripción.
        head = f"{job.get('titulo', '')} {location} {job.get('modalidad', '')}"
        if not (REMOTE_ONLY_RE.search(head) or REMOTE_WORLDWIDE_DESC_RE.search(details)):
            return False
        if REMOTE_NEGATION_RE.search(details):
            return False
    elif not REMOTE_MODALITY_RE.search(details):
        return False
    if job.get("search_scope") == "WORLDWIDE":
        job["alcance_geografico"] = "Remoto internacional; confirmar elegibilidad desde Colombia"
        if "remoto internacional" not in location:
            job["ubicacion"] = f"{location} · remoto internacional (elegibilidad por confirmar)"
    else:
        job["alcance_geografico"] = "Fuera de Antioquia; remoto o híbrido según el aviso"
        if not re.search(r"remoto|h[ií]brid", location, re.IGNORECASE):
            job["ubicacion"] = f"{location} · remoto o híbrido (confirmar en el aviso)"
    return True

def needs_detail_before_location(job):
    """Avisos de LinkedIn fuera de Antioquia: la modalidad solo aparece en la descripción."""
    return "linkedin.com" in job.get("url", "").lower() and not LOCAL_LOCATION_RE.search(str(job.get("ubicacion", "")))

def filter_verified_jobs(jobs, max_workers=25):
    """Verifica enlaces en paralelo separando LinkedIn de los demás portales para no bloquear hilos."""
    in_profile = [job for job in jobs if job.get("curada") or not title_is_out_of_profile(job.get("titulo", ""))]
    print(f"[*] Perfil: {len(in_profile)} de {len(jobs)} ofertas con título afín (descartadas {len(jobs) - len(in_profile)})")
    candidates = [job for job in in_profile if needs_detail_before_location(job) or is_in_target_location(job)]
    print(f"[*] Cobertura geográfica preliminar: {len(candidates)} candidatas (descartadas {len(in_profile) - len(candidates)})")
    print(f"[*] Verificando enlaces y leyendo descripciones de {len(candidates)} vacantes...")

    linkedin_candidates = [j for j in candidates if "linkedin.com" in j.get("url", "").lower()]
    other_candidates = [j for j in candidates if "linkedin.com" not in j.get("url", "").lower()]

    opened = []
    if other_candidates:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            other_results = list(executor.map(verify_job_url, other_candidates))
        opened.extend(j for j, ok in zip(other_candidates, other_results) if ok)

    if linkedin_candidates:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            li_results = list(executor.map(verify_job_url, linkedin_candidates))
        opened.extend(j for j, ok in zip(linkedin_candidates, li_results) if ok)

    verified = [j for j in opened if is_in_target_location(j)]
    print(f" [✓] Enlaces abiertos: {len(opened)} (descartadas {len(candidates) - len(opened)}); "
          f"en Antioquia o remotas/híbridas: {len(verified)}")
    if LINKEDIN_STATS:
        print(f"     LinkedIn: {dict(LINKEDIN_STATS)}")
    return verified

def export_csv(vacantes):
    """Exporta las vacantes ordenadas a CSV para Excel"""
    fieldnames = ["titulo", "empresa", "ubicacion", "rama_principal", "afinidad", "score_pensum", "es_exclusiva_fisica", "programa_inclusion_genero", "convocatoria_exclusiva_mujeres", "es_cierre_inminente", "es_practica", "compensacion", "perfil", "mision", "tareas", "fecha_publicacion", "fuente", "url"]
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
                "score_pensum": v.get("score_pensum", 0),
                "es_exclusiva_fisica": v.get("es_exclusiva_fisica", False),
                "programa_inclusion_genero": v.get("programa_inclusion_genero", False),
                "convocatoria_exclusiva_mujeres": v.get("convocatoria_exclusiva_mujeres", False),
                "es_cierre_inminente": v.get("es_cierre_inminente", False),
                "es_practica": v.get("es_practica", False),
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

def main():
    if "--render-only" in sys.argv:
        print("[*] Modo render-only: verificando y regenerando HTML y CSV desde vacantes_practicas.json...")
        config_ramas = load_json(CONFIG_RAMAS_PATH)
        vacantes = load_json(OUTPUT_JSON)
        vacantes = sellar_registros(filter_verified_jobs(vacantes, max_workers=25))
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(vacantes, f, ensure_ascii=False, indent=2)
        export_csv(vacantes)
        return

    print(encabezado_bot("[PRÁCTICAS] BOT DE RASTREO DE PRÁCTICAS DE INGENIERÍA FÍSICA"))
    
    config_ramas = load_json(CONFIG_RAMAS_PATH)
    collected = {}

    def add_jobs(jobs, label):
        added = 0
        for job in jobs:
            key = canonical_job_url(job.get("url"))
            if key and key not in collected:
                collected[key] = job
                added += 1
        if jobs:
            print(f"    {label}: {len(jobs)} ofertas (+{added} nuevas)")
        return added

    # 1. Convocatorias destacadas curadas a mano: se publican sin filtro de perfil.
    convocatorias_destacadas = load_json(CONVOCATORIAS_DESTACADAS_PATH)
    if isinstance(convocatorias_destacadas, list):
        print(f"[*] Cargando {len(convocatorias_destacadas)} convocatorias verificadas (Magneto365, Jooble, Portales de Antioquia)...")
        add_jobs([{**c, "curada": True} for c in convocatorias_destacadas if c.get("url")], "Destacadas")

    target_companies = load_target_companies()

    # 2. Computrabajo Antioquia (2 páginas por búsqueda, en paralelo)
    computrabajo_queries = [
        "practicante",
        "practicante ingenieria",
        "practicante electronica",
        "practicante mantenimiento",
        "practicante automatizacion",
        "practicante datos",
        "practicante electromecanico",
        "practicante instrumentacion",
        "practicante metrologia",
        "practicante fisica",
        "practicante mecatronica",
        "practicante electrica",
        "practicante mecanica",
        "practicante laboratorio",
        "practicante calidad",
        "practicante produccion",
        "practicante proyectos",
        "estudiante en practica",
        "aprendiz universitario",
        "practica profesional",
        *CARRERAS_ESPEJO_QUERIES,
    ]
    print(f"\n[*] Rastreando Computrabajo Antioquia ({len(computrabajo_queries)} búsquedas)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for q_ct, jobs in zip(computrabajo_queries, executor.map(scrape_computrabajo_query, computrabajo_queries)):
            add_jobs(jobs, f"Computrabajo '{q_ct}'")

    # 3. Magneto365 (API pública, 4 páginas por búsqueda): Antioquia con
    # cualquier modalidad y el resto de Colombia si es remoto o híbrido.
    magneto_queries = [
        "practicante",
        "practicante ingenieria",
        "practica ingenieria",
        "practicante ingenieria fisica",
        "practicante fisica",
        "practicante electronica",
        "practicante electrica",
        "practicante automatizacion",
        "practicante mecatronica",
        "practicante mecanica",
        "practicante datos",
        "practicante analitica",
        "practicante desarrollo",
        "practicante mantenimiento",
        "practicante energia",
        "practicante materiales",
        "practicante calidad laboratorio",
        "practicante proyectos",
        "practicante procesos",
        "practicante planta",
        "practicante investigacion",
        "practicante biomedica",
        "practicante telecomunicaciones",
        "practicante quimica",
        "practicante simulacion",
        "estudiante en practica",
        "aprendiz universitario",
        "semillero",
        "trainee ingenieria",
        "pasantia ingenieria",
        "practicas universitarias",
        "practicas 2026",
        "practicas 2027",
        "practicas universitarias 2027-1",
        "aprendices y practicantes 2027-1",
    ]
    print(f"\n[*] Rastreando Magneto365 en tiempo real ({len(magneto_queries)} búsquedas)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for q_mag, jobs in zip(magneto_queries, executor.map(scrape_magneto_query, magneto_queries)):
            add_jobs(jobs, f"Magneto365 '{q_mag}'")

    print(f"\n[*] Magneto365 por empresa objetivo ({len(target_companies)} empresas)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        mag_comp_futures = [executor.submit(scrape_magneto_query, f"practicante {comp}", 1) for comp in target_companies]
        for comp, fut in zip(target_companies, mag_comp_futures):
            try:
                add_jobs(fut.result(), f"Magneto365 {comp}")
            except Exception:
                pass

    # 4. ElEmpleo.com (Medellín)
    elempleo_queries = [
        "practicante",
        "practicante ingenieria",
        "practicante automatizacion",
        "practicante electromecanico",
        "practicante electronica",
        "practicante datos",
        "practicante fisica",
        "practicante mantenimiento",
        "practicante mecatronica",
        "practicante electrica",
        "practicante mecanica",
        "aprendiz universitario",
        *CARRERAS_ESPEJO_QUERIES,
    ]
    print(f"\n[*] Rastreando ElEmpleo.com Medellín ({len(elempleo_queries)} búsquedas)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for q_ee, jobs in zip(elempleo_queries, executor.map(scrape_elempleo_query, elempleo_queries)):
            add_jobs(jobs, f"ElEmpleo '{q_ee}'")

    # 5. FirstJob Colombia (Semilleros Multinacionales)
    firstjob_queries = ["practicante", "intern", "ingenieria", "trainee"]
    print(f"\n[*] Rastreando FirstJob Colombia ({len(firstjob_queries)} búsquedas)...")
    for q_fj in firstjob_queries:
        add_jobs(scrape_firstjob_query(q_fj), f"FirstJob '{q_fj}'")

    # 5b. Portales corporativos en Workday (prácticas que a veces no llegan a LinkedIn).
    portales = load_json(PORTALES_WORKDAY_PATH) or []
    print(f"\n[*] Rastreando {len(portales)} portales corporativos Workday...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for portal, jobs in zip(portales, executor.map(scrape_workday_portal, portales)):
            add_jobs(jobs, f"Workday {portal['empresa']}")

    # 6. LinkedIn Medellín: consultas paraguas de alta cobertura (4 páginas) + categorías del pénsum.
    umbrella_medellin_queries = [
        "practicante",
        "practicantes",
        "practicante ingenieria",
        "estudiante en practica",
        "aprendiz universitario",
        "semillero practicantes",
        "intern",
        "trainee",
    ]
    print(f"\n[*] Rastreando LinkedIn Medellín (consultas paraguas de cobertura total)...")
    for q_umb in umbrella_medellin_queries:
        add_jobs(scrape_linkedin_query(q_umb, location="Medellin, Antioquia, Colombia", pages=4), f"LinkedIn Medellín paraguas '{q_umb}'")

    # 6a-bis. LinkedIn Antioquia general: captura municipios como Bello, Rionegro, Itagüí,
    # Envigado, Sabaneta, La Estrella, Guarne, Girardota, Apartadó y Oriente Antioqueño.
    antioquia_queries = [
        "practicante",
        "practicante ingenieria",
        "practicante electronica",
        "practicante mecatronica",
        "practicante mecanica",
        "practicante electrica",
        "practicante datos",
        "practicante automatizacion",
        "practicante mantenimiento",
        "practicante calidad",
        "practicante laboratorio",
        "practicante produccion",
        "practicante proyectos",
        "estudiante en practica",
        "aprendiz universitario",
        "intern engineering",
    ]
    print(f"\n[*] Rastreando LinkedIn Antioquia general ({len(antioquia_queries)} búsquedas para cubrir todos los municipios)...")
    for q_ant in antioquia_queries:
        add_jobs(scrape_linkedin_query(q_ant, location="Antioquia, Colombia", pages=3), f"LinkedIn Antioquia '{q_ant}'")

    print(f"\n[*] Rastreando LinkedIn Jobs para {len(SEARCH_QUERIES)} categorías del pénsum UNAL...")
    for q in SEARCH_QUERIES:
        if time_budget_exceeded(margin_seconds=600):
            print("    [!] Presupuesto de tiempo alcanzado en categorías LinkedIn; pasando a verificación.")
            break
        add_jobs(scrape_linkedin_query(q, pages=2), f"LinkedIn '{q}'")

    # 6b. LinkedIn en todo Colombia: solo sobreviven avisos remotos o híbridos.
    print(f"\n[*] Buscando prácticas remotas/híbridas en Colombia ({len(REMOTE_COLOMBIA_QUERIES)} búsquedas)...")
    for q in REMOTE_COLOMBIA_QUERIES:
        if time_budget_exceeded(margin_seconds=480):
            break
        add_jobs(scrape_linkedin_query(q, location="Colombia", pages=2), f"Colombia remoto/híbrido '{q}'")

    # 6c. Remoto internacional: exige práctica en el título y modalidad remota.
    print(f"\n[*] Buscando prácticas remotas internacionales en {len(REMOTE_GLOBAL_SEARCH_QUERIES)} áreas...")
    for query in REMOTE_GLOBAL_SEARCH_QUERIES:
        if time_budget_exceeded(margin_seconds=360):
            break
        add_jobs(scrape_linkedin_query(query, location="Worldwide"), f"Remoto mundial '{query}'")

    # 6d. Buscador web abierto: amplía el alcance a portales corporativos y bolsas
    # que no aparecen en las APIs anteriores. Las búsquedas web son pistas y la
    # página de destino se verifica antes de publicar.
    print(f"\n[*] Ampliando rastreo con {len(WEB_SEARCH_QUERIES)} búsquedas web...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        web_futures = [
            executor.submit(scrape_web_query, query, scope)
            for query, scope in WEB_SEARCH_QUERIES
        ]
        for (query, scope), future in zip(WEB_SEARCH_QUERIES, web_futures):
            try:
                jobs = future.result()
            except Exception:
                jobs = []
            add_jobs(jobs, f"Web {scope.lower()} '{query}'")

    # 7. LinkedIn por todas las empresas objetivo en Antioquia (filtrando coincidencias reales de empresa).
    print(f"\n[*] Rastreando practicantes en las {len(target_companies)} empresas objetivo en LinkedIn...")
    for comp in target_companies:
        if time_budget_exceeded(margin_seconds=300):
            print("    [!] Presupuesto de tiempo alcanzado en empresas LinkedIn; pasando a verificación.")
            break
        add_jobs(
            scrape_linkedin_query(f"practicante {comp}", location="Antioquia, Colombia", pages=1, required_company=comp),
            f"LinkedIn {comp}",
        )

    print(f"\n[*] Total de vacantes únicas recolectadas: {len(collected)}")
    # Las vacantes de la corrida anterior que no reaparecieron (portal caído,
    # 429, cambio de orden) se vuelven a verificar en lugar de perderse.
    previous_jobs = load_json(OUTPUT_JSON)
    all_raw_jobs = merge_job_snapshots(list(collected.values()), previous_jobs if isinstance(previous_jobs, list) else [])
    print(f"[*] Con la corrida anterior: {len(all_raw_jobs)} vacantes para verificar")
    verified_raw_jobs = filter_verified_jobs(all_raw_jobs, max_workers=25)
    print(f"[*] Clasificando, filtrando y ordenando {len(verified_raw_jobs)} vacantes verificadas por afinidad al pénsum UNAL...")
    
    classified_jobs = []
    for j in verified_raw_jobs:
        classified = classify_and_score_job(j, config_ramas)
        if classified:
            classified_jobs.append(classified)
        
    # Ordenar por Score de Afinidad del Pénsum
    classified_jobs.sort(key=lambda x: x.get("score_pensum", 0), reverse=True)
    sellar_registros(classified_jobs)
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(classified_jobs, f, ensure_ascii=False, indent=2)
    print(f" [✓] Datos JSON guardados en: {OUTPUT_JSON} ({len(classified_jobs)} vacantes afines)")
    
    export_csv(classified_jobs)
    
    print("\n" + "="*70)
    print(" ¡RASTREO DE PRÁCTICAS COMPLETADO! Ejecuta bot_pagina.py para regenerar la página.")
    print("="*70)

if __name__ == "__main__":
    main()
