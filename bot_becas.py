#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BOT DE BECAS Y PASANTÍAS DE INVESTIGACIÓN INTERNACIONALES (PORTAL IPF)
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Universidad Nacional de Colombia - Sede Medellín • Ingeniería Física
Licencia: PolyForm Noncommercial 1.0.0 con descargo de responsabilidad (ver LICENSE)
=============================================================================
Rastrea en vivo las convocatorias vigentes del ICETEX (entrando al detalle de
cada beca y filtrando estrictamente áreas STEM / Ingeniería Física), verifica
la disponibilidad de cada enlace (limpieza automática de convocatorias caídas
o vencidas) y compila los programas mundiales de pasantías de investigación de
pregrado y becas de posgrado para Ingeniería Física.
Salida: becas_internacionales.json (la página la arma bot_pagina.py).
"""

import concurrent.futures
import json
import os
import re
import sys
from datetime import datetime
from html import unescape
from urllib.parse import urljoin, urlparse

import requests

from firma import encabezado_bot, sellar_registros

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BECAS_JSON_PATH = os.path.join(BASE_DIR, "becas_internacionales.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}

# Filtro de exclusión para descartar becas de ICETEX ajenas a Ingeniería Física / STEM
NON_STEM_BECAS_RE = re.compile(
    r"\b(?:multicultural\s+societies|inclusivity\s+in\s+multicultural|servidores\s+p[uú]blicos|"
    r"derechos\s+humanos|ciencias\s+sociales|literatura|artes\s+esc[eé]nicas|m[uú]sica|baile|danza|"
    r"gastronom[ií]a|turismo|deporte|entrenadores\s+deportivos|administraci[oó]n\s+judicial|"
    r"ense[ñn]anza\s+del\s+(?:espa[ñn]ol|franc[eé]s|ingl[eé]s\s+como\s+lengua)|asistentes\s+de\s+idiomas|"
    r"periodismo|comunicaci[oó]n\s+social|psicolog[ií]a\s+cl[ií]nica|odontolog[ií]a|enfermer[ií]a|"
    r"derecho\s+penal|relaciones\s+internacionales\s+y\s+diplomacia)\b",
    re.IGNORECASE,
)

STEM_POSITIVE_RE = re.compile(
    r"\b(?:ingenier[ií]a|engineering|f[ií]sica|physics|ciencias|science|stem|datos|data|"
    r"inteligencia\s+artificial|artificial\s+intelligence|tecnolog[ií]a|technology|matem[aá]ticas|"
    r"energ[ií]a|energy|materiales|materials|nanotecnolog[ií]a|[oó]ptica|photonics|quantum|cu[aá]ntic|"
    r"computaci[oó]n|automatizaci[oó]n|electr[oó]nica|rob[oó]tica|investigaci[oó]n|research|innovation|"
    r"academia[\s-]industry|maestr[ií]as?|doctorados?|posgrado|postgraduate|master|phd)\b",
    re.IGNORECASE,
)

PAISES_CONOCIDOS = [
    ("Suiza", r"\bsuiza\b|switzerland|zurich|lausanne|geneva|ginebra"),
    ("Alemania", r"\balemania\b|germany|munich|aachen|dresden|heidelberg|daad"),
    ("Canadá", r"\bcanad[aá]\b|waterloo|toronto|mcgill|mitacs"),
    ("Estados Unidos", r"\bestados\s+unidos\b|\bu\.?s\.?a\.?\b|united\s+states|fulbright"),
    ("Japón", r"\bjap[oó]n\b|japan|okinawa|mext|tokio|tokyo"),
    ("China", r"\bchina\b|tsinghua|zhejiang|beijing|pekin"),
    ("India", r"\bindia\b|\bitec\b"),
    ("Reino Unido", r"\breino\s+unido\b|\bu\.?k\.?\b|united\s+kingdom|salford|london|oxford|cambridge|chevening"),
    ("España", r"\bespa[ñn]a\b|spain|madrid|barcelona|valencia|carolina"),
    ("Francia", r"\bfrancia\b|france|paris|saclay|grenoble"),
    ("Italia", r"\bitalia\b|italy|trieste|ictp|mil[aá]n"),
    ("Brasil", r"\bbrasil\b|brazil|campinas|sao\s+paulo|cnpem|sirius"),
    ("Singapur", r"\bsingapur\b|singapore"),
    ("Corea del Sur", r"\bcorea\b|korea|kaist|seoul"),
    ("Arabia Saudita", r"\barabia\s+saudita\b|saudi\s+arabia|kaust"),
    ("Hungría", r"\bhungr[ií]a\b|hungary|stipendium\s+hungaricum"),
    ("Austria", r"\baustria\b|vienna|viena|ista"),
]

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def clean_text(raw):
    text = re.sub(r"<(?:script|style)[^>]*>.*?</(?:script|style)>", " ", raw or "", flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    # Corregir signos de interrogación invertidos mal usados como comillas en ICETEX
    text = re.sub(r"¿([^?¿]+?)¿", r'"\1"', text)
    return re.sub(r"\s+", " ", text).strip()


def infer_country(text, default="Internacional / Multidestino"):
    for nombre, pattern in PAISES_CONOCIDOS:
        if re.search(pattern, text, re.IGNORECASE):
            return nombre
    return default


def parse_spanish_date(text):
    """Extrae una fecha en español ('15 de noviembre de 2026' o '2026-11-30') y devuelve (iso, texto)."""
    m_iso = re.search(r"\b(202[6-9]-\d{2}-\d{2})\b", text)
    if m_iso:
        return m_iso.group(1), m_iso.group(1)
    m_es = re.search(
        r"\b(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\s+(?:de|del)\s+(202[6-9])\b",
        text,
        re.IGNORECASE,
    )
    if m_es:
        day = int(m_es.group(1))
        month = MESES_ES[m_es.group(2).lower()]
        year = int(m_es.group(3))
        try:
            iso = datetime(year, month, day).date().isoformat()
            return iso, f"{day} de {m_es.group(2).lower()} de {year}"
        except ValueError:
            pass
    return "", ""


def enrich_icetex_detail(item):
    """Descarga el detalle de una convocatoria de ICETEX para extraer país, cobertura, cierre y relevancia STEM."""
    url = item["url"]
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        full_text = clean_text(r.text)
    except Exception:
        full_text = ""

    combined = f"{item['titulo']} {full_text[:3000]}"
    if NON_STEM_BECAS_RE.search(item["titulo"]):
        return None
    if NON_STEM_BECAS_RE.search(combined) and not STEM_POSITIVE_RE.search(item["titulo"]):
        return None

    pais = infer_country(combined, default="Global / Varios")
    item["pais"] = pais

    # Detectar cobertura porcentual si aparece en el título o detalle
    cov_m = re.search(r"(\d{2,3}\s*%[^.;,\n]{0,50})", item["titulo"])
    if cov_m:
        item["cobertura"] = cov_m.group(1).strip()
    elif re.search(r"\b100\s*%\b", full_text):
        item["cobertura"] = "Hasta 100% según modalidad de la convocatoria en ICETEX"

    # Detectar fecha de cierre en la ficha de ICETEX
    cierre_zone = re.search(
        r"(?:fecha\s+de\s+cierre|cierre\s+de\s+la\s+convocatoria|postulaciones\s+hasta|vence\s+el)[^.]{0,120}",
        full_text,
        re.IGNORECASE,
    )
    if cierre_zone:
        iso, label = parse_spanish_date(cierre_zone.group(0))
        if iso:
            try:
                if (datetime.fromisoformat(iso).date() - datetime.now().date()).days < 0:
                    return None
            except ValueError:
                pass
            item["fecha_cierre_iso"] = iso
            item["fechas"] = f"Cierre: {label}"

    # Clasificar nivel académico
    t_lower = item["titulo"].lower()
    if re.search(r"maestr[ií]a|master|doctorado|phd|posgrado", t_lower):
        item["nivel"] = "Posgrado (Maestría / Doctorado)"
        item["tipo"] = "Beca de Posgrado (ICETEX)"
    elif re.search(r"pasant[ií]a|intern|pregrado|semillero", t_lower):
        item["nivel"] = "Pregrado / Pasantía"
        item["tipo"] = "Pasantía Internacional (ICETEX)"
    else:
        item["nivel"] = "Curso / Estancia Corta"
        item["tipo"] = "Curso o Estancia Internacional (ICETEX)"

    return item


def scrape_icetex_becas():
    """Rastrea convocatorias vigentes de becas en el portal oficial del ICETEX y filtra solo STEM."""
    url = "https://web.icetex.gov.co/es/becas/becas-para-estudios-en-el-exterior/becas-vigentes"
    print("\n[*] Rastreando becas vigentes en el portal de ICETEX Cooperación...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        items = re.findall(
            r'<a[^>]*href="([^"]+)"[^>]*class="lnk_art_nuevo_cred"[^>]*>(.*?)</a>',
            r.text,
            re.DOTALL,
        )
        candidates = []
        seen_urls = set()
        for link, raw_title in items:
            clean_link = urljoin(url, link.strip())
            if clean_link in seen_urls:
                continue
            seen_urls.add(clean_link)
            title = clean_text(raw_title)
            if not title or NON_STEM_BECAS_RE.search(title):
                continue
            candidates.append({
                "titulo": title,
                "url": clean_link,
                "entidad": "ICETEX Cooperación Internacional",
                "tipo": "Beca Internacional Vigente (ICETEX)",
                "nivel": "Posgrado / Especialización",
                "pais": infer_country(title, "Global / Varios"),
                "cobertura": "Convocatoria oficial ICETEX (ver porcentaje en ficha)",
                "area": "Ingeniería, Tecnología, Ciencias y Analítica",
                "fechas": "Convocatoria abierta en ICETEX",
                "descripcion": "Convocatoria oficial activa gestionada por la Dirección de Cooperación Internacional del ICETEX para profesionales y estudiantes colombianos en áreas de ciencia, tecnología e ingeniería.",
                "destacada": False,
            })

        enriched = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            for res in ex.map(enrich_icetex_detail, candidates):
                if res:
                    enriched.append(res)

        print(f" [✓] {len(enriched)} becas vigentes afines a STEM verificadas en ICETEX (de {len(items)} totales).")
        return enriched
    except Exception as e:
        print(f" [!] Error en ICETEX: {e}")
        return []


def verify_beca_url(beca):
    """Confirma que el portal oficial de la beca o pasantía responde correctamente (limpieza de enlaces rotos)."""
    url = beca.get("url", "")
    if not url or not url.startswith("http"):
        return False
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code in (404, 410):
            return False
        # Algunos portales gubernamentales/universitarios devuelven 403 ante User-Agent de script pero existen
        return r.status_code < 500
    except requests.RequestException:
        # Si es una beca insignia destacada con portal institucional conocido, conservar ante timeout puntual
        return bool(beca.get("destacada"))


def canonical_beca_url(url):
    parsed = urlparse(str(url or "").strip())
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/").lower()
    return f"{host}{path}"


def compile_global_opportunities(icetex_live):
    """Compila pasantías de investigación de pregrado y becas globales de posgrado para Ingeniería Física."""
    print("\n[*] Compilando catálogo global de pasantías de investigación y becas para Ingeniería Física...")

    becas_catalogo = [
        # =====================================================================
        # 1. PASANTÍAS DE INVESTIGACIÓN DE PREGRADO (SUMMER RESEARCH & INTERNSHIPS)
        # =====================================================================
        {
            "titulo": "CERN Summer Student Programme & Technical Studentships (Ginebra)",
            "entidad": "Organización Europea para la Investigación Nuclear (CERN)",
            "pais": "Suiza",
            "tipo": "Pasantía de Investigación (Pregrado / Maestría)",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "100% financiado (93 CHF/día libres de impuestos + tiquetes aéreos + seguro médico)",
            "area": "Física Experimental, Aceleradores, Detectores, Criogenia, Electrónica y Computación",
            "fechas": "Convocatoria anual: noviembre a enero (estancia junio–agosto, 8 a 13 semanas)",
            "descripcion": "Una de las estancias científicas más prestigiosas del mundo para estudiantes de Ingeniería Física y Física. Trabaja directamente en experimentos del LHC, instrumentación criogénica, superconductores, electrónica de adquisición de datos (DAQ) y física médica.",
            "url": "https://careers.cern/summer",
            "destacada": True,
        },
        {
            "titulo": "Mitacs Globalink Research Internship (Universidades de Canadá)",
            "entidad": "Gobierno de Canadá • Mitacs",
            "pais": "Canadá",
            "tipo": "Pasantía de Investigación de Verano (12 semanas)",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "100% financiado (Tiquetes aéreos, alojamiento, estipendio de manutención y seguro)",
            "area": "Física Aplicada, Computación Cuántica, Fotónica, Nanotecnología, Energías e IA",
            "fechas": "Convocatoria anual: agosto a septiembre (estancia mayo–agosto)",
            "descripcion": "Pasantías de investigación de 12 semanas para estudiantes de pregrado en más de 70 universidades canadienses (Waterloo / Institute for Quantum Computing, Toronto, McGill, UBC) bajo supervisión directa de profesores líderes.",
            "url": "https://www.mitacs.ca/our-programs/globalink-research-internship-students/",
            "destacada": True,
        },
        {
            "titulo": "DAAD RISE Worldwide & Becas para Colombia (Alemania)",
            "entidad": "Servicio Alemán de Intercambio Académico (DAAD Colombia)",
            "pais": "Alemania",
            "tipo": "Pasantía de Investigación y Becas STEM",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "Estipendio mensual en euros + auxilio de tiquetes internacionales + seguro médico",
            "area": "Física, Óptica, Cuántica, Ciencia de Materiales, Automatización y Energía",
            "fechas": "Convocatorias escalonadas durante el año (RISE: octubre–diciembre)",
            "descripcion": "Estancias de investigación trabajando con investigadores doctorales de universidades técnicas alemanas (TU Munich, RWTH Aachen, KIT, Heidelberg) e institutos Fraunhofer, Helmholtz y Max Planck.",
            "url": "https://www.daad.co/es/becas/buscador-de-becas/",
            "destacada": True,
        },
        {
            "titulo": "Pasantías Técnicas Internacionales Remuneradas STEM (IAESTE Colombia)",
            "entidad": "IAESTE Colombia • Asociación Internacional para el Intercambio de Estudiantes Técnicos",
            "pais": "Alemania, Suiza, Austria, Japón, Brasil y +80 países",
            "tipo": "Pasantía Industrial o de Laboratorio (6 semanas a 12 meses)",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "Salario/estipendio mensual que cubre alojamiento y manutención completa en el país destino",
            "area": "Ingeniería Física, Electrónica, Mecatrónica, Control, Instrumentación y Materiales",
            "fechas": "Convocatoria nacional anual (enero–marzo) y ofertas de canje continuo",
            "descripcion": "Prácticas profesionales y pasantías remuneradas en empresas tecnológicas e institutos de investigación internacionales. Válidas para homologar o realizar práctica internacional desde pregrado.",
            "url": "https://iaeste.org.co/",
            "destacada": True,
        },
        {
            "titulo": "EPFL Excellence Research Internship Program — E3 (Lausana, Suiza)",
            "entidad": "École Polytechnique Fédérale de Lausanne (EPFL)",
            "pais": "Suiza",
            "tipo": "Pasantía de Investigación de Verano (8 a 12 semanas)",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "100% financiado (Estipendio de 1.600 CHF/mes + reembolso de tiquetes aéreos + alojamiento)",
            "area": "Fotónica, Física Cuántica, Microingeniería, Materiales, Semiconductores y Biofísica",
            "fechas": "Convocatoria anual: octubre a noviembre/diciembre",
            "descripcion": "Inmersión intensiva en los laboratorios de la EPFL (Escuela de Ciencias Básicas y Escuela de Ingeniería). Altamente afín a las líneas de óptica, estado sólido, instrumentación y nanotecnología de Ingeniería Física.",
            "url": "https://eee.epfl.ch/",
            "destacada": True,
        },
        {
            "titulo": "OIST Research Internship Program (Okinawa, Japón)",
            "entidad": "Okinawa Institute of Science and Technology (OIST)",
            "pais": "Japón",
            "tipo": "Pasantía de Investigación Científica (2 a 6 meses)",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "100% financiado (2.400 JPY/día libres de impuestos + tiquetes aéreos + apartamento en campus + visa)",
            "area": "Física Cuántica, Óptica y Fotónica, Materia Condensada, Nanotecnología y Ciencia de Datos",
            "fechas": "Dos cortes anuales: cierre el 15 de abril y el 15 de octubre",
            "descripcion": "Estancia de investigación de tiempo completo en uno de los centros interdisciplinarios más avanzados de Asia. Abierta a estudiantes de últimos semestres de pregrado y maestría de cualquier nacionalidad.",
            "url": "https://admissions.oist.jp/apply-research-internship",
            "destacada": True,
        },
        {
            "titulo": "KAUST Visiting Student Research Program — VSRP (Arabia Saudita)",
            "entidad": "King Abdullah University of Science and Technology (KAUST)",
            "pais": "Arabia Saudita",
            "tipo": "Pasantía de Investigación (3 a 6 meses)",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "100% financiado (Estipendio de 1.000 USD/mes + tiquetes aéreos + suite privada + seguro médico)",
            "area": "Fotónica, Semiconductores, Energía Solar Fotovoltaica, Materiales 2D, Sensores y Simulación",
            "fechas": "Convocatoria abierta todo el año (postulación continua)",
            "descripcion": "Más de 100 proyectos abiertos para estudiantes de pregrado (3er y 4to año) y maestría en laboratorios de clase mundial con salas limpias de nanofabricación, espectroscopía ultrarrápida y supercomputación.",
            "url": "https://vsrp.kaust.edu.sa/",
            "destacada": True,
        },
        {
            "titulo": "CNPEM — Programa Bolsas de Verão (Sincrotrón Sirius, Brasil)",
            "entidad": "Centro Nacional de Pesquisa em Energia e Materiais (CNPEM)",
            "pais": "Brasil",
            "tipo": "Pasantía de Investigación en Sincrotrón (enero–febrero)",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "100% financiado para estudiantes de Latinoamérica (Tiquetes aéreos, hospedaje, alimentación y estipendio)",
            "area": "Luz Sincrotrón, Nanotecnología, Caracterización de Materiales (DRX/SEM), Instrumentación y Biofísica",
            "fechas": "Convocatoria anual: agosto a octubre (estancia en enero–febrero)",
            "descripcion": "Trabaja en Campinas junto a científicos del acelerador de electrones Sirius (4ta generación) y el Laboratorio Nacional de Nanotecnología (LNNano). Dirigido exclusivamente a estudiantes de pregrado de América Latina.",
            "url": "https://pages.cnpem.br/bolsasdeverao/",
            "destacada": True,
        },
        {
            "titulo": "HZDR Summer Student Program (Dresde, Alemania)",
            "entidad": "Helmholtz-Zentrum Dresden-Rossendorf (HZDR)",
            "pais": "Alemania",
            "tipo": "Pasantía de Investigación en Laboratorio Nacional (6 a 9 semanas)",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "Estipendio de 36 EUR/día + alojamiento gratuito en Dresde + subsidio de transporte",
            "area": "Física de Radiaciones, Física Médica, Campos Magnéticos Intensos, Láseres de Alta Potencia y Materiales",
            "fechas": "Convocatoria anual: diciembre a febrero (estancia julio–septiembre)",
            "descripcion": "Estancia de investigación experimental en uno de los principales centros de la Asociación Helmholtz en Alemania, ideal para las ramas de física de radiaciones, aceleradores, materia condensada y óptica.",
            "url": "https://www.hzdr.de/db/Cms?pNid=2519",
            "destacada": True,
        },
        {
            "titulo": "Perimeter Institute — PSI Start Program (Waterloo, Canadá)",
            "entidad": "Perimeter Institute for Theoretical Physics",
            "pais": "Canadá",
            "tipo": "Escuela + Pasantía de Investigación Cuántica y Física",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "Financiación completa para la estancia presencial de investigación en Waterloo (estipendio, viaje y alojamiento)",
            "area": "Física Cuántica, Materia Condensada, Información Cuántica, Relatividad y Física Matemática",
            "fechas": "Convocatoria anual: octubre a enero",
            "descripcion": "Combina una escuela intensiva en línea de diez semanas con una pasantía de investigación remunerada en el Perimeter Institute para estudiantes sobresalientes de física e ingeniería física.",
            "url": "https://perimeterinstitute.ca/psi-start-program",
            "destacada": True,
        },

        # =====================================================================
        # 2. BECAS DE POSGRADO (MAESTRÍA, DOCTORADO Y DIPLOMADOS CIENTÍFICOS)
        # =====================================================================
        {
            "titulo": "Becas de Maestría Erasmus Mundus (Europhotonics / QuanTEEM / MaMaSelf)",
            "entidad": "Comisión Europea • Erasmus+ Joint Masters",
            "pais": "Francia, Alemania, España, Italia (Multidestino)",
            "tipo": "Maestría Conjunta Europea con Beca Completa",
            "nivel": "Posgrado (Maestría / Doctorado)",
            "cobertura": "100% matrícula + estipendio de 1.400 EUR/mes (durante 24 meses) + seguro médico",
            "area": "Óptica, Fotónica, Tecnologías Cuánticas, Nanotecnología y Ciencia de Materiales",
            "fechas": "Convocatorias anuales: octubre a febrero",
            "descripcion": "Programas de maestría de doble o triple titulación europea donde cursas cada semestre en una universidad distinta (ej. Europhotonics en Marsella, Karlsruhe y Barcelona; QuanTEEM en tecnologías cuánticas; MaMaSelf en materiales en grandes instalaciones).",
            "url": "https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en",
            "destacada": True,
        },
        {
            "titulo": "ICTP Postgraduate Diploma Programme (Trieste, Italia)",
            "entidad": "Centro Internacional Abdus Salam de Física Teórica (ICTP - UNESCO / OIEA)",
            "pais": "Italia",
            "tipo": "Posgrado Intensivo de Preparación Doctoral (1 año)",
            "nivel": "Posgrado (Maestría / Doctorado)",
            "cobertura": "100% financiado (Estipendio mensual en euros + tiquetes aéreos ida y vuelta + alojamiento)",
            "area": "Materia Condensada, Física de Altas Energías, Física de la Tierra, Cuántica y Física Matemática",
            "fechas": "Convocatoria anual: cierra entre diciembre y enero",
            "descripcion": "Programa de excelencia en Trieste diseñado para jóvenes físicos e ingenieros físicos de países en desarrollo, con acceso directo a doctorados en Europa y los laboratorios del sistema científico de Trieste.",
            "url": "https://www.ictp.it/opportunity/ictp-postgraduate-diploma-programme",
            "destacada": True,
        },
        {
            "titulo": "Fulbright Colombia — Becas de Posgrado STEM en Estados Unidos",
            "entidad": "Comisión Fulbright Colombia • MinCiencias / ICETEX",
            "pais": "Estados Unidos",
            "tipo": "Beca de Maestría y Doctorado (PhD)",
            "nivel": "Posgrado (Maestría / Doctorado)",
            "cobertura": "Exención/cobertura de matrícula + estipendio mensual de sostenimiento + tiquetes + seguro ASPE + visa J-1",
            "area": "Ingeniería Física, Física Aplicada, Ciencia de Materiales, Óptica, Energía, IA y Bioingeniería",
            "fechas": "Convocatoria anual en Colombia: febrero a mayo",
            "descripcion": "Principal programa binacional de becas de posgrado e investigación en universidades estadounidenses de primer orden, con acompañamiento integral en el proceso de admisión y exámenes estandarizados.",
            "url": "https://fulbright.edu.co/",
            "destacada": True,
        },
        {
            "titulo": "Colfuturo — Programa Crédito-Beca y Convenios de Cooperación STEM",
            "entidad": "Fundación para el Futuro de Colombia (COLFUTURO) • MinCiencias",
            "pais": "Global (+130 convenios en Europa, EE. UU., Reino Unido y Australia)",
            "tipo": "Crédito-Beca de Maestría y Doctorado (hasta 80% de condonación)",
            "nivel": "Posgrado (Maestría / Doctorado)",
            "cobertura": "Hasta 50.000 USD + descuentos del 20% al 100% en matrícula por convenios directos con universidades top",
            "area": "Todas las ramas de Ingeniería, Física, Ciencias Básicas, Energía y Ciencia de Datos",
            "fechas": "Convocatoria anual: enero a febrero / Programa Semillero de Talentos todo el año",
            "descripcion": "Financia estudios de maestría y doctorado en las mejores universidades del mundo (ETH Zürich, EPFL, TU Delft, Imperial College, PSL, TU Munich) con condonación de hasta el 80% al regresar a Colombia.",
            "url": "https://www.colfuturo.org/programas/credito-beca",
            "destacada": True,
        },
        {
            "titulo": "Maestrías y Doctorados en Ciencias e Ingeniería (China / CSC - ICETEX)",
            "entidad": "Gobierno de la República Popular China • China Scholarship Council (CSC) / ICETEX",
            "pais": "China",
            "tipo": "Beca Completa de Posgrado (Maestría / Doctorado)",
            "nivel": "Posgrado (Maestría / Doctorado)",
            "cobertura": "85% - 100% (Exención total de matrícula, residencia universitaria, seguro médico y estipendio mensual)",
            "area": "Semiconductores, Nanotecnología, Óptica y Fotónica, Materiales Avanzados, Energías Renovables e IA",
            "fechas": "Convocatoria anual ICETEX / Embajada de China: noviembre a febrero",
            "descripcion": "Becas para cursar posgrados en inglés o chino en universidades líderes (Tsinghua, USTC, Zhejiang, Harbin Institute of Technology) con laboratorios de frontera en cuántica, fotónica y materiales.",
            "url": "https://web.icetex.gov.co/es/becas/becas-para-estudios-en-el-exterior/becas-vigentes",
            "destacada": True,
        },
        {
            "titulo": "Beca MEXT (Monbukagakusho) de Investigación y Posgrado en Japón",
            "entidad": "Ministerio de Educación, Cultura, Deporte, Ciencia y Tecnología del Japón (MEXT)",
            "pais": "Japón",
            "tipo": "Beca Completa de Investigación, Maestría y Doctorado",
            "nivel": "Posgrado (Maestría / Doctorado)",
            "cobertura": "100% (Exención total de matrícula + 143.000–145.000 JPY/mes + tiquetes aéreos ida y vuelta)",
            "area": "Física del Estado Sólido, Robótica, Fotónica, Materiales, Electrónica, Cuántica y Energía",
            "fechas": "Convocatoria anual Embajada del Japón / ICETEX: abril a mayo",
            "descripcion": "Permite realizar una estancia como estudiante de investigación y empalmar directamente con maestría o doctorado en universidades imperiales japonesas (Tokyo, Kyoto, Tohoku, Osaka, Tokyo Tech).",
            "url": "https://www.colombia.emb-japan.go.jp/itpr_es/becasMEXT.html",
            "destacada": True,
        },
        {
            "titulo": "Becas Fundación Carolina — Maestrías en Ingeniería, Energía, Fotónica y Datos",
            "entidad": "Fundación Carolina • Cooperación Española",
            "pais": "España",
            "tipo": "Beca de Posgrado y Movilidad en España",
            "nivel": "Posgrado (Maestría / Doctorado)",
            "cobertura": "Exención parcial/total de matrícula + tiquetes aéreos ida y vuelta + seguro médico + ayuda de alojamiento",
            "area": "Fotónica (UPC/ICFO), Energías Renovables, Ciencia de Datos, Automática, Robótica y Materiales",
            "fechas": "Convocatoria anual: enero a marzo",
            "descripcion": "Amplio catálogo de másteres oficiales en la Universitat Politècnica de Catalunya (UPC), Universidad Politécnica de Madrid (UPM), UPV e institutos como el ICFO (Instituto de Ciencias Fotónicas).",
            "url": "https://www.fundacioncarolina.es/formacion/postgrado/",
            "destacada": True,
        },
        {
            "titulo": "Optica Foundation & SPIE Optics and Photonics Education Scholarships",
            "entidad": "Optica (antes OSA) & SPIE — Sociedades Internacionales de Óptica y Fotónica",
            "pais": "Internacional / Aplicable desde Colombia",
            "tipo": "Beca Académica y de Investigación en Óptica y Fotónica",
            "nivel": "Pregrado / Pasantía",
            "cobertura": "Subvenciones directas de 2.500 a 10.000 USD para matrícula, proyectos de grado y asistencia a congresos",
            "area": "Óptica, Fotónica, Láseres, Interferometría, Procesamiento de Imágenes y Fibras Ópticas",
            "fechas": "Convocatoria anual: cierra entre enero y febrero",
            "descripcion": "Dirigida a estudiantes de pregrado y posgrado que desarrollan su trabajo de grado, semillero o investigación en óptica, fotónica, visión artificial o ingeniería láser (incluye capítulos estudiantiles UNAL).",
            "url": "https://spie.org/membership/student-services/scholarships",
            "destacada": True,
        },
        {
            "titulo": "Data Analytics & IA for Decision Making (India / ITEC - ICETEX)",
            "entidad": "Gobierno de la India • Indian Technical and Economic Cooperation (ITEC) / ICETEX",
            "pais": "India",
            "tipo": "Beca Completa Presencial (Curso de Alta Especialización)",
            "nivel": "Curso / Estancia Corta",
            "cobertura": "100% (Tiquetes aéreos ida y vuelta, hospedaje, matrícula y estipendio diario)",
            "area": "Ciencia de Datos, Inteligencia Artificial, Estadística y Modelado Cuantitativo",
            "fechas": "Convocatorias periódicas en ICETEX",
            "descripcion": "Programa intensivo presencial para ingenieros y científicos en el International Statistical Education Centre (ISEC) e institutos tecnológicos de la India (IITs). Formación en analítica avanzada, series de tiempo y modelos predictivos.",
            "url": "https://web.icetex.gov.co/es/-/2026-data-analytics-for-decision-making-india",
            "destacada": True,
        },
    ]

    # Deduplicar por URL canónica y por título para no repetir convocatorias entre catálogo e ICETEX en vivo
    seen_urls = {canonical_beca_url(b["url"]) for b in becas_catalogo if b.get("url")}
    seen_titles = {b["titulo"].lower()[:40] for b in becas_catalogo}

    for ic in icetex_live:
        c_url = canonical_beca_url(ic.get("url"))
        t_prefix = ic.get("titulo", "").lower()[:40]
        if c_url in seen_urls or t_prefix in seen_titles:
            continue
        seen_urls.add(c_url)
        seen_titles.add(t_prefix)
        becas_catalogo.append(ic)

    print(f"[*] Verificando disponibilidad de {len(becas_catalogo)} enlaces de becas y pasantías...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        valid_flags = list(executor.map(verify_beca_url, becas_catalogo))

    verificadas = [b for b, ok in zip(becas_catalogo, valid_flags) if ok]
    print(f" [✓] Enlaces verificados: {len(verificadas)} activas (descartadas {len(becas_catalogo) - len(verificadas)} caídas o cerradas).")

    sellar_registros(verificadas)
    with open(BECAS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(verificadas, f, ensure_ascii=False, indent=2)
    print(f" [✓] Total de {len(verificadas)} becas y pasantías guardadas en: {BECAS_JSON_PATH}")
    return verificadas


def main():
    print(encabezado_bot("[BECAS] BOT DE BECAS Y PASANTÍAS DE INVESTIGACIÓN INTERNACIONALES"))
    compile_global_opportunities(scrape_icetex_becas())


if __name__ == "__main__":
    main()
