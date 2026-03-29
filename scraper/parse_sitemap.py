# -*- coding: utf-8 -*-
"""
scraper/parse_sitemap.py
Descarga los sub-sitemaps de Cafe Astrology y clasifica solo URLs de alta confianza.
Genera: scraper/cafe_astrology_urls.json

Uso: python scraper/parse_sitemap.py
"""

import json
import re
import sys
import time
import warnings
from collections import defaultdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_URL = "https://cafeastrology.com"
OUT_FILE = Path(__file__).parent / "cafe_astrology_urls.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

PLANETA_SLUG = r"(sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto|chiron|north-node|south-node)"
RE_ASPECTO_NATAL = re.compile(
    rf"^https://cafeastrology\.com/aspects/"
    rf"{PLANETA_SLUG}-(conjunct|opposite|square|trine|sextile|quincunx)-{PLANETA_SLUG}\.html$"
)
RE_SINASTRIA = re.compile(
    rf"^https://cafeastrology\.com/synastry/(?:relationship-)?{PLANETA_SLUG}-{PLANETA_SLUG}-aspects\.html$"
)
RE_TRANSITO = re.compile(
    r"^https://cafeastrology\.com/"
    r"(?:[a-z-]+-transit|[a-z-]+-transits(?:-[a-z-]+)?)\.html$"
)


def clasificar(url):
    u = url.lower().strip()
    if RE_ASPECTO_NATAL.match(u):
        return "aspecto_natal"
    if RE_SINASTRIA.match(u):
        return "sinastria"
    if RE_TRANSITO.match(u) and "/tag/" not in u and "/events/" not in u and "/astrologytopics/" not in u:
        return "transito"
    return None


def bajar_sitemap(url, delay=1.5):
    time.sleep(delay)
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")
    return [loc.get_text(strip=True) for loc in soup.find_all("loc")]


def main():
    print("Descargando indice de sitemaps...")
    todas_locs = bajar_sitemap(f"{BASE_URL}/sitemap.xml", delay=1)

    sub_sitemaps = [u for u in todas_locs if "sitemap" in u.lower()]
    urls_directas = [u for u in todas_locs if "sitemap" not in u.lower()]
    print(f"  Sub-sitemaps: {len(sub_sitemaps)}")
    print(f"  URLs directas en raiz: {len(urls_directas)}")

    todas_urls = list(urls_directas)
    for i, sub_url in enumerate(sub_sitemaps, 1):
        nombre = sub_url.split("/")[-1]
        print(f"  [{i:02d}/{len(sub_sitemaps)}] {nombre}", end=" ... ", flush=True)
        urls = bajar_sitemap(sub_url, delay=1.5)
        paginas = [u for u in urls if "sitemap" not in u.lower()]
        todas_urls.extend(paginas)
        print(f"{len(paginas)} URLs")

    print(f"\nTotal URLs en sitemap: {len(todas_urls)}")

    clasificadas = defaultdict(list)
    for url in todas_urls:
        tipo = clasificar(url)
        if tipo:
            clasificadas[tipo].append(url)

    for tipo in list(clasificadas.keys()):
        clasificadas[tipo] = sorted(set(clasificadas[tipo]))

    print("\n--- Clasificacion de alta confianza ---")
    total_rel = 0
    for tipo in sorted(clasificadas):
        n = len(clasificadas[tipo])
        total_rel += n
        print(f"  {tipo:<25} {n:>4} URLs")
    print(f"  {'TOTAL RELEVANTE':<25} {total_rel:>4} URLs")
    print(f"  {'(sitemap total)':<25} {len(todas_urls):>4} URLs")

    resultado = {
        "total_sitemap": len(todas_urls),
        "total_relevante": total_rel,
        "clasificadas": {k: v for k, v in sorted(clasificadas.items())},
    }
    OUT_FILE.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nGuardado: {OUT_FILE}")

    print("\n--- Muestra 5 URLs por tipo ---")
    for tipo in sorted(clasificadas):
        print(f"\n  [{tipo}]")
        for u in clasificadas[tipo][:5]:
            print(f"    {u}")


if __name__ == "__main__":
    main()
