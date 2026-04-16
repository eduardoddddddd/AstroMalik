# -*- coding: utf-8 -*-
"""Explora índices de categorías para encontrar URLs reales"""
import sys, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from bs4 import BeautifulSoup

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

def get(url, delay=1.5):
    time.sleep(delay)
    r = requests.get(url, headers=HDR, timeout=15)
    return r

def extraer_links(url, filtros):
    r = get(url)
    if r.status_code != 200:
        print(f"  {r.status_code} {url}")
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        txt = a.get_text(strip=True)
        if any(f in href.lower() for f in filtros):
            links.append((txt, href))
    return links

# ── ASTROLIBRARY categorías ──────────────────────────────────────────────────
print("=== ASTROLIBRARY - Categoría planetas en signos ===")
links = extraer_links("https://astrolibrary.org/interpretations/category/planets-in-signs/",
                      ["sun","moon","mercury","venus","mars","saturn","jupiter","uranus","neptune","pluto"])
for txt, href in links[:30]:
    print(f"  {txt:<45} {href}")

print("\n=== ASTROLIBRARY - /sun/ page ===")
r = get("https://astrolibrary.org/sun/")
soup = BeautifulSoup(r.text, "html.parser")
contenido = soup.select_one("article, div.entry-content, main")
if contenido:
    texto = contenido.get_text(separator=" ", strip=True)
    print(f"  chars: {len(texto)}")
    print(f"  preview: {texto[:500]}")
# Sub-links desde /sun/
sub = [(a.get_text(strip=True), a["href"]) for a in soup.find_all("a", href=True)
       if "aries" in a["href"].lower() or "taurus" in a["href"].lower() or "gemini" in a["href"].lower()]
for t, h in sub[:10]:
    print(f"  link: {t} -> {h}")

# ── ASTRO-SEEK URLs correctas ────────────────────────────────────────────────
print("\n=== ASTRO-SEEK - Buscar patrón URL correcto ===")
r2 = get("https://horoscopes.astro-seek.com/astrology-chart-free-interpretations")
soup2 = BeautifulSoup(r2.text, "html.parser")
links2 = [(a.get_text(strip=True), a["href"]) for a in soup2.find_all("a", href=True)
          if any(k in a["href"] for k in ["sun","moon","mercury"]) and "astro-seek" in a["href"]]
for txt, href in links2[:20]:
    print(f"  {txt:<45} {href}")

# ── ASTRO.COM estructura natal ───────────────────────────────────────────────
print("\n=== ASTRO.COM - Ver si tienen páginas estáticas de planetas ===")
candidatas_astro = [
    "https://www.astro.com/astrology/in_nathowto_e.htm",
    "https://www.astro.com/astrology/in_signs_e.htm",
    "https://www.astro.com/astrowiki/en/Sun_in_Signs",
]
for url in candidatas_astro:
    r3 = get(url, delay=1.5)
    print(f"  {r3.status_code}  {url}")
    if r3.status_code == 200:
        soup3 = BeautifulSoup(r3.text, "html.parser")
        body = soup3.get_text(separator=" ", strip=True)
        print(f"    chars: {len(body)} | preview: {body[:200]}")
