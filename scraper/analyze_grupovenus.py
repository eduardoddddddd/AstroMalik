"""
scraper/analyze_grupovenus.py
Analiza la estructura de grupovenus.com para evaluar viabilidad de scraping.
No guarda nada en BD — solo exploración y reporte.

Objetivo: entender cómo están estructurados sus tránsitos (el modelo que queremos replicar).
Uso: python scraper/analyze_grupovenus.py
"""

import time, json, re, warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from pathlib import Path
from urllib.parse import urljoin

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_URL = "https://www.grupovenus.com"
HEADERS  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Accept-Language": "es-ES,es;q=0.9"}
OUT_FILE = Path(__file__).parent / "grupovenus_analysis.json"

def get(url, delay=2):
    time.sleep(delay)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r
    except Exception as e:
        print(f"  ERR {url}: {e}")
        return None

def analizar_pagina_transito(soup, url):
    """Analiza la estructura interna de una página de tránsito."""
    info = {"url": url, "estructura": {}}

    # Título
    h1 = soup.find("h1")
    info["titulo"] = h1.get_text(strip=True) if h1 else "?"

    # Buscar si hay sistema de estrellas / intensidad
    estrellas = soup.find_all(class_=re.compile(r"star|rating|intensi|nivel", re.I))
    info["estructura"]["sistema_intensidad"] = len(estrellas) > 0
    if estrellas:
        info["estructura"]["intensidad_clases"] = [str(e.get("class")) for e in estrellas[:3]]

    # Buscar navegación por fecha
    fecha_nav = soup.find_all(class_=re.compile(r"fecha|date|calendar|mes|month", re.I))
    info["estructura"]["navegacion_fecha"] = len(fecha_nav) > 0

    # Buscar selector de planeta / aspecto
    selects = soup.find_all(["select", "input"])
    info["estructura"]["hay_formulario"] = len(selects) > 0
    info["estructura"]["num_selects"] = len(selects)

    # Bloque de texto principal
    for selector in ["div.entry-content","div#content","article","div.post","main"]:
        bloque = soup.select_one(selector)
        if bloque:
            texto = bloque.get_text(separator=" ", strip=True)
            info["texto_preview"] = texto[:400]
            info["estructura"]["selector_contenido"] = selector
            info["estructura"]["longitud_texto"] = len(texto)
            break

    # Estructura general de divs con clase
    divs_info = []
    for tag in soup.find_all(["div","section","article"], limit=30):
        cls = tag.get("class")
        iid = tag.get("id")
        if cls or iid:
            divs_info.append({
                "tag": tag.name,
                "class": " ".join(cls) if cls else None,
                "id": iid,
            })
    info["estructura"]["divs_principales"] = divs_info[:15]

    return info

def main():
    resultado = {
        "base_url": BASE_URL,
        "paginas_analizadas": [],
        "resumen": {}
    }

    # 1. Home
    print(f"\n[1] Home: {BASE_URL}")
    r = get(BASE_URL, delay=1)
    if r and r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("title")
        print(f"  Título: {title.text.strip()[:80] if title else '?'}")
        print(f"  Status: {r.status_code}")

        # Extraer todos los links relevantes
        links = {}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            texto = a.get_text(strip=True)
            if any(k in href.lower() for k in ["transit","transito","aspecto","planeta","signo","carta","natal"]):
                full = urljoin(BASE_URL, href)
                links[full] = texto
        resultado["links_relevantes_home"] = links
        print(f"  Links relevantes encontrados: {len(links)}")
        for url, txt in list(links.items())[:10]:
            print(f"    {txt[:40]:<40} → {url}")
    else:
        print(f"  Status: {r.status_code if r else 'ERR'}")

    # 2. Intentar sitemap
    print(f"\n[2] Sitemap")
    for sm_url in [f"{BASE_URL}/sitemap.xml", f"{BASE_URL}/sitemap_index.xml"]:
        r = get(sm_url, delay=1.5)
        if r and r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            sm_urls = [loc.text.strip() for loc in soup.find_all("loc")]
            resultado["sitemap_urls_muestra"] = sm_urls[:30]
            print(f"  {sm_url} → {len(sm_urls)} URLs")
            # Buscar urls de tránsitos
            transit_urls = [u for u in sm_urls if "transit" in u.lower() or "transito" in u.lower()]
            print(f"  URLs de tránsitos en sitemap: {len(transit_urls)}")
            for u in transit_urls[:5]:
                print(f"    {u}")
            break
        else:
            print(f"  {sm_url} → {r.status_code if r else 'ERR'}")

    # 3. Explorar sección de tránsitos si encontramos URL
    transito_url = None
    for url in resultado.get("links_relevantes_home", {}).keys():
        if "transit" in url.lower() or "transito" in url.lower():
            transito_url = url
            break

    if not transito_url:
        # Intentar URLs comunes
        for candidata in [
            f"{BASE_URL}/transitos",
            f"{BASE_URL}/transits",
            f"{BASE_URL}/transitos.html",
            f"{BASE_URL}/es/transitos",
        ]:
            r = get(candidata, delay=1.5)
            if r and r.status_code == 200:
                transito_url = candidata
                break

    if transito_url:
        print(f"\n[3] Página de tránsitos: {transito_url}")
        r = get(transito_url, delay=2)
        if r and r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            info = analizar_pagina_transito(soup, transito_url)
            resultado["paginas_analizadas"].append(info)
            print(f"  Título: {info.get('titulo','?')}")
            print(f"  Texto preview: {info.get('texto_preview','')[:200]}")
            print(f"  Selector contenido: {info['estructura'].get('selector_contenido','?')}")
            print(f"  Longitud texto: {info['estructura'].get('longitud_texto',0)}")
            print(f"  Sistema intensidad: {info['estructura'].get('sistema_intensidad')}")
    else:
        print("\n[3] No encontré URL de tránsitos desde home")

    # Guardar resultado
    OUT_FILE.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Análisis guardado: {OUT_FILE}")

if __name__ == "__main__":
    main()
