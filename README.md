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
* **Identidad Visual de Laboratorio:** Tipografía técnica (`Syne`, `JetBrains Mono` y `Outfit`), paleta clara de papel, verde mineral y acentos de laboratorio. Las descripciones se despliegan al pasar el cursor por una convocatoria y también al navegar con teclado.
* **Cero Plantillas Genéricas:** Se eliminaron las estéticas predecibles de IA (degradados morados sobre blanco, fuentes del sistema sobreusadas y tarjetas flotantes genéricas).

---

## 🔒 Seguridad y Protección de Datos
* **Protección de Credenciales:** El archivo `.gitignore` bloquea cualquier intento de subir archivos `.env`, claves privadas (`.key`, `.pem`), tokens o secretos de API al repositorio público.
* **Manejo de Variables:** Las configuraciones sensibles se leen desde variables de entorno locales o secretos de GitHub Actions (`secrets.MY_KEY`), garantizando que ningún bot o tercero pueda extraer accesos privados.

---

## 🚀 Arquitectura y Automatización
* `bot_practicas.py`: Motor de rastreo y clasificación en Python. Combina LinkedIn con búsquedas web públicas de ofertas indexadas en portales de empleo y páginas de empresas. Consulta también nombres del directorio `empresas_antioquia.json`, además de focos mineros como Antioquia Gold.
* `empresas_antioquia.json`: Directorio de empresas y sectores para ampliar la búsqueda a empleadores locales.
* `estilos.css`: Sistema de diseño visual y responsivo.
* `index.html`: Dashboard interactivo con buscador en vivo y filtros por pestañas:
  * **💼 Todas las Vacantes**
  * **🎯 Exclusivas: Piden Físico / Ing. Físico**
  * **⏳ Próximas a Finalizar (< 5 Días)**
  * **📝 Guía & Tips para la Hoja de Vida**
* `.github/workflows/auto_update.yml`: Flujo de GitHub Actions que ejecuta el bot automáticamente todos los días en la nube y despliega los resultados a GitHub Pages sin requerir servidores de pago ni computadores encendidos.

### Cobertura de fuentes
La búsqueda web puede encontrar páginas públicas que los buscadores tengan indexadas, incluidos resultados de Magneto, Computrabajo/Pandapé, elempleo y sitios corporativos. No garantiza cubrir todo Internet: algunos portales requieren iniciar sesión, bloquean rastreadores o publican vacantes que aún no están indexadas. Las fechas y el estado de cada resultado se deben confirmar en la publicación original; los resúmenes web se distinguen de las misiones inferidas por área.
