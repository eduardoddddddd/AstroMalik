# -*- coding: utf-8 -*-
"""
scraper/fill_sinastria.py
Rellena los 75 huecos de sinastría detectados en corpus.db.

Estrategia:
  1. Calcula los huecos exactos vs teórico
  2. Para cada hueco, construye la clave GV y prueba la URL directa
  3. Si GV no tiene el par A->B, prueba el par invertido B->A
     (el texto es el mismo aspecto, solo cambia la perspectiva)
  4. Si tampoco, lo marca como no disponible

Uso: python scraper/fill_sinastria.py [--dry-run]
"""
import sys, sqlite3, time, logging
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sources.grupo_venus import (
    FetcherGV, extraer_texto_gv, insertar, init_db, DB_PATH,
    DECODE_PLANETA, FUENTE_NOMBRE, FUENTE_CALIDAD
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("fill_sinastria")

BASE_URL = "https://grupovenus.com"

# Mapa inverso ES -> cod3 para construir URLs GV
ES_A_COD = {v: k for k, v in DECODE_PLANETA.items()}
ASPECTO_COD = {
    "CONJUNCION": "CJC", "OPOSICION": "OPO",
    "CUADRADO":   "CUA", "TRIGONO":   "TRI", "SEXTIL": "SEX"
}

PLANETAS  = ["SOL","LUNA","MERCURIO","VENUS","MARTE","JUPITER",
             "SATURNO","URANO","NEPTUNO","PLUTON"]
ASPECTOS  = ["CONJUNCION","OPOSICION","CUADRADO","TRIGONO","SEXTIL"]

def calcular_huecos(conn):
    """Devuelve set de claves SYN_P1_P2_ASP que faltan."""
    teorico = set()
    for p1 in PLANETAS:
        for asp in ASPECTOS:
            for p2 in PLANETAS:
                if p1 != p2:
                    teorico.add(f"SYN_{p1}_{p2}_{asp}")
    reales = set(r[0] for r in conn.execute(
        "SELECT DISTINCT clave FROM interpretaciones WHERE tipo='sinastria'"))
    return teorico - reales

def clave_a_url_gv(clave):
    """
    SYN_LUNA_JUPITER_CONJUNCION -> URL GV directa y URL con pares invertidos.
    Devuelve (url_directa, url_inversa)
    """
    partes = clave.split("_")
    # formato: SYN _ P1 _ P2 _ ASPECTO
    # pero P1 y P2 pueden ser MERCURIO (una sola palabra) y el aspecto al final
    # Reconstruimos: SYN + p1 (1 token) + p2 (1 token) + asp (1 token)
    # clave: SYN_LUNA_JUPITER_CONJUNCION -> ['SYN','LUNA','JUPITER','CONJUNCION']
    if len(partes) != 4 or partes[0] != "SYN":
        return None, None
    _, p1_es, p2_es, asp_es = partes

    cod_p1  = ES_A_COD.get(p1_es)
    cod_p2  = ES_A_COD.get(p2_es)
    cod_asp = ASPECTO_COD.get(asp_es)
    if not cod_p1 or not cod_p2 or not cod_asp:
        return None, None

    # URL directa: p1+asp+p2
    cla_dir = f"{cod_p1}{cod_asp}{cod_p2}"
    url_dir = f"{BASE_URL}/sacainter.asp?tabla=tracompu&cla={cla_dir}"
    # URL inversa: p2+asp+p1
    cla_inv = f"{cod_p2}{cod_asp}{cod_p1}"
    url_inv = f"{BASE_URL}/sacainter.asp?tabla=tracompu&cla={cla_inv}"
    return url_dir, url_inv

def intentar_scrape(fetcher, url, clave, fuente_url_label):
    """Intenta obtener texto de una URL. Devuelve (texto_largo, texto_corto) o ('','')."""
    soup = fetcher.get(url)
    if not soup:
        return "", ""
    tl, tc = extraer_texto_gv(soup, url)
    return tl, tc

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()

    conn    = init_db(DB_PATH)
    fetcher = FetcherGV(delay=args.delay)

    huecos = calcular_huecos(conn)
    print(f"\nHuecos detectados: {len(huecos)}")

    insertados = 0
    no_encontrados = []

    for i, clave in enumerate(sorted(huecos), 1):
        url_dir, url_inv = clave_a_url_gv(clave)
        if not url_dir:
            log.warning(f"  No se pudo construir URL para: {clave}")
            no_encontrados.append(clave)
            continue

        log.info(f"[{i:02d}/{len(huecos)}] {clave}")

        # Intento 1: URL directa
        tl, tc = intentar_scrape(fetcher, url_dir, clave, url_dir)

        # Intento 2: URL inversa (GV puede tener solo B->A)
        if not tl and url_inv:
            log.info(f"  Probando inversa: {url_inv}")
            tl, tc = intentar_scrape(fetcher, url_inv, clave, url_inv)
            url_usada = url_inv
        else:
            url_usada = url_dir

        if not tl or len(tl) < 80:
            log.warning(f"  Sin texto para: {clave}")
            no_encontrados.append(clave)
            continue

        row = {
            "tipo":          "sinastria",
            "clave":         clave,
            "autor":         "Grupo Venus",
            "fuente_url":    url_usada,
            "fuente_nombre": FUENTE_NOMBRE,
            "idioma_origen": "es",
            "texto_corto":   tc,
            "texto_largo":   tl,
            "calidad":       FUENTE_CALIDAD,
        }
        if insertar(conn, row, dry_run=args.dry_run):
            insertados += 1

    print(f"\n{'='*50}")
    print(f"  Insertados:      {insertados}")
    print(f"  No encontrados:  {len(no_encontrados)}")
    if no_encontrados:
        print("  Claves sin texto:")
        for c in no_encontrados[:20]:
            print(f"    {c}")

    # Cobertura final
    total_syn = conn.execute(
        "SELECT COUNT(DISTINCT clave) FROM interpretaciones WHERE tipo='sinastria'"
    ).fetchone()[0]
    teorico = len(PLANETAS) * (len(PLANETAS)-1) * len(ASPECTOS)
    print(f"\n  Cobertura sinastria: {total_syn}/{teorico} "
          f"({100*total_syn//teorico}%)")
    conn.close()

if __name__ == "__main__":
    main()
