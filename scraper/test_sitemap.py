# -*- coding: utf-8 -*-
import sys, time, warnings, json, re
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BASE_URL = "https://cafeastrology.com"
HEADERS  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

try:
    print("Descargando sitemap...")
    r = requests.get(f"{BASE_URL}/sitemap.xml", headers=HEADERS, timeout=20)
    print(f"Status: {r.status_code}")
    soup = BeautifulSoup(r.content, "lxml-xml")
    
    # Ver estructura
    sitemaps = soup.find_all("sitemap")
    urls_direct = soup.find_all("url")
    print(f"Sub-sitemaps: {len(sitemaps)}")
    print(f"URLs directas: {len(urls_direct)}")
    
    # Mostrar sub-sitemaps
    for s in sitemaps[:5]:
        loc = s.find("loc")
        if loc: print(f"  sub: {loc.text.strip()}")
    
    # Si hay sub-sitemaps, bajar el primero
    if sitemaps:
        first_loc = sitemaps[0].find("loc").text.strip()
        print(f"\nBajando primer sub-sitemap: {first_loc}")
        time.sleep(2)
        r2 = requests.get(first_loc, headers=HEADERS, timeout=20)
        soup2 = BeautifulSoup(r2.content, "lxml-xml")
        sub_urls = [u.find("loc").text.strip() for u in soup2.find_all("url") if u.find("loc")]
        print(f"URLs en primer sub-sitemap: {len(sub_urls)}")
        for u in sub_urls[:10]:
            print(f"  {u}")
            
except Exception as e:
    import traceback
    traceback.print_exc()
