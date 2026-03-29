# -*- coding: utf-8 -*-
"""Analiza sitemap de GrupoVenus en detalle + inspecciona HTML real de home"""
import time, json
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings; warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
from pathlib import Path

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
       "Accept-Language": "es-ES,es;q=0.9"}

# --- Ver sitemap completo ---
print("=== SITEMAP GRUPOVENUS ===")
r = requests.get("https://www.grupovenus.com/sitemap.xml", headers=HDR, timeout=15)
soup = BeautifulSoup(r.content, "lxml")
locs = [l.text.strip() for l in soup.find_all("loc")]
print(f"Total: {len(locs)} URLs\n")

# Agrupar por patrón
from collections import Counter
patrones = Counter()
for u in locs:
    partes = u.replace("https://grupovenus.com/","").replace("https://www.grupovenus.com/","").split("/")
    patrones[partes[0] if partes else "raiz"] += 1

print("Directorios/secciones:")
for pat, cnt in patrones.most_common(20):
    print(f"  {pat:<30} {cnt:>3}")

print("\nMuestra de URLs (primeras 50):")
for u in locs[:50]:
    print(f"  {u}")

# --- Inspeccionar HTML real de home ---
print("\n=== HOME HTML ESTRUCTURA ===")
time.sleep(2)
r2 = requests.get("https://www.grupovenus.com/", headers=HDR, timeout=15)
soup2 = BeautifulSoup(r2.text, "html.parser")

# Script tags - clave para entender si es SPA
scripts = soup2.find_all("script")
print(f"Script tags: {len(scripts)}")
for s in scripts[:10]:
    src = s.get("src","")
    contenido_inline = s.string or ""
    if src:
        print(f"  <script src='{src}'>")
    elif contenido_inline.strip()[:100]:
        print(f"  <script inline> {contenido_inline.strip()[:120]}")

# Iframes
iframes = soup2.find_all("iframe")
print(f"\nIframes: {len(iframes)}")
for i in iframes:
    print(f"  <iframe src='{i.get('src','')}'>")

# Estructura principal
print("\nEstructura body (primeros divs):")
for tag in soup2.find_all(["div","section","main","article","header"], limit=20):
    cls = " ".join(tag.get("class",[]))
    iid = tag.get("id","")
    if cls or iid:
        txt = tag.get_text(strip=True)[:60]
        print(f"  <{tag.name} class='{cls}' id='{iid}'> {txt}")

# Links de navegación
print("\nTodos los links:")
for a in soup2.find_all("a", href=True)[:30]:
    print(f"  {a.get_text(strip=True):<40} → {a['href']}")
