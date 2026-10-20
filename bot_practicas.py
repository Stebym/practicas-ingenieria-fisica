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
from datetime import datetime
from urllib.parse import quote
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
OUTPUT_HTML = os.path.join(BASE_DIR, "dashboard_practicas.html")
OUTPUT_INDEX = os.path.join(BASE_DIR, "index.html")
OUTPUT_CSV = os.path.join(BASE_DIR, "vacantes_practicas.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "vacantes_practicas.json")

SEARCH_QUERIES = [
    "practicante ingenieria",
    "practicante datos",
    "practicante ia",
    "practicante python",
    "practicante analitica",
    "practicante iot",
    "practicante electronica digital",
    "practicante embebidos",
    "practicante electronica analoga",
    "practicante circuitos",
    "practicante instrumentacion",
    "practicante metrologia",
    "practicante diseno mecanico",
    "practicante cad solidworks",
    "practicante cuantica",
    "practicante radiaciones",
    "practicante fisica medica",
    "practicante optica",
    "practicante vision artificial",
    "practicante materiales",
    "practicante nanotecnologia",
    "practicante energia solar",
    "practicante potencia transformadores",
    "practicante fisico",
    "practicante investigacion i+d",
    "practicante mujeres stem",
    "intern engineering medellin"
]

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

def classify_and_score_job(job, config_ramas):
    """Calcula el Score de Afinididad con el Pénsum UNAL con priorización interna discreta"""
    text_to_analyze = f"{job['titulo']} {job.get('empresa', '')}".lower()
    
    # Detección interna para priorizar sin exhibirlo en público
    es_impulso_liderazgo = False
    terminos_mujeres = ["mujer", "mujeres", "women", "women in tech", "femenin", "stem"]
    if any(t in text_to_analyze for t in terminos_mujeres):
        es_impulso_liderazgo = True

    es_exclusiva_fisica = False
    terminos_fisica = ["físic", "fisic", "metrolog", "cuantic", "cuántic", "espectroscop", "difracci", "radiaci", "dosimetr", "nanotecn"]
    if any(t in text_to_analyze for t in terminos_fisica):
        es_exclusiva_fisica = True

    es_cierre_inminente = False
    pub_lower = job.get("fecha_publicacion", "").lower()
    if any(k in pub_lower for k in ["hora", "horas", "1 día", "2 días", "3 días", "4 días", "5 días", "hace 1", "hace 2"]):
        es_cierre_inminente = True
    elif "urgente" in text_to_analyze or "pipeline" in text_to_analyze:
        es_cierre_inminente = True

    # Ponderación interna: programas especiales quedan en los primeros puestos
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
            continue # Mantener oculto del listado público de ramas
            
        score = 0
        palabras = data.get("palabras_clave", [])
        for p in palabras:
            if p in text_to_analyze:
                score += 3
        
        empresas_ref = [e.lower() for e in data.get("empresas_referencia", [])]
        for e in empresas_ref:
            if e in text_to_analyze:
                score += 4

        bonus = data.get("prioridad_bonus", 20)
        if score > 0:
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

    job["ramas"] = ramas_coincidentes
    job["rama_principal"] = ramas_coincidentes[0]["nombre"]
    job["color_principal"] = ramas_coincidentes[0]["color"]
    job["clave_principal"] = ramas_coincidentes[0]["clave"]
    job["afinidad"] = afinidad
    job["es_exclusiva_fisica"] = es_exclusiva_fisica
    job["es_cierre_inminente"] = es_cierre_inminente
    job["score_pensum"] = total_score
    job["mision"] = mision_especifica if mision_especifica else f"Desarrollo de proyectos técnicos y operativos en {job.get('empresa', 'la empresa')}."
    job["tareas"] = tareas_especificas if tareas_especificas else "Apoyo en mediciones, modelado técnico, análisis de datos y reporte de resultados."

    return job

def build_full_html(vacantes, config_ramas):
    """Genera el HTML semántico con diseño de laboratorio, ícono [i] flotante y sin menciones públicas de género"""
    vacantes_json_str = json.dumps(vacantes, ensure_ascii=False)
    total_exclusivas = sum(1 for v in vacantes if v.get("es_exclusiva_fisica"))
    total_inminentes = sum(1 for v in vacantes if v.get("es_cierre_inminente"))

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prácticas de Ingeniería Física • UNAL Medellín | Jimmy Rosero</title>
  <meta name="description" content="Portal de convocatorias prioritarias para estudiantes de Ingeniería Física de la Universidad Nacional de Colombia Sede Medellín. Creado por Jimmy Stebym Rosero Barrera.">
  <meta name="author" content="Jimmy Stebym Rosero Barrera">
  <link rel="stylesheet" href="estilos.css">
</head>
<body>

  <!-- HEADER SEMÁNTICO -->
  <header class="site-header">
    <div class="header-container">
      <div class="branding">
        <div class="brand-symbol">⚛</div>
        <div class="brand-text">
          <h1>Prácticas de Ingeniería Física</h1>
          <p class="subtitle">Medellín y Antioquia • Convocatorias & Directorio de I+D</p>
          <div class="creator-tag">
            Creado por <strong>Jimmy Stebym Rosero Barrera</strong>
          </div>
        </div>
      </div>
      <div class="header-meta">
        <div>Vacantes activas: <strong style="color: var(--accent-cyan);">{len(vacantes)}</strong></div>
        <div>•</div>
        <div>Exclusivas Física: <strong style="color: var(--accent-amber);">{total_exclusivas}</strong></div>
        <div>•</div>
        <div>Próximas a cerrar: <strong style="color: var(--accent-crimson);">{total_inminentes}</strong></div>
      </div>
    </div>
  </header>

  <main class="main-content">

    <section class="manifesto-box">
      <h2>Ecosistema de Prácticas para Ingenieros Físicos (UNAL Medellín)</h2>
      <p>
        Plataforma automatizada diseñada por <strong>Jimmy Stebym Rosero Barrera</strong>. El algoritmo prioriza en los primeros lugares las convocatorias de mayor rigor alineadas con las materias clave de nuestra carrera: <strong>Análisis de Datos & IA, Electrónica Digital (Taller V / Microcontroladores / I2C / IoT), Electrónica Análoga (Taller IV), Física de Radiaciones, Mecánica Cuántica, Diseño Mecánico (Taller II), Dibujo Técnico (Taller I), Instrumentación Virtual y Metrología</strong>.
      </p>
    </section>

    <!-- NAVEGACIÓN POR PESTAÑAS (SIN EMOJIS) -->
    <nav class="tabs-nav" aria-label="Secciones de prácticas">
      <button class="tab-link active" onclick="switchMainTab('todas', this)">
        Todas las Vacantes ({len(vacantes)})
      </button>
      <button class="tab-link exclusive" onclick="switchMainTab('exclusivas', this)">
        Exclusivas: Piden Físico / Ing. Físico ({total_exclusivas})
      </button>
      <button class="tab-link urgent" onclick="switchMainTab('inminentes', this)">
        Próximas a Finalizar (&lt; 5 Días) ({total_inminentes})
      </button>
      <button class="tab-link" onclick="switchMainTab('consejos', this)">
        Guía & Tips de Hoja de Vida
      </button>
    </nav>

    <!-- CONTENEDOR DE FILTROS Y BÚSQUEDA -->
    <div id="filterControls">
      <input type="text" id="searchInput" class="search-bar" placeholder="Buscar por materia, software o tecnología (ej. I2C, Python, Taller V, CAD, PLC, Cuántica, Radiaciones)..." onkeyup="handleFilter()">
      
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
      <!-- Inyectado dinámicamente con etiquetas article -->
    </section>

    <!-- PESTAÑA: GUÍA Y TIPS -->
    <section id="guideContainer" style="display: none;">
      <article class="editorial-card">
        <h3>Cómo defender el perfil de Ingeniería Física ante Recursos Humanos</h3>
        <p>A menudo el reclutador de RRHH no conoce a fondo el pénsum de Ingeniería Física. Si dices solo <em>"Soy estudiante de Física"</em>, asumirán que solo haces teoría en tablero. Tu perfil debe destacar como <strong>Ingeniero Físico orientado a soluciones prácticas de alta tecnología</strong>:</p>
        <ul>
          <li><strong>Destaca tus habilidades duras en el encabezado del CV:</strong> Instrumentación industrial, adquisición de datos (DAQ), buses de comunicación (I2C/SPI), microcontroladores, automatización, modelado numérico (Python/MATLAB), caracterización de materiales (DRX/SEM) o análisis de datos.</li>
          <li><strong>Si la oferta dice "Ing. Electrónico, Mecatrónico, Materiales o afines":</strong> Postúlate sin dudar. En tu carta o resumen escribe: <em>"Estudiante de Ingeniería Física con énfasis en sistemas de potencia / automatización / electrónica digital / análisis de datos..."</em></li>
          <li><strong>Menciona tus proyectos de taller de la UNAL:</strong> Taller I (Dibujo técnico CAD), Taller II (Diseño mecánico), Taller III (Circuitos electromagnéticos), Taller IV (Electrónica análoga) y Taller V (Electrónica digital y microcontroladores).</li>
        </ul>
        <h4 style="color: #fff; margin-bottom: 8px; font-family: var(--font-display);">Calendario de Convocatorias Masivas en Medellín:</h4>
        <p>• <strong>Semestre 1 (Prácticas enero a junio):</strong> Convocatorias abren entre <strong>septiembre y noviembre</strong>.<br>
        • <strong>Semestre 2 (Prácticas julio a diciembre):</strong> Convocatorias abren entre <strong>marzo y mayo</strong>.</p>
      </article>
    </section>

  </main>

  <!-- FOOTER SEMÁNTICO -->
  <footer class="site-footer">
    <p class="institution">Herramienta desarrollada para estudiantes de Ingeniería Física • UNAL Medellín, Colombia</p>
    <p class="schedule-note">Para actualizar las vacantes en cualquier momento, este se actualiza solo a las 20:00 pm</p>
  </footer>

  <script>
    const allJobs = {vacantes_json_str};
    let currentTab = 'todas';
    let currentBranch = 'TODOS';

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
        
        const tagsHtml = j.ramas.map(r => `<span class="job-tag" style="border-left: 2px solid ${{r.color}}">${{r.nombre}}</span>`).join('');
        
        let badgeColor = j.color_principal;
        let badgeText = j.afinidad.toUpperCase();
        if (j.es_cierre_inminente) {{
          badgeText = 'CIERRE INMINENTE (< 5 DIAS)';
          badgeColor = '#ef476f';
        }} else if (j.es_exclusiva_fisica) {{
          badgeText = 'EXCLUSIVA FISICA';
          badgeColor = '#ffb703';
        }}
        
        card.innerHTML = `
          <div>
            <header class="job-card-header">
              <span class="affinity-badge" style="background: ${{badgeColor}}22; color: ${{badgeColor}}; border: 1px solid ${{badgeColor}}55;">
                ${{badgeText}}
              </span>
              <div class="header-right">
                <time class="job-date">${{j.fecha_publicacion}}</time>
                <div class="info-trigger" tabindex="0">
                  <span class="info-icon" title="Pasa el mouse para ver misiones">i</span>
                  <div class="floating-cloud">
                    <div class="cloud-title">Misión & Contexto</div>
                    <div class="cloud-body">${{j.mision}}</div>
                    <div class="cloud-tasks-section">
                      <strong>¿Qué te tocará hacer?</strong>
                      <p>${{j.tareas}}</p>
                    </div>
                  </div>
                </div>
              </div>
            </header>
            <h3 class="job-title">${{j.titulo}}</h3>
            <div class="job-company">${{j.empresa}}</div>
            <div class="job-specs">
              <span>Ubicación: ${{j.ubicacion}}</span>
              <span>Portal: ${{j.fuente}}</span>
            </div>
            <div class="job-tags">${{tagsHtml}}</div>
          </div>
          <footer class="job-card-footer">
            <a href="${{j.url}}" target="_blank" class="apply-link" rel="noopener noreferrer">Postularme a la Oferta</a>
          </footer>
        `;
        container.appendChild(card);
      }});
    }}

    function handleFilter() {{
      const query = document.getElementById('searchInput').value.toLowerCase();
      
      const filtered = allJobs.filter(j => {{
        if (currentTab === 'exclusivas' && !j.es_exclusiva_fisica) return false;
        if (currentTab === 'inminentes' && !j.es_cierre_inminente) return false;
        
        const matchesBranch = (currentBranch === 'TODOS') || j.ramas.some(r => r.nombre === currentBranch);
        if (!matchesBranch) return false;
        
        const matchesText = j.titulo.toLowerCase().includes(query) ||
                            j.empresa.toLowerCase().includes(query) ||
                            j.ubicacion.toLowerCase().includes(query) ||
                            j.mision.toLowerCase().includes(query) ||
                            j.tareas.toLowerCase().includes(query) ||
                            j.ramas.some(r => r.nombre.toLowerCase().includes(query));
        return matchesText;
      }});
      
      renderJobs(filtered);
    }}

    function handlePill(branchName, btn) {{
      currentBranch = branchName;
      document.querySelectorAll('.branch-pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      handleFilter();
    }}

    function switchMainTab(tabId, btn) {{
      document.querySelectorAll('.tab-link').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      currentTab = tabId;
      const filterBox = document.getElementById('filterControls');
      const jobsBox = document.getElementById('jobsContainer');
      const guideBox = document.getElementById('guideContainer');
      
      if (tabId === 'consejos') {{
        filterBox.style.display = 'none';
        jobsBox.style.display = 'none';
        guideBox.style.display = 'block';
      }} else {{
        filterBox.style.display = 'block';
        jobsBox.style.display = 'grid';
        guideBox.style.display = 'none';
        handleFilter();
      }}
    }}

    renderJobs(allJobs);
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
    fieldnames = ["titulo", "empresa", "ubicacion", "rama_principal", "afinidad", "score_pensum", "es_exclusiva_fisica", "es_cierre_inminente", "mision", "tareas", "fecha_publicacion", "fuente", "url"]
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
    
    print(f"[*] Rastreando en vivo {len(SEARCH_QUERIES)} categorías del pénsum UNAL...")
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
        time.sleep(0.8)
        
    print(f"\n[*] Total de vacantes únicas recolectadas: {len(all_raw_jobs)}")
    print("[*] Clasificando y ordenando por afinidad al pénsum UNAL...")
    
    classified_jobs = []
    for j in all_raw_jobs:
        classified_jobs.append(classify_and_score_job(j, config_ramas))
        
    # Ordenar por Score de Afinidad del Pénsum
    classified_jobs.sort(key=lambda x: x.get("score_pensum", 0), reverse=True)
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(classified_jobs, f, ensure_ascii=False, indent=2)
    print(f" [✓] Datos JSON guardados en: {OUTPUT_JSON}")
    
    export_csv(classified_jobs)
    build_full_html(classified_jobs, config_ramas)
    
    print("\n" + "="*70)
    print(" ¡RASTREO Y ACTUALIZACIÓN COMPLETADOS EXITOSAMENTE!")
    print(f" Dashboard listo para abrir:")
    print(f" file:///{OUTPUT_INDEX.replace('\\', '/')}")
    print("="*70)

if __name__ == "__main__":
    main()
