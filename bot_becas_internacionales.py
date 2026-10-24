#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BOT DE RASTREO: BECAS, PASANTÍAS Y CONVENIOS INTERNACIONALES (UNAL)
Autor: Jimmy Stebym Rosero Barrera
Universidad Nacional de Colombia - Sede Medellín
Ingeniería Física
=============================================================================
Rastrea y actualiza:
1. Convenios internacionales vigentes de la UNAL (Dirección de Relaciones Exteriores - DRE).
2. Convocatorias globales activas (ICETEX, IAESTE, DAAD, CERN, Mitacs, CSC China, ITEC India).
"""

import os
import io
import re
import csv
import json
import time
import requests
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONVENIOS_JSON_PATH = os.path.join(BASE_DIR, "convenios_internacionales.json")
BECAS_JSON_PATH = os.path.join(BASE_DIR, "becas_internacionales.json")

# Hoja oficial de Convenios UNAL DRE (Google Sheets público)
SHEET_ID = "1X0ZaWn8uxyFy9w_lf3lzHjdvmL6L3IYGbjMnR6D51As"
GID = "1315141815"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_unal_convenios():
    """Descarga y filtra convenios vigentes para STEM y movilidad internacional de la UNAL."""
    print("[*] Descargando catálogo de convenios UNAL DRE desde Google Sheets...")
    try:
        r = requests.get(SHEET_CSV_URL, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            print(f" [!] Error al descargar sheet: HTTP {r.status_code}")
            return []
        
        reader = csv.reader(io.StringIO(r.text))
        rows = list(reader)
        print(f" [✓] {len(rows)} filas descargadas. Procesando y filtrando áreas STEM...")

        afines = []
        # La tabla oficial de datos comienza en la fila 26 (índice 25 son encabezados)
        for row in rows[26:]:
            if len(row) < 8:
                continue
            ano, pais, inst, nombre, tipo, estado, link, area = row[:8]
            if estado.strip().upper() != "VIGENTE":
                continue
            
            area_u = area.upper()
            is_stem = any(k in area_u for k in [
                "INGENIERÍA", "INGENIERIA", "MATEMATICA", "CIENCIAS", "EXACTAS",
                "TODAS LAS ÁREAS", "INTERDISCIPLINAR", "TECNOLOGÍA", "TECNOLOGIA"
            ])
            if not is_stem:
                continue
            
            is_intl = pais.strip().upper() != "COLOMBIA"
            is_practica = any(k in tipo.upper() for k in [
                "PRÁCTICA", "PRACTICA", "PASANTÍA", "PASANTIA", "INTERCAMBIO",
                "MOVILIDAD", "INVESTIGACIÓN", "INVESTIGACION", "DOBLE TITULACIÓN", "ERASMUS"
            ])
            
            if is_practica or is_intl:
                clean_pais = pais.strip().title()
                clean_inst = re.sub(r"\s+", " ", inst.strip().title())
                clean_tipo = re.sub(r"\s+", " ", tipo.strip().title())
                clean_nombre = re.sub(r"\s+", " ", nombre.strip())
                clean_area = re.sub(r"\s+", " ", area.strip().title())
                
                afines.append({
                    "ano": ano.strip(),
                    "pais": clean_pais,
                    "institucion": clean_inst,
                    "nombre": clean_nombre,
                    "tipo": clean_tipo,
                    "link": link.strip(),
                    "area": clean_area
                })
        
        print(f" [✓] {len(afines)} convenios vigentes STEM/Internacionales identificados.")
        with open(CONVENIOS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(afines, f, ensure_ascii=False, indent=2)
        print(f" [✓] Guardado en: {CONVENIOS_JSON_PATH}")
        return afines
    except Exception as e:
        print(f" [!] Excepción descargando convenios: {e}")
        return []

def scrape_icetex_becas():
    """Rastrea convocatorias vigentes de becas en el portal oficial del ICETEX."""
    url = "https://web.icetex.gov.co/es/becas/becas-para-estudios-en-el-exterior/becas-vigentes"
    print("\n[*] Rastreando becas vigentes en el portal de ICETEX Cooperación...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return []
        items = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="lnk_art_nuevo_cred"[^>]*>(.*?)</a>', r.text, re.DOTALL)
        results = []
        for link, raw_title in items:
            title = re.sub(r'<[^>]+>', '', raw_title).strip()
            title = re.sub(r'\s+', ' ', title)
            results.append({
                "titulo": title,
                "url": link.strip(),
                "entidad": "ICETEX Cooperación Internacional",
                "tipo": "Beca Internacional Vigente",
                "pais": "Global / Varios",
                "cobertura": "Ver requisitos en convocatoria",
                "area": "Ingeniería, Tecnología y Ciencias"
            })
        print(f" [✓] {len(results)} becas vigentes encontradas en ICETEX.")
        return results
    except Exception as e:
        print(f" [!] Error en ICETEX: {e}")
        return []

def compile_global_opportunities(icetex_live):
    """Compila convocatorias internacionales permanentes de alto impacto para Ingeniería Física."""
    print("\n[*] Compilando convocatorias globales de alto impacto para Ingeniería Física...")
    
    becas_fijas = [
        {
            "titulo": "Data Analytics & IA for Decision Making (India / ITEC)",
            "entidad": "Gobierno de la India • Indian Technical and Economic Cooperation (ITEC)",
            "pais": "India",
            "tipo": "Beca Completa Presencial",
            "cobertura": "100% (Tiquetes aéreos ida y vuelta, hospedaje, matrícula y estipendio diario)",
            "area": "Ciencia de Datos, Inteligencia Artificial y Modelado Cuantitativo",
            "descripcion": "Programa de alta especialización presencial para ingenieros y científicos en el International Statistical Education Centre (ISEC). Formación intensiva en analítica avanzada, series de tiempo y modelos predictivos.",
            "url": "https://web.icetex.gov.co/es/-/2026-data-analytics-for-decision-making-india",
            "destacada": True
        },
        {
            "titulo": "Maestrías en Ciencias e Ingeniería (China Scholarship Council - CSC)",
            "entidad": "Gobierno de la República Popular China • CSC / ICETEX",
            "pais": "China",
            "tipo": "Beca de Posgrado (Maestría)",
            "cobertura": "85% - 100% (Exención total de matrícula, alojamiento universitario, seguro médico y estipendio mensual)",
            "area": "Ciencia de Materiales, Nanotecnología, Óptica, IA y Energías Renovables",
            "descripcion": "Convocatoria para cursar maestrías en las mejores universidades tecnológicas chinas (Tsinghua, Zhejiang, Harbin Institute of Technology). Especialmente afín a líneas de investigación en semiconductores, caracterización de materiales y fotónica.",
            "url": "https://web.icetex.gov.co/es/becas/becas-para-estudios-en-el-exterior/becas-vigentes",
            "destacada": True
        },
        {
            "titulo": "Pasantías Técnicas Internacionales STEM (IAESTE)",
            "entidad": "IAESTE Colombia • Representado por Universidad de Ibagué / IAESTE Global",
            "pais": "Alemania, Austria, Reino Unido, Suiza, Japón y +80 países",
            "tipo": "Pasantía Industrial / Práctica Profesional Remunerada",
            "cobertura": "Estipendio mensual que cubre manutención completa y alojamiento en el país destino",
            "area": "Ingeniería Física, Electrónica, Mecatrónica, Control y Automatización",
            "descripcion": "Prácticas remuneradas de 6 semanas a 1 año en industrias y laboratorios de investigación internacionales. Los estudiantes colombianos compiten en cupos reservados por reciprocidad institucional.",
            "url": "https://iaeste.org.co/",
            "destacada": True
        },
        {
            "titulo": "Becas DAAD RISE & WISE (Alemania)",
            "entidad": "Servicio Alemán de Intercambio Académico (DAAD)",
            "pais": "Alemania",
            "tipo": "Pasantía de Investigación de Verano (Summer Research Internship)",
            "cobertura": "Estipendio mensual en euros, seguro médico integral y auxilio de viaje internacional",
            "area": "Física, Óptica, Cuántica, Materiales y Sistemas de Potencia",
            "descripcion": "Estancias de 3 meses trabajando mano a mano con investigadores doctorales en universidades de élite alemanas (TU Munich, RWTH Aachen, Heidelberg, KIT) o centros Helmholtz y Fraunhofer.",
            "url": "https://www.daad.co/es/becas/buscador-de-becas/",
            "destacada": True
        },
        {
            "titulo": "DAAD EPOS — Posgrados relacionados con desarrollo e ingeniería sostenible",
            "entidad": "Servicio Alemán de Intercambio Académico (DAAD)",
            "pais": "Alemania",
            "tipo": "Beca de Maestría / Doctorado",
            "cobertura": "Manutención mensual, seguro médico y apoyo de viaje; otros apoyos dependen del programa",
            "area": "Ingeniería, energía sostenible, materiales y ciencias aplicadas",
            "descripcion": "Becas para cursos de posgrado seleccionados. Dirigidas a egresados con al menos dos años de experiencia profesional; cada universidad publica su propia fecha límite y requisitos.",
            "estado_convocatoria": "Fechas y elegibilidad varían según el programa; revisar la lista oficial de cursos y cierres.",
            "url": "https://www.daad.co/es/becas/becas-de-posgrado/maestria-2/",
            "destacada": True
        },
        {
            "titulo": "Fundación Carolina — Becas de posgrado y doctorado",
            "entidad": "Fundación Carolina",
            "pais": "España",
            "tipo": "Becas de Maestría, Doctorado y estancias",
            "cobertura": "Parcial o completa según programa; revisar ficha y condiciones de cada beca",
            "area": "Ingeniería, tecnología, energía y ciencias aplicadas",
            "descripcion": "Convocatoria anual para estudios de posgrado en España. La edición 2026–2027 abrió el 12 de enero y cerró el 2 de marzo de 2026; las fechas de la próxima edición deben confirmarse en el portal oficial.",
            "estado_convocatoria": "Ciclo 2026–2027 cerrado; próxima convocatoria por anunciar.",
            "url": "https://www.fundacioncarolina.es/convocatoria-de-becas-2026-2027/",
            "destacada": True
        },
        {
            "titulo": "CERN Summer Student Programme (Ginebra, Suiza)",
            "entidad": "Organización Europea para la Investigación Nuclear (CERN)",
            "pais": "Suiza",
            "tipo": "Pasantía de Investigación Científica (8 a 13 semanas)",
            "cobertura": "90 CHF diarios de subsidio neto de manutención + seguro médico + gastos de viaje",
            "area": "Física Experimental, Partículas, Aceleradores, Instrumentación y Detectores",
            "descripcion": "Una de las pasantías más prestigiosas del mundo para estudiantes de física e ingeniería. Trabaja directamente en experimentos del Gran Colisionador de Hadrones (LHC), desarrollo de sensores criogénicos y computación científica.",
            "url": "https://careers.cern/summer",
            "destacada": True
        },
        {
            "titulo": "Mitacs Globalink Research Internship (Canadá)",
            "entidad": "Gobierno de Canadá • Mitacs",
            "pais": "Canadá",
            "tipo": "Pasantía de Investigación de Verano (12 semanas)",
            "cobertura": "100% financiado (Tiquetes aéreos ida y vuelta, hospedaje, estipendio y talleres)",
            "area": "Física Aplicada, Computación Cuántica, Nanotecnología e IA",
            "descripcion": "Pasantía de investigación en universidades canadienses de primer orden (McGill, Toronto, UBC, Waterloo). Estudiantes de pregrado colaboran directamente con profesores líderes en proyectos de vanguardia.",
            "url": "https://www.mitacs.ca/our-programs/globalink-research-internship-students/",
            "destacada": True
        },
        {
            "titulo": "Becas de Maestría Erasmus Mundus (Europhotonics / Quantum)",
            "entidad": "Comisión Europea • Erasmus+",
            "pais": "Francia, Alemania, España, Italia (Multidestino)",
            "tipo": "Maestría Conjunta Internacional con Beca Completa",
            "cobertura": "100% matrícula + estipendio mensual de 1.400 EUR + seguro de viaje",
            "area": "Óptica, Fotónica, Nanotecnología, Láseres y Tecnologías Cuánticas",
            "descripcion": "Programas como Europhotonics o Quantum Technologies donde estudias cada semestre en un país europeo distinto y obtienes doble o múltiple titulación de posgrado.",
            "url": "https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals/students/erasmus-mundus-joint-masters",
            "destacada": True
        }
    ]

    # Integrar becas vigentes en vivo de ICETEX
    for ic in icetex_live:
        becas_fijas.append({
            "titulo": ic["titulo"],
            "entidad": ic["entidad"],
            "pais": ic.get("pais", "Global"),
            "tipo": ic.get("tipo", "Beca Vigente"),
            "cobertura": ic.get("cobertura", "Ver términos en convocatoria"),
            "area": ic.get("area", "Ingeniería y Ciencias"),
            "descripcion": "Convocatoria oficial activa a través de la Dirección de Cooperación Internacional del ICETEX.",
            "estado_convocatoria": "Aparece en el catálogo oficial de convocatorias vigentes; confirmar la fecha límite en la ficha.",
            "url": ic["url"],
            "destacada": False
        })

    for beca in becas_fijas:
        beca.setdefault(
            "estado_convocatoria",
            "Programa periódico o de referencia; consulta fechas, elegibilidad y estado en el portal oficial."
        )

    with open(BECAS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(becas_fijas, f, ensure_ascii=False, indent=2)
    print(f" [✓] Total de {len(becas_fijas)} becas y pasantías guardadas en: {BECAS_JSON_PATH}")
    return becas_fijas

def main():
    print("="*70)
    print(" [ATOM] BOT DE BECAS, PASANTÍAS Y CONVENIOS INTERNACIONALES (UNAL)")
    print("        Ingeniería Física • Autor: Jimmy Rosero")
    print("="*70)
    
    # 1. Extraer y filtrar convenios internacionales de la UNAL (DRE)
    convenios = fetch_unal_convenios()
    
    # 2. Rastrear ICETEX en vivo
    icetex_becas = scrape_icetex_becas()
    
    # 3. Compilar becas y pasantías globales
    becas = compile_global_opportunities(icetex_becas)
    
    # 4. Regenerar el portal web completo
    print("\n[*] Sincronizando con el portal web general...")
    try:
        from bot_practicas import build_full_html, load_json, CONFIG_RAMAS_PATH, OUTPUT_JSON
        config_ramas = load_json(CONFIG_RAMAS_PATH)
        vacantes = load_json(OUTPUT_JSON)
        build_full_html(vacantes, config_ramas)
        print(" [✓] Portal HTML sincronizado exitosamente con becas y convenios.")
    except Exception as e:
        print(f" [!] Nota al regenerar portal completo: {e}")

    print("\n" + "="*70)
    print(" ¡ACTUALIZACIÓN DE BECAS Y CONVENIOS COMPLETADA!")
    print("="*70)

if __name__ == "__main__":
    main()
