"""debug_sitemap.py — explora la estructura real de Cafe Astrology"""
import requests, time
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

def get(url, delay=2):
    time.sleep(delay)
    r = requests.get(url, headers=HEADERS, timeout=15)
    return r

# Pistas de la home: /zodiacaries.html, /sun.html, /saturn-aries-transit.html
urls_explorar = [
    "https://cafeastrology.com/sun.html",
    "https://cafeastrology.com/zodiacaries.html",
    "https://cafeastrology.com/saturn-aries-transit.html",
    "https://cafeastrology.com/articles/synastrysuninhouses.html",
    "https://cafeastrology.com/sitemap.xml",
    "https://cafeastrology.com/natal.html",
    "https://cafeastrology.com/planets.html",
]

for url in urls_explorar:
    r = get(url, delay=1.5)
    status = r.status_code
    print(f"\n{status}  {url}")
    if status == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("title")
        print(f"  TITLE: {title.text.strip()[:80] if title else '?'}")
        # Mostrar links internos relevantes (planetas, signos)
        keywords = ["aries","sun","moon","mercury","venus","mars","saturn",
                    "jupiter","transit","natal","house","aspect"]
        links = list({a['href'] for a in soup.find_all('a', href=True)
                     if any(k in a['href'].lower() for k in keywords)
                     and not a['href'].startswith('http')})
        for l in sorted(links)[:15]:
            print(f"    {l}")
