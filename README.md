# ⚛️ Portal de Prácticas para Ingeniería Física — Colombia y remoto internacional

**Autor:** Jimmy Stebym Rosero Barrera  
**Institución:** Universidad Nacional de Colombia (Sede Medellín)  
**Carrera:** Ingeniería Física  
**Rastreo de vacantes:** inicia todos los días a las 19:30 (7:30 PM, hora Colombia); GitHub Pages publica al terminar el bot, con objetivo de quedar actualizado antes de las 20:00.

---

## 🎯 Propósito del Proyecto
Plataforma web automatizada diseñada para conectar estudiantes de **Ingeniería Física** con prácticas en Antioquia, el resto de Colombia y oportunidades remotas internacionales.

Consulta fuentes de empleo y clasifica convocatorias de práctica para todo Colombia, Antioquia y roles remotos internacionales. El clasificador cruza las carreras espejo con competencias del pénsum: marca alta afinidad cuando encuentra una carrera afín y al menos dos competencias técnicas; reserva “Física explícita” para convocatorias que nombran Física como carrera o perfil. Las áreas técnicas (metrología, radiaciones, óptica, materiales, etc.) cuentan como competencias, no como mención de la carrera. Los anuncios internacionales que solo muestran “Remote” se incluyen como pistas y se etiquetan con elegibilidad desde Colombia por confirmar.

La cobertura se organiza en estas áreas formativas:
1. ⚡ **Energía, Potencia y Renovables** (Sistemas fotovoltaicos, BESS, subestaciones, transformadores).
2. 🎛️ **Automatización, Instrumentación y Control** (PLC, sensores, SCADA, metrología, adquisición de datos).
3. 🔬 **Materiales, Nanotecnología y Ensayos** (Caracterización, difracción de rayos X, microscopía, polímeros).
4. 👁️ **Óptica, Fotónica y Visión Artificial** (Láser, fibra óptica, procesamiento digital de imágenes).
5. 📊 **Simulación, Datos, IA y Cuántica** (Modelado numérico, algoritmos, analítica avanzada, computación cuántica).
6. 🏥 **Física Médica y Bioingeniería** (Radioterapia, dosimetría, resonancia magnética, medicina nuclear).
7. 💡 **I+D, Innovación y Procesos Industriales** (Centros de investigación, prototipado y transferencia tecnológica).

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
* `bot_practicas.py`: Motor de rastreo y clasificación de prácticas y empleo industrial en Python. Busca en Antioquia, todo Colombia y LinkedIn Worldwide para posiciones remotas en áreas espejo (Computrabajo, LinkedIn, Magneto365, ElEmpleo, FirstJob).
* `bot_becas_internacionales.py`: Bot de rastreo matutino para oportunidades globales y sincronización del catálogo oficial de convenios UNAL DRE (Google Sheets, ICETEX, IAESTE, DAAD, CERN, Mitacs).
* `convenios_internacionales.json`: Base de datos de más de 1.150 convenios oficiales vigentes suscritos por la UNAL para ingeniería y ciencias en 63 países con enlaces a los documentos oficiales en Google Drive.
* `becas_internacionales.json`: Convocatorias internacionales de becas completas y pasantías técnicas remuneradas.
* `convocatorias_destacadas.json`: Referencias de empleadores y convocatorias; el bot no las agrega como vigentes por sí solas. Una vacante entra al portal cuando aparece en una búsqueda ejecutada. El tablero separa enlaces accesibles de publicaciones recientes de LinkedIn cuya vigencia el servidor no puede confirmar.
* `empresas_antioquia.json`: Directorio de empresas y sectores para ampliar la búsqueda a empleadores locales.
* `estilos.css`: Sistema de diseño visual y responsivo (laboratorio técnico / blueprint).
* `fondo_fisica.svg` y `fondo_fisica_movil.svg`: Fondos vectoriales adaptados a escritorio y móvil con planetas, estrellas y ecuaciones.
* `index.html`: Dashboard interactivo con buscador en vivo y filtros por pestañas:
  * **💼 Todas las Vacantes**
  * **🎯 Exclusivas: Piden Físico / Ing. Físico**
  * **⏳ Próximas a Finalizar (< 5 Días)**
  * **🚀 Ecosistema Nacional & Retos (Interacpedia, Estado Joven, Torre.ai, SENA SGVA)**
  * **🌍 Becas & Pasantías Internacionales (ICETEX, IAESTE, DAAD, CERN, Mitacs y Convenios UNAL)**
* `.github/workflows/auto_update.yml`: Flujo nocturno que inicia el rastreo de vacantes a las 19:30 (hora Colombia), espera a que el bot termine y luego dispara el despliegue de Pages.
* `.github/workflows/becas_update.yml`: Flujo matutino que rastrea becas y convenios internacionales a las 07:00 AM (hora Colombia).
* `.github/workflows/static.yml`: Despliega automáticamente `index.html`, `estilos.css`, `estrellas.js`, `fondo_fisica.svg`, `fondo_fisica_movil.svg`, `vacantes_practicas.json`, `convenios_internacionales.json` y `becas_internacionales.json` a GitHub Pages cada vez que se actualiza `main` o al concluir cualquiera de los bots diarios.

### Cobertura de fuentes
Rastreo activo multi-plataforma:
1. **Magneto365 (API Pública Oficial)**: Rastreo dinámico en vivo de ofertas con compensación verificada (Corona Industrial, Haceb, Kalley, Crystal, ERCO Energía, Protección, Comfama).
2. **ElEmpleo.com**: Rastreo en tiempo real de pasantías de ingeniería, automatización, datos y mantenimiento.
3. **FirstJob Colombia**: Programas de prácticas y semilleros en multinacionales (Schneider Electric, Dialectica, Galderma, Alsea).
4. **Computrabajo**: Barrido en Antioquia y en el país completo con consultas técnicas, electromecánicas, de datos, instrumentación y metrología.
5. **LinkedIn Jobs Guest API**: Búsqueda por áreas del pénsum y carreras espejo en Antioquia, Colombia y Worldwide (prácticas remotas). Las ofertas remotas genéricas quedan marcadas con elegibilidad geográfica pendiente. LinkedIn limita las comprobaciones automatizadas; estas publicaciones se etiquetan como recientes, con vigencia pendiente de confirmar en el portal de origen.
6. **ElEmpleo, Magneto365 y FirstJob**: búsquedas nacionales; Magneto365 y FirstJob usan ámbito Colombia y ElEmpleo consulta resultados nacionales.
7. **Búsquedas por empleador**: consultas de LinkedIn para empresas del directorio regional y empleadores nacionales priorizados; no se presentan como rastreo directo de los portales corporativos.
8. **Ecosistema Complementario**: Accesos y guías directas para Interacpedia (retos empresariales), Estado Joven (MinTrabajo), Torre.ai y SENA SGVA.
