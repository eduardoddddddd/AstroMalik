# -*- coding: utf-8 -*-
"""Explora candidatos a fuente para natal_planeta_signo y natal_planeta_casa"""
import sys, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from bs4 import BeautifulSoup

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

def get(url, delay=1.5):
    time.sleep(delay)
    try:
        r = requests.get(url, headers=HDR, timeout=15)
        return r
    except Exception as e:
        print(f"  ERR: {e}")
        return None

def probar_fuente(nombre, urls_test):
    print(f"\n{'='*55}")
    print(f"  {nombre}")
    print(f"{'='*55}")
    for url in urls_test:
        r = get(url, delay=1.5)
        if not r:
            print(f"  ERR  {url}")
            continue
        print(f"  {r.status_code}  {url}")
        if r.status_code != 200:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        # Buscar contenido principal
        for sel in ["article","div.entry-content","div#content","main","div.post-content","div.content"]:
            bloque = soup.select_one(sel)
            if bloque:
                # Eliminar nav/scripts
                for t in bloque.find_all(["script","style","nav","aside"]):
                    t.decompose()
                texto = bloque.get_text(separator=" ", strip=True)
                if len(texto) > 200:
                    print(f"       selector: {sel} | chars: {len(texto)}")
                    print(f"       preview: {texto[:300]}")
                    break
        else:
            body = soup.find("body")
            if body:
                texto = body.get_text(separator=" ", strip=True)
                print(f"       body chars: {len(texto)}")
                print(f"       preview: {texto[:300]}")

# ── 1. ASTROLIBRARY.ORG ──────────────────────────────────────────────────────
probar_fuente("astrolibrary.org", [
    "https://astrolibrary.org/interpretations/",
    "https://astrolibrary.org/sun-in-aries/",
    "https://astrolibrary.org/sun-in-1st-house/",
    "https://astrolibrary.org/moon-in-taurus/",
    "https://astrolibrary.org/saturn-in-12th-house/",
])

# ── 2. ASTRO-SEEK.COM ─────────────────────────────────────────────────────────
probar_fuente("astro-seek.com", [
    "https://horoscopes.astro-seek.com/astrology-chart-free-interpretations",
    "https://horoscopes.astro-seek.com/sun-in-aries-natal",
    "https://horoscopes.astro-seek.com/sun-in-1st-house-natal",
    "https://horoscopes.astro-seek.com/moon-in-taurus-natal",
])

# ── 3. ASTROTHEME.COM ────────────────────────────────────────────────────────
probar_fuente("astrotheme.com", [
    "https://www.astrotheme.com/astrology/sun_in_aries",
    "https://www.astrotheme.com/astrology/sun_in_first_house",
    "https://www.astrotheme.com/astrology/moon_in_taurus",
])

# ── 4. ASTROMATRIX.ORG ───────────────────────────────────────────────────────
probar_fuente("astromatrix.org", [
    "https://astromatrix.org/Astrology/Sun-In-Aries-Natal-Chart",
    "https://astromatrix.org/Astrology/Sun-In-1st-House-Natal-Chart",
    "https://astromatrix.org/Astrology/Moon-In-Taurus-Natal-Chart",
])
