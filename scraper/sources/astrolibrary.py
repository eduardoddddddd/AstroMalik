# -*- coding: utf-8 -*-
"""
astrolibrary.py - Scraper para astrolibrary.org
Signos:  /interpretations/[planeta]/       -> 12 secciones H2 "Sun in Aries"
Casas:   /interpretations/[planeta]-house/ -> 12 secciones H2 "Sun in 1st House"
Motor:   deep-translator (Google Translate, sin cuota)
"""
import sys, sqlite3, time, argparse, logging
import requests
from bs4 import BeautifulSoup
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(__file__).resolve().parents[2]
DB_PATH       = BASE_DIR / "backend" / "data" / "corpus.db"
SCHEMA        = BASE_DIR / "corpus" / "schema.sql"
FUENTE_NOMBRE = "Astrolibrary"
FUENTE_CALIDAD = 4
DELAY_HTTP    = 2.0
DELAY_TRADUC  = 0.8

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("astrolibrary")

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
       "Accept-Language": "en-US,en;q=0.9"}

PLANETAS_EN_ES = {
    "sun":"SOL","moon":"LUNA","mercury":"MERCURIO","venus":"VENUS",
    "mars":"MARTE","jupiter":"JUPITER","saturn":"SATURNO",
    "uranus":"URANO","neptune":"NEPTUNO","pluto":"PLUTON",
}
SIGNOS_EN_ES = {
    "aries":"ARIES","taurus":"TAURO","gemini":"GEMINIS","cancer":"CANCER",
    "leo":"LEO","virgo":"VIRGO","libra":"LIBRA","scorpio":"ESCORPIO",
    "sagittarius":"SAGITARIO","capricorn":"CAPRICORNIO",
    "aquarius":"ACUARIO","pisces":"PISCIS",
}
SIGNOS_ORDER = list(SIGNOS_EN_ES.keys())

# Casas: astrolibrary usa "1st","2nd"... en los H2
CASAS_SUFIJO_NUM = {
    "1st":1,"2nd":2,"3rd":3,"4th":4,"5th":5,"6th":6,
    "7th":7,"8th":8,"9th":9,"10th":10,"11th":11,"12th":12,
}

def traducir(texto_en):
    if not texto_en or len(texto_en) < 20: return texto_en
    try:
        from deep_translator import GoogleTranslator
        tr = GoogleTranslator(source="en", target="es")
        MAX = 4500
        if len(texto_en) <= MAX:
            return tr.translate(texto_en) or texto_en
        parrafos = texto_en.split("\n\n")
        chunks, cur = [], ""
        for p in parrafos:
            if len(cur) + len(p) < MAX: cur += ("\n\n" if cur else "") + p
            else:
                if cur: chunks.append(cur)
                cur = p
        if cur: chunks.append(cur)
        partes = []
        for c in chunks:
            partes.append(tr.translate(c) or c)
            time.sleep(0.5)
        return "\n\n".join(partes)
    except Exception as e:
        log.warning(f"Traduccion fallida: {e}"); return texto_en

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(Path(SCHEMA).read_text(encoding="utf-8"))
    conn.commit(); return conn

def insertar(conn, row, dry_run=False):
    if dry_run:
        log.info(f"[DRY] {row['tipo']} | {row['clave']}"); return True
    sql = """INSERT OR IGNORE INTO interpretaciones
             (tipo,clave,autor,fuente_url,fuente_nombre,idioma_origen,
              texto_corto,texto_largo,calidad)
             VALUES (:tipo,:clave,:autor,:fuente_url,:fuente_nombre,:idioma_origen,
                     :texto_corto,:texto_largo,:calidad)"""
    cur = conn.execute(sql, row); conn.commit()
    if cur.rowcount > 0:
        log.info(f"  OK {row['tipo']} | {row['clave']}"); return True
    return False

def get_soup(url):
    time.sleep(DELAY_HTTP)
    r = requests.get(url, headers=HDR, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def _extraer_secciones(url, tipo, planeta_es, detectar_clave, conn, dry_run):
    log.info(f"Descargando: {url}")
    try: soup = get_soup(url)
    except Exception as e: log.error(f"Error: {e}"); return 0

    art = soup.select_one("article, div.entry-content, main")
    if not art: log.warning(f"Sin contenido: {url}"); return 0

    total = 0
    for h in art.find_all(["h2","h3"]):
        titulo = h.get_text(strip=True).lower()
        clave = detectar_clave(titulo, planeta_es)
        if not clave: continue

        parrafos = []
        for sib in h.find_next_siblings():
            if sib.name in ["h2","h3"]: break
            txt = sib.get_text(separator=" ", strip=True)
            if len(txt) > 40: parrafos.append(txt)
        if not parrafos: continue

        texto_en = "\n\n".join(parrafos)
        log.info(f"  Traduciendo {clave} ({len(texto_en)} chars)...")
        texto_es = traducir(texto_en)
        time.sleep(DELAY_TRADUC)

        row = {"tipo":tipo,"clave":clave,"autor":"Astrolibrary","fuente_url":url,
               "fuente_nombre":FUENTE_NOMBRE,"idioma_origen":"en",
               "texto_corto":texto_es[:300].rsplit(" ",1)[0]+"…",
               "texto_largo":texto_es,"calidad":FUENTE_CALIDAD}
        if insertar(conn, row, dry_run): total += 1
    return total

def scrape_signos(conn, planeta_en, dry_run=False):
    url = f"https://astrolibrary.org/interpretations/{planeta_en}/"
    planeta_es = PLANETAS_EN_ES[planeta_en]
    def detectar(titulo, pl):
        signo = next((s for s in SIGNOS_ORDER if s in titulo), None)
        return f"{pl}_{SIGNOS_EN_ES[signo]}" if signo else None
    return _extraer_secciones(url, "natal_planeta_signo", planeta_es, detectar, conn, dry_run)

def scrape_casas(conn, planeta_en, dry_run=False):
    url = f"https://astrolibrary.org/interpretations/{planeta_en}-house/"
    planeta_es = PLANETAS_EN_ES[planeta_en]
    def detectar(titulo, pl):
        # "sun in 1st house", "sun in 2nd house", etc.
        num = next((n for s,n in CASAS_SUFIJO_NUM.items() if s in titulo), None)
        return f"{pl}_CASA_{num}" if num else None
    return _extraer_secciones(url, "natal_planeta_casa", planeta_es, detectar, conn, dry_run)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tipo", default="all", choices=["signos","casas","all"])
    parser.add_argument("--planeta", default="")
    args = parser.parse_args()
    print(f"\nAstrolibrary | deep-translator | Tipo: {args.tipo}\n")

    conn = init_db()
    planetas = [args.planeta] if args.planeta else list(PLANETAS_EN_ES.keys())
    totales = {}

    if args.tipo in ("signos","all"):
        print("[1/2] SIGNOS...")
        n = sum(scrape_signos(conn, p, args.dry_run) for p in planetas)
        totales["natal_planeta_signo"] = n

    if args.tipo in ("casas","all"):
        print("\n[2/2] CASAS...")
        n = sum(scrape_casas(conn, p, args.dry_run) for p in planetas)
        totales["natal_planeta_casa"] = n

    print(f"\n{'='*50}")
    for tipo, n in totales.items():
        total = conn.execute("SELECT COUNT(*) FROM interpretaciones WHERE tipo=?",(tipo,)).fetchone()[0]
        print(f"  {tipo:<25} +{n:>3} | total BD: {total}")
    conn.close()

if __name__ == "__main__":
    main()
