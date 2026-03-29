# -*- coding: utf-8 -*-
"""Test rapido Grupo Venus - 3 URLs reales"""
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scraper.sources.grupo_venus import (
    FetcherGV, extraer_texto_gv, decodificar_clave_gv, init_db, insertar, DB_PATH
)

TEST_URLS = [
    ("transiaw", "JUPCJCASC",  "https://grupovenus.com/sacainter.asp?tabla=transiaw&cla=JUPCJCASC"),
    ("transiaw", "SATOPOSOL",  "https://grupovenus.com/sacainter.asp?tabla=transiaw&cla=SATOPOSOL"),
    ("starsolu", "SOLCJCLUN",  "https://grupovenus.com/sacainter.asp?tabla=starsolu&cla=SOLCJCLUN"),
]

conn    = init_db(DB_PATH)
fetcher = FetcherGV(delay=1.5)

for tabla, cla, url in TEST_URLS:
    print(f"\n{'='*60}")
    print(f"CLA: {cla} | URL: {url}")
    decoded = decodificar_clave_gv(cla, tabla)
    print(f"Decoded: {decoded}")

    soup = fetcher.get(url)
    if not soup:
        print("  ERROR: sin respuesta")
        continue

    texto_largo, texto_corto = extraer_texto_gv(soup, url)
    print(f"Texto largo ({len(texto_largo)} chars):")
    print(texto_largo[:600])
    print(f"\nTexto corto: {texto_corto[:200]}")

    if decoded and texto_largo and len(texto_largo) > 80:
        row = {
            "tipo": decoded["tipo"], "clave": decoded["clave"],
            "autor": "Grupo Venus", "fuente_url": url,
            "fuente_nombre": "Grupo Venus", "idioma_origen": "es",
            "texto_corto": texto_corto, "texto_largo": texto_largo,
            "calidad": 4,
        }
        ok = insertar(conn, row, dry_run=False)
        print(f"  -> Insertado: {ok}")

conn.close()
print("\nTest completado.")
