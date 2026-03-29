"""debug_urls.py — encuentra URLs reales de Cafe Astrology"""
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

# Probar variantes de URL
urls_test = [
    "https://cafeastrology.com/sun-in-aries.html",
    "https://cafeastrology.com/suninaries.html",
    "https://cafeastrology.com/articles/suninaries.html",
    "https://cafeastrology.com/natal/sun-in-aries/",
    "https://cafeastrology.com/sun-sign-aries.html",
    "https://cafeastrology.com/",   # home para ver menú
]

for url in urls_test:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"  {r.status_code}  {url}")
        if r.status_code == 200 and url.endswith("/"):
            # Buscar links internos con 'sun' o 'aries'
            soup = BeautifulSoup(r.text, "html.parser")
            links = [a['href'] for a in soup.find_all('a', href=True)
                     if 'sun' in a['href'].lower() or 'aries' in a['href'].lower()]
            for l in links[:10]:
                print(f"    LINK: {l}")
    except Exception as e:
        print(f"  ERR  {url} — {e}")
