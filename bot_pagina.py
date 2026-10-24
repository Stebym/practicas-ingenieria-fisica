#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BOT CONSTRUCTOR DE LA PÁGINA (PORTAL IPF)
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Universidad Nacional de Colombia - Sede Medellín • Ingeniería Física
Licencia: MIT con descargo de responsabilidad (ver LICENSE)
=============================================================================
Reúne lo que dejan los otros cuatro bots y arma la página pública:
  bot_practicas.py   -> vacantes_practicas.json
  bot_retos.py       -> retos_hackatones.json
  bot_becas.py       -> becas_internacionales.json
  bot_convenios.py   -> convenios_internacionales.json
Si un archivo falta o está dañado, usa una lista vacía en vez de romper la
página, e incrusta la firma del proyecto (ver firma.py).
Salida: index.html y dashboard_practicas.html.
"""

import json
import os
import sys

from firma import ANIO, AUTOR, AVISO_LEGAL_CORTO, FIRMA_ID, REPOSITORIO, encabezado_bot, marca_agua

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_HTML = os.path.join(BASE_DIR, "dashboard_practicas.html")
OUTPUT_INDEX = os.path.join(BASE_DIR, "index.html")
FIREBASE_CONFIG_PATH = os.path.join(BASE_DIR, "firebase_config.json")
FUENTES = {
    "vacantes": "vacantes_practicas.json",
    "retos": "retos_hackatones.json",
    "becas": "becas_internacionales.json",
    "convenios": "convenios_internacionales.json",
}


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def json_for_script(data):
    """JSON seguro dentro de <script>: evita que un texto con '</script>' cierre la etiqueta."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def cargar_lista(nombre):
    datos = load_json(os.path.join(BASE_DIR, FUENTES[nombre]), [])
    if not isinstance(datos, list):
        print(f" [!] {FUENTES[nombre]} no es una lista; se usa vacío.")
        return []
    print(f" [✓] {FUENTES[nombre]}: {len(datos)} registros")
    return datos


def build_full_html(vacantes, becas_data, convenios_data, retos_data):
    """Genera el HTML semántico con diseño de laboratorio a partir de los datos de los cuatro bots."""
    vacantes_json_str = json_for_script(vacantes)
    convenios_json_str = json_for_script(convenios_data)
    becas_json_str = json_for_script(becas_data)
    retos_json_str = json_for_script(retos_data)
    firebase_config_str = json_for_script(load_json(FIREBASE_CONFIG_PATH, {}))
    total_retos = sum(1 for r in retos_data if r.get("tipo") != "Plataforma")
    pie_firma = marca_agua(f"© {ANIO} {AUTOR} · Licencia MIT · Portal IPF")

    total_exclusivas = sum(1 for v in vacantes if v.get("es_exclusiva_fisica"))
    total_practicas = sum(1 for v in vacantes if v.get("es_practica"))
    total_convenios = len(convenios_data)
    total_becas = len(becas_data)

    html = f"""<!DOCTYPE html>
<html lang="es" data-ipf="{FIRMA_ID}">
<!-- Portal IPF · © {ANIO} {AUTOR} · Licencia MIT · firma {FIRMA_ID} -->
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prácticas de Ingeniería Física • UNAL Medellín | Jimmy Rosero</title>
  <meta name="description" content="Portal inteligente de convocatorias de prácticas profesionales, pasantías y becas internacionales para estudiantes de Ingeniería Física de la Universidad Nacional de Colombia Sede Medellín. Desarrollado por Jimmy Stebym Rosero Barrera.">
  <meta name="author" content="Jimmy Stebym Rosero Barrera">
  <meta name="generator" content="ipf-{FIRMA_ID}">
  <meta name="color-scheme" content="light dark">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta http-equiv="X-Content-Type-Options" content="nosniff">
  
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
        <div class="live-online-chip" id="liveOnlineBadge" title="Personas con la página abierta en este momento" hidden>
          <span class="live-pulse-dot"></span>
          <span id="liveOnlineCount">conectando…</span>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('todas', document.querySelector('.tab-link:nth-child(1)'))" title="Ver todas las vacantes">
          Vacantes: <strong style="color: var(--accent-cyan);">{len(vacantes)}</strong>
        </div>
        <div class="kpi-chip" onclick="switchMainTab('exclusivas', document.querySelector('.tab-link.exclusive'))" title="Ver vacantes afines a Física">
          Afinidad con Física: <strong style="color: var(--accent-amber);">{total_exclusivas}</strong>
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
      <p><strong>Cobertura:</strong> Antioquia con cualquier modalidad; resto de Colombia solo prácticas remotas o híbridas; exterior solo remotas (confirma en el aviso si aceptan postulantes desde Colombia).</p>
    </section>

    <!-- NAVEGACIÓN POR PESTAÑAS (TABS) -->
    <nav class="tabs-nav" aria-label="Secciones de prácticas">
      <button class="tab-link active" onclick="switchMainTab('todas', this)">
        Todas las Vacantes ({len(vacantes)})
      </button>
      <button class="tab-link exclusive" onclick="switchMainTab('exclusivas', this)">
        Afinidad con Física ({total_exclusivas})
      </button>
      <button class="tab-link urgent" onclick="switchMainTab('practicas', this)">
        Prácticas / pasantías ({total_practicas})
      </button>
      <button class="tab-link" onclick="switchMainTab('canales', this)">
        Retos, Hackatones & Ecosistema ({total_retos})
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
        <h3>Retos, Hackatones y Competencias Abiertas</h3>
        <p>Rastreo automático diario de hackatones en línea (Devpost), competencias de datos e IA (Zindi, DrivenData) y retos de ciudad e innovación abierta en Colombia. Solo se muestran retos <strong>en línea</strong> o <strong>presenciales en Medellín / Antioquia</strong>. Verifica siempre requisitos, elegibilidad y fechas en la fuente oficial.</p>
        <div class="convenios-controls">
          <input type="text" id="retosSearch" class="search-bar" style="flex: 1 1 240px; margin: 0; padding: 10px 14px;" placeholder="Buscar reto o tema (ej. energía, movilidad, cuántica, IA, hardware)..." onkeyup="renderRetos()">
          <select id="retosTipoFilter" onchange="renderRetos()">
            <option value="ALL">Todos los tipos</option>
            <option value="Hackatón">Hackatones</option>
            <option value="Competencia de datos / IA">Competencias de datos / IA</option>
            <option value="Reto / convocatoria">Retos y convocatorias</option>
            <option value="Plataforma">Plataformas y programas recurrentes</option>
          </select>
        </div>
        <div id="retosCounter" style="font-family: var(--font-mono); font-size: 0.84rem; color: var(--accent-cyan); margin-bottom: 14px; font-weight: 600;"></div>
        <div id="retosGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; max-height: 760px; overflow-y: auto; padding-right: 6px;"></div>
      </article>

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
    <p class="schedule-note">Actualización automática diaria • Prácticas 19:30 • Retos 06:00 • Becas 07:00 • Convenios 07:30 (hora Colombia)</p>
    
    <div class="footer-meta-bar">
      <span>Portal Académico Independiente • Facultad de Ciencias & Facultad de Minas</span>
      <div class="footer-views-counter" id="totalViewsCounter" title="Visitas reales registradas en este portal" hidden>
        <span>Visitas registradas:</span>
        <strong id="totalViewsText">—</strong>
      </div>
    </div>
    <p class="legal-note"><strong>Aviso legal:</strong> {AVISO_LEGAL_CORTO}</p>
    <p class="signature-note">{pie_firma} · <a href="{REPOSITORIO}" target="_blank" rel="noopener noreferrer">Código fuente</a></p>
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
    const allRetos = {retos_json_str};
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
            <p class="beca-desc">${{escapeHtml(b.descripcion || '')}}</p>
          </div>
          <a href="${{sanitizeUrl(b.url)}}" target="_blank" rel="noopener noreferrer" class="apply-link" style="text-align: center; font-size: 0.82rem; padding: 9px 14px;">
            <span>Ver Convocatoria Oficial</span> <span>↗</span>
          </a>
        `;
        grid.appendChild(card);
      }});
    }}

    function renderRetos() {{
      const grid = document.getElementById('retosGrid');
      if (!grid) return;
      const q = (document.getElementById('retosSearch')?.value || '').toLowerCase();
      const tipo = document.getElementById('retosTipoFilter')?.value || 'ALL';
      const visibles = allRetos.filter(r => {{
        if (tipo !== 'ALL' && r.tipo !== tipo) return false;
        if (!q) return true;
        const texto = [r.titulo, r.organizador, r.descripcion, r.ubicacion, ...(r.temas || []), ...(r.areas_perfil || [])].join(' ').toLowerCase();
        return texto.includes(q);
      }});
      const counter = document.getElementById('retosCounter');
      if (counter) counter.textContent = `[ ${{visibles.length}} de ${{allRetos.length}} retos, hackatones y plataformas ]`;
      grid.innerHTML = '';
      visibles.forEach(r => {{
        const card = document.createElement('div');
        card.className = 'beca-card';
        const color = r.tipo === 'Plataforma' ? 'var(--accent-amber)' : (r.tipo === 'Hackatón' ? 'var(--accent-cyan)' : 'var(--accent-emerald)');
        let cierre = '';
        if (r.fecha_cierre_iso) {{
          const dias = Math.ceil((new Date(r.fecha_cierre_iso + 'T23:59:59') - new Date()) / 86400000);
          cierre = `<div class="beca-coverage"><strong>Cierre:</strong> ${{escapeHtml(new Date(r.fecha_cierre_iso + 'T00:00:00').toLocaleDateString('es-CO'))}}${{dias >= 0 && dias <= 7 ? ` · <strong style="color: var(--accent-amber);">quedan ${{dias}} días</strong>` : ''}}</div>`;
        }} else if (r.fechas) {{
          cierre = `<div class="beca-coverage"><strong>Fechas:</strong> ${{escapeHtml(r.fechas)}}</div>`;
        }}
        const areas = (r.areas_perfil || []).slice(0, 3).map(a => `<span class="beca-country-tag">${{escapeHtml(a)}}</span>`).join(' ');
        card.innerHTML = `
          <div>
            <div class="beca-header">
              <span class="beca-type-tag" style="background: ${{color}}22; color: ${{color}}; border: 1px solid ${{color}}44;">${{escapeHtml(r.tipo || 'Reto')}}</span>
              <span class="beca-country-tag">[ ${{escapeHtml((r.modalidad || '').toUpperCase())}} ]</span>
            </div>
            <h4 class="beca-title">${{escapeHtml(r.titulo)}}</h4>
            <div class="beca-entity">${{escapeHtml(r.organizador || r.plataforma || '')}} · ${{escapeHtml(r.ubicacion || '')}}</div>
            ${{cierre}}
            ${{r.premio ? `<div class="beca-coverage"><strong>Premio:</strong> ${{escapeHtml(r.premio)}}</div>` : ''}}
            ${{r.descripcion ? `<p class="beca-desc">${{escapeHtml(r.descripcion)}}</p>` : ''}}
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px;">${{areas}}</div>
          </div>
          <a href="${{sanitizeUrl(r.url)}}" target="_blank" rel="noopener noreferrer" class="apply-link" style="text-align: center; font-size: 0.82rem; padding: 9px 14px;">
            <span>${{r.tipo === 'Plataforma' ? 'Explorar plataforma' : 'Ver reto oficial'}}</span> <span>↗</span>
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
              <span>Vigencia: confirmar en la publicación original</span>
              ${{j.programa_inclusion_genero ? `<span>Programa STEM / inclusión de género · revisar requisitos de elegibilidad</span>` : ''}}
              ${{j.convocatoria_exclusiva_mujeres ? `<span>Convocatoria dirigida exclusivamente a mujeres según el aviso</span>` : ''}}
            </div>
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
        if (canalesBox) {{
          canalesBox.style.display = 'block';
          renderRetos();
        }}
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

    // Cerrar tooltip si se hace clic afuera
    document.addEventListener('click', () => {{
      document.querySelectorAll('.info-trigger.active').forEach(el => el.classList.remove('active'));
    }});

    setTheme(document.documentElement.dataset.theme || 'light');
    handleFilter();
  </script>
  <!-- Contador real de personas en línea y visitas (Firebase Realtime Database) -->
  <script type="application/json" id="ipfFirebaseConfig">{firebase_config_str}</script>
  <script type="module" src="presencia.js"></script>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    with open(OUTPUT_INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f" [✓] Archivos HTML generados: {OUTPUT_HTML} y {OUTPUT_INDEX}")


def main():
    print(encabezado_bot("[PÁGINA] BOT CONSTRUCTOR DE LA PÁGINA"))
    build_full_html(cargar_lista("vacantes"), cargar_lista("becas"), cargar_lista("convenios"), cargar_lista("retos"))


if __name__ == "__main__":
    main()
