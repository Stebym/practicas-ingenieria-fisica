#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
BOT DE BECAS Y PASANTÍAS INTERNACIONALES (PORTAL IPF)
Autor: Jimmy Stebym Rosero Barrera <jiroserob@unal.edu.co>
Universidad Nacional de Colombia - Sede Medellín • Ingeniería Física
Licencia: MIT con descargo de responsabilidad (ver LICENSE)
=============================================================================
Rastrea becas vigentes del ICETEX y compila convocatorias internacionales de
alto impacto para Ingeniería Física (IAESTE, DAAD, CERN, Mitacs, CSC, ITEC, Erasmus).
Salida: becas_internacionales.json (la página la arma bot_pagina.py).
"""

import os
import re
import json
import requests

from firma import encabezado_bot, sellar_registros

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BECAS_JSON_PATH = os.path.join(BASE_DIR, "becas_internacionales.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

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
            "url": ic["url"],
            "destacada": False
        })

    sellar_registros(becas_fijas)
    with open(BECAS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(becas_fijas, f, ensure_ascii=False, indent=2)
    print(f" [✓] Total de {len(becas_fijas)} becas y pasantías guardadas en: {BECAS_JSON_PATH}")
    return becas_fijas

def main():
    print(encabezado_bot("[BECAS] BOT DE BECAS Y PASANTÍAS INTERNACIONALES"))
    compile_global_opportunities(scrape_icetex_becas())

if __name__ == "__main__":
    main()
