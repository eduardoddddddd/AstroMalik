# -*- coding: utf-8 -*-
"""Valida calidad y estructura de astrolibrary y astro-seek para natal"""
import sys, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from bs4 import BeautifulSoup

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

def get(url, delay=1.5):
    time.sleep(delay)
    return requests.get(url, headers=HDR, timeout=15)

# ══════════════════════════════════════════════════════
# ASTROLIBRARY — planetas en SIGNOS (una página por planeta, todos los signos)
# ══════════════════════════════════════════════════════
print("=== ASTROLIBRARY - Sol en Signos (una sola pagina!) ===")
r = get("https://astrolibrary.org/interpretations/sun/")
soup = BeautifulSoup(r.text, "html.parser")
articulo = soup.select_one("article, div.entry-content, main")
if articulo:
    # Buscar secciones H2/H3 que corresponden a signos
    secciones = articulo.find_all(["h2","h3"])
    print(f"  Secciones encontradas: {len(secciones)}")
    for s in secciones[:14]:
        print(f"    H: {s.get_text(strip=True)}")
    # Texto total
    texto = articulo.get_text(separator="\n", strip=True)
    print(f"  Total chars: {len(texto)}")
    # Muestra Aries
    idx = texto.find("Aries")
    if idx >= 0:
        print(f"\n  [SOL EN ARIES - preview]\n  {texto[idx:idx+400]}")

# ══════════════════════════════════════════════════════
# ASTROLIBRARY — planetas en CASAS  
# ══════════════════════════════════════════════════════
print("\n=== ASTROLIBRARY - Planetas en Casas ===")
casas_urls = [
    "https://astrolibrary.org/interpretations/category/planets-in-houses/",
    "https://astrolibrary.org/interpretations/sun-in-houses/",
    "https://astrolibrary.org/sun-in-houses/",
    "https://astrolibrary.org/interpretations/sun-houses/",
]
for url in casas_urls:
    r2 = get(url, delay=1.2)
    print(f"  {r2.status_code}  {url}")
    if r2.status_code == 200:
        soup2 = BeautifulSoup(r2.text, "html.parser")
        art = soup2.select_one("article, div.entry-content, main")
        if art:
            txt = art.get_text(separator=" ", strip=True)
            print(f"    chars: {len(txt)} | preview: {txt[:250]}")

# ══════════════════════════════════════════════════════
# ASTRO-SEEK — planetas en SIGNOS (URLs individuales)
# ══════════════════════════════════════════════════════
print("\n=== ASTRO-SEEK - Sol en Aries ===")
r3 = get("https://horoscopes.astro-seek.com/sun-in-aries-sign-astrology-meaning")
soup3 = BeautifulSoup(r3.text, "html.parser")
print(f"  Status: {r3.status_code}")
for sel in ["div.interpretations","div.content","article","main","div.box-content","div#content"]:
    bloque = soup3.select_one(sel)
    if bloque:
        txt = bloque.get_text(separator=" ", strip=True)
        if len(txt) > 200:
            print(f"  selector={sel} chars={len(txt)}")
            print(f"  preview: {txt[:400]}")
            break

# Buscar URLs de casas en astro-seek
print("\n=== ASTRO-SEEK - Patrón URLs casas ===")
r4 = get("https://horoscopes.astro-seek.com/astrology-chart-free-interpretations")
soup4 = BeautifulSoup(r4.text, "html.parser")
house_links = [(a.get_text(strip=True), a["href"]) for a in soup4.find_all("a", href=True)
               if "house" in a["href"].lower() and "astro-seek" in a["href"]]
for txt, href in house_links[:15]:
    print(f"  {txt:<40} {href}")
