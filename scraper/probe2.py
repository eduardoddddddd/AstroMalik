# -*- coding: utf-8 -*-
"""Profundiza en astrotheme y astrolibrary - busca URLs reales y calidad del texto"""
import sys, time, requests, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from bs4 import BeautifulSoup

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
       "Accept-Language": "en-US,en;q=0.9"}

def get(url, delay=2):
    time.sleep(delay)
    r = requests.get(url, headers=HDR, timeout=15)
    return r

# ── ASTROTHEME: extraer texto real ────────────────────────────────────────────
print("=== ASTROTHEME - Texto real de Sol en Aries ===")
r = get("https://www.astrotheme.com/astrology/sun_in_aries")
soup = BeautifulSoup(r.text, "html.parser")

# Buscar divs con texto sustancial
for tag in soup.find_all(["div","section","article","p"], limit=60):
    cls = " ".join(tag.get("class", []))
    texto = tag.get_text(strip=True)
    if len(texto) > 150 and len(texto) < 5000:
        if any(k in texto.lower() for k in ["aries","sun","personality","energy","fire","bold","pioneer"]):
            print(f"\n  <{tag.name} class='{cls}'>")
            print(f"  {texto[:500]}")
            break

print("\n=== ASTROTHEME - Links a planetas/casas ===")
links_planetas = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if "/astrology/" in href and any(k in href for k in ["sun_","moon_","mercury_","venus_","mars_","jupiter_","saturn_","uranus_","neptune_","pluto_"]):
        links_planetas.append(href)
for l in sorted(set(links_planetas))[:20]:
    print(f"  {l}")

# ── ASTROLIBRARY: buscar URLs correctas ──────────────────────────────────────
print("\n\n=== ASTROLIBRARY - URLs reales en el índice ===")
r2 = get("https://astrolibrary.org/interpretations/")
soup2 = BeautifulSoup(r2.text, "html.parser")
links2 = [(a.get_text(strip=True), a["href"]) for a in soup2.find_all("a", href=True)
          if "astrolibrary.org" in a["href"] or a["href"].startswith("/")]
for txt, href in links2[:40]:
    if any(k in href.lower() for k in ["sun","moon","mercury","venus","mars","jupiter","saturn","house","sign","planet"]):
        print(f"  {txt:<40} {href}")

# ── PROBAR URL real de astrolibrary ──────────────────────────────────────────
print("\n=== ASTROLIBRARY - Probando URLs candidatas ===")
candidatas = [
    "https://astrolibrary.org/sun-aries/",
    "https://astrolibrary.org/sun-in-aries-meaning/",
    "https://astrolibrary.org/natal-sun-in-aries/",
    "https://astrolibrary.org/planets/sun/aries/",
    "https://astrolibrary.org/sun/",
]
for url in candidatas:
    r3 = get(url, delay=1.5)
    print(f"  {r3.status_code}  {url}")
