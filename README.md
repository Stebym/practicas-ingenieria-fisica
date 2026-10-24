# ⚛️ Portal de Prácticas para Ingeniería Física — Medellín y Antioquia

**Autor:** Jimmy Stebym Rosero Barrera  
**Institución:** Universidad Nacional de Colombia (Sede Medellín)  
**Carrera:** Ingeniería Física  
**Búsqueda de vacantes:** inicia todos los días a las 19:30 (7:30 PM, hora Colombia); la página se actualiza al terminar el bot.

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

## 🚀 Arquitectura: cinco bots automáticos

Cuatro bots recolectan datos y un quinto arma la página. Todo corre solo en GitHub Actions.

| Bot | Qué hace | Salida | Horario (Colombia) |
|---|---|---|---|
| `bot_practicas.py` | Prácticas en LinkedIn, Magneto365, Computrabajo, ElEmpleo, FirstJob, portales corporativos y 200+ empresas objetivo | `vacantes_practicas.json` / `.csv` | 19:30 |
| `bot_retos.py` | Hackatones en línea (Devpost), competencias de datos e IA (Zindi, DrivenData), retos de ciudad e innovación abierta en Colombia y plataformas recurrentes (`retos_destacados.json`) | `retos_hackatones.json` | 06:00 |
| `bot_becas.py` | Becas vigentes del ICETEX y convocatorias internacionales (IAESTE, DAAD, CERN, Mitacs, CSC, ITEC, Erasmus) | `becas_internacionales.json` | 07:00 |
| `bot_convenios.py` | Convenios vigentes de la UNAL desde la hoja pública de la DRE (Google Drive / Sheets) | `convenios_internacionales.json` | 07:30 |
| `bot_pagina.py` | Junta los cuatro JSON, arma `index.html`, incrusta la firma y publica en GitHub Pages | `index.html` | Al terminar cualquiera de los anteriores |

Cada bot tiene su propio workflow (`auto_update.yml`, `retos_update.yml`, `becas_update.yml`, `convenios_update.yml`) y solo sube sus datos. `static.yml` ("Construir y publicar página") se dispara cuando cualquiera termina. Si un bot falla, los demás siguen y la página se arma con los últimos datos buenos.

En local: `./ejecutar_todo.sh` (o `ejecutar_todo.bat` en Windows) corre los cuatro bots y luego la página; `./ejecutar_todo.sh retos` corre solo uno.

Otros archivos:
* `firma.py` / `verificar_firma.py`: autoría, aviso legal y firma interna del proyecto (ver abajo).
* `presencia.js`, `firebase_config.json`, `database.rules.json`: contador real de personas en línea y visitas.
* `empresas_objetivo.json`, `empresas_antioquia.json`, `convocatorias_destacadas.json`, `config_ramas.json`: catálogos que usa el bot de prácticas.
* `portales_workday.json`: portales de empleo Workday de empresas (Rockwell, 3M, Medtronic, Hitachi…). Para agregar una empresa basta copiar de su portal `https://<tenant>.<servidor>.myworkdayjobs.com/<sitio>` esos tres datos.
* `estilos.css`, `estrellas.js`, `fondo_fisica*.svg`: diseño visual.

### Contador real de personas en línea (Firebase)
La página ya no muestra cifras inventadas: si Firebase no está configurado, el contador se oculta. Para activarlo (gratis, plan Spark):
1. Entra a <https://console.firebase.google.com>, crea un proyecto y agrega una **app web**.
2. En *Build → Realtime Database* crea la base de datos (ubicación `us-central1`, modo bloqueado).
3. En la pestaña *Reglas* pega el contenido de `database.rules.json` y publica.
4. Copia el objeto `firebaseConfig` de la app web (apiKey, authDomain, databaseURL, projectId, appId…) en `firebase_config.json` y súbelo. Estos datos son públicos por diseño; la seguridad la dan las reglas.

Cada pestaña abierta se registra en `/presencia` y Firebase la borra sola al cerrarse, así que el número es real; `/visitas` suma una por sesión.

### Firma y autoría
Además del aviso de copyright, el proyecto lleva una firma interna (`FIRMA_ID` en `firma.py`):
* marca de agua invisible (caracteres de ancho cero) en el pie de la página;
* metadatos `ipf-<firma>` en el HTML y la hoja de estilos;
* un `_sello` en cada registro de los JSON, derivado de la firma y del enlace de la oportunidad.

`python verificar_firma.py index.html vacantes_practicas.json` dice si un archivo salió de este proyecto.

### Aviso legal
Proyecto académico independiente. No somos agencia de empleo ni representamos a las empresas, universidades o plataformas citadas. La información proviene de fuentes públicas y puede cambiar o tener errores: verifica siempre en la fuente oficial. El autor no se hace responsable por decisiones, postulaciones, pérdidas o daños derivados del uso del portal, ni por el mal uso que terceros hagan del código o de los datos. Ver `LICENSE`.

### Alcance geográfico y de perfil
* **Antioquia:** se publican prácticas con cualquier modalidad (presencial, híbrida o remota).
* **Resto de Colombia:** solo si el aviso dice remoto o híbrido.
* **Exterior:** solo prácticas remotas (lo híbrido en otro país no sirve); hay que confirmar la elegibilidad desde Colombia.
* Solo prácticas (practicante, aprendiz, pasantía, intern, estudiante en práctica); los empleos regulares se descartan.
* Se descartan los avisos cuyo título pide solo carreras ajenas (administración, psicología, ingeniería industrial, ambiental, de alimentos, ventas, etc.) sin mencionar una carrera afín.
* Las vacantes que una noche no reaparecen se vuelven a verificar durante 21 días antes de retirarse.

### Cobertura de fuentes
Rastreo activo multi-plataforma:
1. **Magneto365 (API Pública Oficial)**: Rastreo dinámico en vivo de ofertas con compensación verificada (Corona Industrial, Haceb, Kalley, Crystal, ERCO Energía, Protección, Comfama).
2. **ElEmpleo.com**: Rastreo en tiempo real de pasantías de ingeniería, automatización, datos y mantenimiento.
3. **FirstJob Colombia**: Programas de prácticas y semilleros en multinacionales (Schneider Electric, Dialectica, Galderma, Alsea).
4. **Computrabajo Antioquia**: Búsqueda de Ingeniería Física y carreras espejo en áreas técnicas; las consultas espejo se enfocan en avisos que mencionan carreras afines.
5. **LinkedIn Jobs Guest API**: Búsqueda en Medellín y Antioquia, más consultas Worldwide para prácticas remotas. Los avisos internacionales quedan marcados para confirmar elegibilidad desde Colombia.
6. **Portales Corporativos y Estatales Directos**: EPM, Grupo Argos, Enel, ABB, Gobernación de Antioquia y Sievert Radiaciones.
7. **Ecosistema Complementario**: Accesos y guías directas para Interacpedia (retos empresariales), Estado Joven (MinTrabajo), Torre.ai y SENA SGVA.
