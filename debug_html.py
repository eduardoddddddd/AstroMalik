"""debug_html.py — inspecciona estructura HTML de Cafe Astrology"""
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
url = "https://cafeastrology.com/sun-in-aries.html"

r = requests.get(url, headers=HEADERS, timeout=15)
print(f"Status: {r.status_code}")
soup = BeautifulSoup(r.text, "html.parser")

# Ver todos los divs con clase o id relevante
for tag in soup.find_all(["div","article","main","section"], limit=40):
    attrs = []
    if tag.get("class"):
        attrs.append("class=" + " ".join(tag["class"]))
    if tag.get("id"):
        attrs.append("id=" + tag["id"])
    if attrs:
        texto_preview = tag.get_text(strip=True)[:60].replace("\n"," ")
        print(f"  <{tag.name} {' '.join(attrs)}> → {texto_preview}")
