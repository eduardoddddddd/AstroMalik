# -*- coding: utf-8 -*-
"""Exploración manual de Grupo Venus - versión robusta"""
import time, json, re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

BASE = "https://www.grupovenus.com"
HDR  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept-Language": "es-ES,es;q=0.9"}
OUT  = Path("scraper/grupovenus_analysis.json")

def get(url, delay=2):
    time.sleep(delay)
    try:
        r = requests.get(url, headers=HDR, timeout=20)
        return r
    except Exception as e:
        print(f"  ERR: {e}")
        return None

resultado = {}

# --- HOME ---
print("[1] Home")
r = get(BASE, 1)
if r:
    print(f"  Status: {r.status_code}")
    soup = BeautifulSoup(r.text, "html.parser")
    # Todos los links
    all_links = [(a.get_text(strip=True)[:50], urljoin(BASE, a["href"]))
                 for a in soup.find_all("a", href=True) if a.get_text(strip=True)]
    # Menu/nav links
    nav_links = []
    for nav in soup.find_all(["nav","ul","menu"]):
        for a in nav.find_all("a", href=True):
            nav_links.append((a.get_text(strip=True), urljoin(BASE, a["href"])))

    print(f"  Total links: {len(all_links)}")
    print("  Nav links:")
    for txt, url in nav_links[:20]:
        print(f"    {txt:<35} {url}")
    resultado["nav_links"] = nav_links[:30]

# --- SITEMAP ---
print("\n[2] Sitemap")
for sm in [f"{BASE}/sitemap.xml", f"{BASE}/sitemap_index.xml", f"{BASE}/sitemap/"]:
    r = get(sm, 1.5)
    if r and r.status_code == 200 and "xml" in r.headers.get("content-type",""):
        from bs4 import XMLParsedAsHTMLWarning
        import warnings; warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(r.content, "lxml")
        locs = [l.text.strip() for l in soup.find_all("loc")]
        print(f"  {sm}: {len(locs)} URLs")
        resultado["sitemap_url"] = sm
        resultado["sitemap_muestra"] = locs[:40]
        
        # Filtrar por tránsitos/aspectos
        transit_urls = [u for u in locs if any(k in u.lower() 
                        for k in ["transit","transito","transito","aspecto","planeta"])]
        print(f"  URLs relevantes: {len(transit_urls)}")
        for u in transit_urls[:10]:
            print(f"    {u}")
        break
    else:
        status = r.status_code if r else "ERR"
        print(f"  {sm}: {status}")

# --- PÁGINAS CLAVE ---
# Intentar URLs de tránsitos típicas en español
print("\n[3] Secciones de tránsitos")
candidatas = [
    f"{BASE}/transitos/",
    f"{BASE}/transits/",
    f"{BASE}/astrologia/transitos/",
    f"{BASE}/interpretaciones/transitos/",
    f"{BASE}/saturn-conjunct-sun/",
    f"{BASE}/saturno-conjuncion-sol/",
    f"{BASE}/jupiter-trine-venus/",
    f"{BASE}/carta-astral/transitos/",
]
for url in candidatas:
    r = get(url, 1.5)
    if r and r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        h1 = soup.find("h1")
        print(f"  200 {url}")
        print(f"      H1: {h1.get_text(strip=True)[:80] if h1 else '?'}")
        
        # Estructura de divs
        divs = [(tag.name, " ".join(tag.get("class",[])), tag.get("id",""))
                for tag in soup.find_all(["div","section","article","main"], limit=20)
                if tag.get("class") or tag.get("id")]
        for d in divs[:10]:
            print(f"      <{d[0]} class='{d[1]}' id='{d[2]}'>")
        
        # Texto preview
        contenido = soup.select_one("div.entry-content, article, main, div#content, div.post")
        if contenido:
            texto = contenido.get_text(separator=" ", strip=True)
            print(f"      Texto ({len(texto)} chars): {texto[:300]}")
        resultado[f"pagina_{url.split('/')[-2]}"] = {
            "url": url, "h1": h1.get_text(strip=True) if h1 else None,
            "texto_preview": texto[:500] if contenido else None
        }
        break
    else:
        print(f"  {r.status_code if r else 'ERR'} {url}")

# --- ANÁLISIS ESTRUCTURA CARTA ASTRAL (su función principal) ---
print("\n[4] Carta astral interactiva")
carta_urls = [f"{BASE}/carta-astral/", f"{BASE}/carta-astral-gratis/",
              f"{BASE}/carta-natal/", f"{BASE}/"]
for url in carta_urls:
    r = get(url, 1.5)
    if r and r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        forms = soup.find_all("form")
        inputs = soup.find_all("input")
        selects = soup.find_all("select")
        print(f"  URL: {url}")
        print(f"  Forms: {len(forms)}, Inputs: {len(inputs)}, Selects: {len(selects)}")
        for inp in inputs[:8]:
            print(f"    <input name='{inp.get('name','')}' type='{inp.get('type','')}' placeholder='{inp.get('placeholder','')}'>")
        
        # Buscar si usan JavaScript para los tránsitos (JS dinámico = más difícil de scrapear)
        scripts = soup.find_all("script", src=True)
        js_externos = [s["src"] for s in scripts if "grupovenus" in s.get("src","").lower()]
        print(f"  Scripts propios: {js_externos[:5]}")
        
        ajax_clues = re.findall(r"ajax|fetch|XMLHttpRequest|axios", r.text)
        print(f"  Indicios de AJAX/fetch: {len(ajax_clues)}")
        break

# Guardar
OUT.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nGuardado: {OUT}")
