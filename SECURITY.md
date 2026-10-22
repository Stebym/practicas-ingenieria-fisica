# Política de Seguridad y Arquitectura de Protección de Datos

**Proyecto:** Portal de Prácticas y Becas — Ingeniería Física UNAL Sede Medellín  
**Autor:** Jimmy Stebym Rosero Barrera  
**Fecha de Auditoría:** Octubre 2026  
**Estado:** Verificado y Blindado (0 vulnerabilidades críticas, 0 credenciales expuestas)

---

## 1. Arquitectura de Cero Credenciales (Zero-Key Architecture)

Este repositorio opera bajo una arquitectura de **Cero Credenciales**:
* **Sin claves de API privadas en el código:** Los módulos de rastreo (`bot_practicas.py` y `bot_becas_internacionales.py`) consultan únicamente puntos de enlace públicos de acceso libre (API pública de búsqueda de Magneto365, catálogo público de la DRE de la Universidad Nacional, convocatorias abiertas del ICETEX e indexadores de empleo).
* **Sin bases de datos con contraseñas:** La información se procesa y consolida en archivos estáticos (`vacantes_practicas.json`, `convenios_internacionales.json`, `becas_internacionales.json`), eliminando riesgos de inyección SQL (SQLi) o robo de contraseñas de bases de datos.
* **Sin credenciales financieras ni cuentas de pago:** No existe ningún servicio de pago, cuenta de facturación ni tarjeta asociada a las consultas del bot.

---

## 2. Seguridad en Automatización (GitHub Actions)

Los flujos de trabajo de GitHub Actions (`auto_update.yml`, `becas_update.yml`, `static.yml`) implementan el principio de **mínimo privilegio**:
* **Permisos Restringidos:** Cada workflow delimita estrictamente sus permisos:
  * `permissions: contents: write` (únicamente para permitir que el bot de GitHub Actions confirme los JSON actualizados de vacantes).
  * `permissions: pages: write, id-token: write` (únicamente para la publicación en GitHub Pages).
* **Token Efímero:** Se utiliza exclusivamente el `GITHUB_TOKEN` interno provisto por GitHub en cada ejecución aislada, el cual caduca automáticamente al finalizar el contenedor y no tiene permisos fuera de este repositorio.
* **Sin Inyección de Código de Terceros:** Los flujos solo se activan mediante cronómetro programado (`schedule`) o manualmente por el propietario (`workflow_dispatch`), impidiendo ataques de tipo *Pwn Request* o ejecución de código arbitrario mediante Pull Requests no verificados.

---

## 3. Seguridad Web y Sanitización en el Navegador

El portal estático implementa defensas contra ataques web comunes:
* **Prevención de Cross-Site Scripting (XSS):** Todas las cadenas de texto provenientes de las vacantes y convenios externos se procesan mediante funciones de sanitización (`escapeHtml`) antes de renderizarse en el DOM, neutralizando posibles inyecciones de código malicioso.
* **Validación de Protocolos de Enlaces:** Las URLs de postulación y convenios son verificadas mediante `sanitizeUrl` para garantizar que únicamente utilicen protocolos seguros (`https://` y `http://`), bloqueando esquemas como `javascript:` o `data:`.
* **Protección contra Tabnabbing Reverso:** Todos los enlaces salientes incluyen `target="_blank"` acompañado de `rel="noopener noreferrer"`.
* **Cabeceras de Seguridad:** El encabezado HTML incluye:
  * `Referrer-Policy: strict-origin-when-cross-origin` (protege la privacidad del usuario al navegar).
  * `X-Content-Type-Options: nosniff` (previene ataques de confusión de tipos MIME).

---

## 4. Auditoría de Secretos y Bloqueo en `.gitignore`

El archivo `.gitignore` previene que archivos locales sensibles sean subidos accidentalmente:
* Archivos de variables de entorno: `.env`, `.env.*`, `*.env`.
* Llaves privadas y certificados: `*.key`, `*.pem`, `*.cert`, `*.token`, `*.pfx`, `*.p12`, `id_rsa*`.
* Archivos de credenciales: `credentials.json`, `config.private.json`.

---

## 5. Reporte de Vulnerabilidades

Si descubres una posible vulnerabilidad o vector de mejora de seguridad, por favor infórmalo de manera responsable abriendo un *Issue* en GitHub o comunicándote directamente a través del correo institucional del creador: **jiroserob@unal.edu.co**.
