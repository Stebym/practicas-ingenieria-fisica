# ⚛️ Portal de Prácticas para Ingeniería Física — Medellín y Antioquia

**Autor:** Jimmy Stebym Rosero Barrera  
**Institución:** Universidad Nacional de Colombia (Sede Medellín)  
**Carrera:** Ingeniería Física  
**Actualización Automática:** Todos los días a las 20:00 horas (8:00 PM)

---

## 🎯 Propósito del Proyecto
Plataforma web automatizada diseñada para resolver la brecha entre la **Ingeniería Física** y las ofertas laborales de prácticas en Medellín y el Valle de Aburrá. 

Rastrea en tiempo real vacantes en empresas industriales, centros de I+D, hospitales y startups de Deep Tech, clasificándolas automáticamente en las 7 ramas formativas de la carrera:
1. ⚡ **Energía, Potencia y Renovables** (Sistemas fotovoltaicos, BESS, subestaciones, transformadores).
2. 🎛️ **Automatización, Instrumentación y Control** (PLC, sensores, SCADA, metrología, adquisición de datos).
3. 🔬 **Materiales, Nanotecnología y Ensayos** (Caracterización, difracción de rayos X, microscopía, polímeros).
4. 👁️ **Óptica, Fotónica y Visión Artificial** (Láser, fibra óptica, procesamiento digital de imágenes).
5. 📊 **Simulación, Datos, IA y Cuántica** (Modelado numérico, algoritmos, analítica avanzada, computación cuántica).
6. 🏥 **Física Médica y Bioingeniería** (Radioterapia, dosimetría, resonancia magnética, medicina nuclear).
7. 💡 **I+D, Innovación y Deep Tech** (Centros de investigación, prototipado y transferencia tecnológica).

---

## 🎨 Principios de Diseño Frontend (Anti "AI Slop")
Este proyecto fue construido aplicando estándares profesionales de **Desarrollo Web**:
* **HTML5 100% Semántico:** Uso riguroso de `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<time>` y `<footer>` para máxima extractabilidad, accesibilidad y compatibilidad con rastreadores de IA.
* **Separación de Responsabilidades:** Hoja de estilos externa e independiente (`estilos.css`) vinculada mediante `<link rel="stylesheet">`.
* **Identidad Visual de Laboratorio:** Tipografía técnica (`Syne`, `JetBrains Mono` y `Outfit`), paleta clara de papel, verde mineral y acentos de laboratorio. El fondo integra ecuaciones de cuántica y estado sólido con planetas y estrellas vectoriales. Las descripciones se despliegan al pasar el cursor por una convocatoria y también al navegar con teclado.
* **Cero Plantillas Genéricas:** Se eliminaron las estéticas predecibles de IA (degradados morados sobre blanco, fuentes del sistema sobreusadas y tarjetas flotantes genéricas).

---

## 🔒 Seguridad y Protección de Datos
* **Protección de Credenciales:** El archivo `.gitignore` bloquea cualquier intento de subir archivos `.env`, claves privadas (`.key`, `.pem`), tokens o secretos de API al repositorio público.
* **Manejo de Variables:** Las configuraciones sensibles se leen desde variables de entorno locales o secretos de GitHub Actions (`secrets.MY_KEY`), garantizando que ningún bot o tercero pueda extraer accesos privados.

---

## 🚀 Arquitectura y Automatización
* `bot_practicas.py`: Motor de rastreo y clasificación en Python. Integra rastreo multi-fuente en vivo (Computrabajo y LinkedIn Jobs), el catálogo verificado de convocatorias destacadas (`convocatorias_destacadas.json` con Magneto365, Jooble y portales oficiales de Antioquia) y el directorio de empleadores clave (`empresas_antioquia.json`).
* `convocatorias_destacadas.json`: Catálogo de convocatorias de alto impacto para Ingeniería Física y carreras afines (Corona, Argos, Haceb, ISA, EPM, Enel, ERCO, Sievert, Gobernación de Antioquia, AKT, Protección, etc.).
* `empresas_antioquia.json`: Directorio de empresas y sectores para ampliar la búsqueda a empleadores locales.
* `estilos.css`: Sistema de diseño visual y responsivo.
* `fondo_fisica.svg` y `fondo_fisica_movil.svg`: Fondos vectoriales adaptados a escritorio y móvil con planetas, estrellas y ecuaciones.
* `index.html`: Dashboard interactivo con buscador en vivo y filtros por pestañas:
  * **💼 Todas las Vacantes**
  * **🎯 Exclusivas: Piden Físico / Ing. Físico**
  * **⏳ Próximas a Finalizar (< 5 Días)**
  * **🚀 Ecosistema & Canales Estratégicos (Interacpedia, Estado Joven, Torre.ai, SENA SGVA)**
  * **📝 Guía & Tips para la Hoja de Vida**
* `.github/workflows/auto_update.yml`: Flujo de GitHub Actions que ejecuta el bot diariamente a las 20:00 (hora Colombia), actualiza los datos y comitea al repositorio.
* `.github/workflows/static.yml`: Despliega automáticamente `index.html`, `estilos.css`, `estrellas.js`, `fondo_fisica.svg`, `fondo_fisica_movil.svg`, `vacantes_practicas.json` y `vacantes_practicas.csv` a GitHub Pages cada vez que se actualiza `main` o al concluir el bot diario.

### Cobertura de fuentes
Rastreo activo multi-plataforma:
1. **Magneto365 (API Pública Oficial)**: Rastreo dinámico en vivo de ofertas con compensación verificada (Corona Industrial, Haceb, Kalley, Crystal, ERCO Energía, Protección, Comfama).
2. **ElEmpleo.com**: Rastreo en tiempo real de pasantías de ingeniería, automatización, datos y mantenimiento.
3. **FirstJob Colombia**: Programas de prácticas y semilleros en multinacionales (Schneider Electric, Dialectica, Galderma, Alsea).
4. **Computrabajo Antioquia**: Barrido dinámico de convocatorias técnicas, electromecánicas, instrumentación y metrología.
5. **LinkedIn Jobs Guest API**: Búsqueda en tiempo real de vacantes y pasantías para las 35 áreas del pénsum UNAL y 35 empresas líderes de Medellín y Antioquia.
6. **Portales Corporativos y Estatales Directos**: EPM, Grupo Argos, Enel, ABB, Gobernación de Antioquia y Sievert Radiaciones.
7. **Ecosistema Complementario**: Accesos y guías directas para Interacpedia (retos empresariales), Estado Joven (MinTrabajo), Torre.ai y SENA SGVA.
