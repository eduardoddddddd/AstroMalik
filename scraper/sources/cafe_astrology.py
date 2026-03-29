"""
scraper/sources/cafe_astrology.py
Scraper para Café Astrology.

Estado actual:
  - aspecto_natal: activo, con URLs reales extraídas del sitemap
  - natal_planeta_signo: pausado hasta aislar URLs canónicas 1:1
  - natal_planeta_casa: pausado hasta aislar URLs canónicas 1:1
  - transito: pausado; el sitemap actual devuelve sobre todo artículos generales

Uso:
    python scraper/sources/cafe_astrology.py [--dry-run] [--tipo TIPO]
"""

import argparse
import json
import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "backend" / "data" / "corpus.db"
SCHEMA = BASE_DIR / "corpus" / "schema.sql"
SITEMAP_JSON = BASE_DIR / "scraper" / "cafe_astrology_urls.json"

FUENTE_NOMBRE = "Café Astrology"
FUENTE_CALIDAD = 4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

DELAY_ENTRE_PETICIONES = 1.2
MAX_REINTENTOS = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("cafe_astrology")

PLANETAS_ES = {
    "sun": "SOL",
    "moon": "LUNA",
    "mercury": "MERCURIO",
    "venus": "VENUS",
    "mars": "MARTE",
    "jupiter": "JUPITER",
    "saturn": "SATURNO",
    "uranus": "URANO",
    "neptune": "NEPTUNO",
    "pluto": "PLUTON",
    "north-node": "NODO_NORTE",
    "north node": "NODO_NORTE",
    "south-node": "NODO_SUR",
    "south node": "NODO_SUR",
    "ascendant": "ASC",
    "midheaven": "MC",
    "chiron": "QUIRON",
}

ASPECTOS_ES = {
    "conjunct": "CONJUNCION",
    "conjunction": "CONJUNCION",
    "opposite": "OPOSICION",
    "opposition": "OPOSICION",
    "square": "CUADRADO",
    "trine": "TRIGONO",
    "sextile": "SEXTIL",
    "quincunx": "QUINCUNCIO",
}

PLANETA_SLUG = r"(sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto|chiron|north-node|south-node)"
RE_ASPECT_URL = re.compile(
    rf"^https://cafeastrology\.com/aspects/"
    rf"(?P<p1>{PLANETA_SLUG})-(?P<asp>conjunct|opposite|square|trine|sextile|quincunx)-(?P<p2>{PLANETA_SLUG})\.html$"
)


class Fetcher:
    def __init__(self, delay: float = DELAY_ENTRE_PETICIONES):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay

    def get(self, url: str) -> Optional[BeautifulSoup]:
        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                time.sleep(self.delay)
                r = self.session.get(url, timeout=20)
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")
                title = soup.title.get_text(" ", strip=True).lower() if soup.title else ""
                if "page not found" in title or title.startswith("404"):
                    return None
                return soup
            except requests.RequestException as e:
                log.warning(f"Intento {intento}/{MAX_REINTENTOS} fallido: {url} — {e}")
                if intento < MAX_REINTENTOS:
                    time.sleep(self.delay * intento)
        log.error(f"Descartado tras {MAX_REINTENTOS} reintentos: {url}")
        return None


def traducir_es(texto: str) -> tuple[str, str]:
    if not texto or len(texto) < 20:
        return texto, "es"
    try:
        from deep_translator import GoogleTranslator
        traductor = GoogleTranslator(source="en", target="es")
        trozos = []
        actual = []
        longitud = 0
        for parrafo in texto.split("\n\n"):
            candidato = len(parrafo) + (2 if actual else 0)
            if actual and longitud + candidato > 3500:
                trozos.append("\n\n".join(actual))
                actual = [parrafo]
                longitud = len(parrafo)
            else:
                actual.append(parrafo)
                longitud += candidato
        if actual:
            trozos.append("\n\n".join(actual))

        traducidos = [traductor.translate(trozo) or trozo for trozo in trozos]
        return "\n\n".join(traducidos), "en"
    except Exception as e:
        log.warning(f"Traducción fallida: {e}. Se guarda en inglés.")
        return texto, "en"


def extraer_texto_pagina(soup: BeautifulSoup, url: str) -> tuple[str, str]:
    contenido = None
    for selector in [
        "div.entry-content",
        "div#content",
        "div.post-content",
        "article",
        "div.page-content",
    ]:
        contenido = soup.select_one(selector)
        if contenido:
            break

    if not contenido:
        log.warning(f"No se encontró contenido en: {url}")
        return "", ""

    for tag in contenido.select("nav, aside, script, style, form, .sharedaddy, .wpcnt, .widget, .sidebar, h1"):
        tag.decompose()

    parrafos = [
        p.get_text(separator=" ", strip=True)
        for p in contenido.find_all(["p", "h2", "h3", "li"])
        if len(p.get_text(strip=True)) > 40
    ]
    if not parrafos:
        return "", ""

    texto_largo = "\n\n".join(parrafos)
    texto_corto = " ".join(parrafos[:2])[:300].rsplit(" ", 1)[0] + "…"
    return texto_largo, texto_corto


def limpiar_texto(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"[^\w\s\.,;:¿?¡!()\-\n\"\'áéíóúüñÁÉÍÓÚÜÑ]", " ", texto)
    return texto.strip()


def recortar_a_natal(texto: str) -> str:
    """Conserva la introducción y la parte natal, cortando tránsito/sinastría/composite."""
    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    if not parrafos:
        return texto

    resultado = []
    for parrafo in parrafos:
        lower = parrafo.lower()
        if resultado and (
            lower.startswith("when transiting ")
            or lower.startswith("transits to the natal chart")
            or lower.startswith("this type of aspect can be considered astrological weather")
            or lower.startswith("when ") and " in one chart forms " in lower
            or lower.startswith("the composite chart")
            or lower.startswith("key traits")
            or lower.startswith("see also ")
            or lower.startswith("dates with planetary positions")
            or lower.startswith("enters ")
        ):
            break
        resultado.append(parrafo)

    if len(resultado) >= 2:
        while resultado and len("\n\n".join(resultado)) > 4500:
            resultado.pop()
        return "\n\n".join(resultado)
    return texto


def cargar_urls_sitemap(tipo: str) -> list[str]:
    if not SITEMAP_JSON.exists():
        raise FileNotFoundError(
            f"No existe {SITEMAP_JSON}. Ejecuta antes: python scraper/parse_sitemap.py"
        )
    data = json.loads(SITEMAP_JSON.read_text(encoding="utf-8"))
    return data.get("clasificadas", {}).get(tipo, [])


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    schema_sql = Path(SCHEMA).read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
    log.info(f"BD inicializada: {db_path}")
    return conn


def insertar(conn: sqlite3.Connection, row: dict, dry_run: bool = False) -> bool:
    if dry_run:
        log.info(f"[DRY-RUN] {row['tipo']} | {row['clave']} | {row['fuente_nombre']}")
        return True

    sql = """
        INSERT OR IGNORE INTO interpretaciones
            (tipo, clave, autor, fuente_url, fuente_nombre,
             idioma_origen, texto_corto, texto_largo, calidad)
        VALUES
            (:tipo, :clave, :autor, :fuente_url, :fuente_nombre,
             :idioma_origen, :texto_corto, :texto_largo, :calidad)
    """
    cursor = conn.execute(sql, row)
    conn.commit()
    if cursor.rowcount > 0:
        log.info(f"  ✓ {row['tipo']} | {row['clave']}")
        return True
    return False


def stats_db(conn: sqlite3.Connection):
    for row in conn.execute("SELECT tipo, COUNT(*) FROM interpretaciones GROUP BY tipo"):
        print(f"  {row[0]:<25} {row[1]:>4} entradas")


def scrape_planeta_signo(fetcher: Fetcher, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    log.warning("natal_planeta_signo desactivado: el sitemap mezcla mucho ruido editorial")
    return 0


def scrape_planeta_casa(fetcher: Fetcher, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    log.warning("natal_planeta_casa desactivado: aún no hay URLs 1:1 fiables")
    return 0


def _orden_canonico(p1: str, p2: str) -> tuple[str, str]:
    orden = ["SOL", "LUNA", "MERCURIO", "VENUS", "MARTE", "JUPITER", "SATURNO", "URANO", "NEPTUNO", "PLUTON"]

    def idx(p):
        return orden.index(p) if p in orden else 99

    return (p1, p2) if idx(p1) <= idx(p2) else (p2, p1)


def scrape_aspectos(fetcher: Fetcher, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    total = 0
    vistos = set()

    for url in cargar_urls_sitemap("aspecto_natal"):
        match = RE_ASPECT_URL.match(url)
        if not match:
            continue

        p1_en = match.group("p1")
        asp_en = match.group("asp")
        p2_en = match.group("p2")

        p1_es = PLANETAS_ES.get(p1_en, p1_en.upper())
        p2_es = PLANETAS_ES.get(p2_en, p2_en.upper())
        asp_es = ASPECTOS_ES.get(asp_en, asp_en.upper())
        if p1_es == p2_es:
            continue

        p1_es, p2_es = _orden_canonico(p1_es, p2_es)
        clave = f"{p1_es}_{p2_es}_{asp_es}"
        if clave in vistos:
            continue
        vistos.add(clave)

        log.info(f"→ {clave}  {url}")
        soup = fetcher.get(url)
        if not soup:
            continue

        texto_largo, texto_corto = extraer_texto_pagina(soup, url)
        if not texto_largo:
            continue
        texto_largo = recortar_a_natal(texto_largo)
        texto_corto = " ".join(texto_largo.split("\n\n")[:2])[:300].rsplit(" ", 1)[0] + "…"

        texto_largo, idioma = traducir_es(limpiar_texto(texto_largo))
        texto_corto, _ = traducir_es(limpiar_texto(texto_corto))

        row = {
            "tipo": "aspecto_natal",
            "clave": clave,
            "autor": "Cafe Astrology",
            "fuente_url": url,
            "fuente_nombre": FUENTE_NOMBRE,
            "idioma_origen": idioma,
            "texto_corto": texto_corto,
            "texto_largo": texto_largo,
            "calidad": FUENTE_CALIDAD,
        }
        if insertar(conn, row, dry_run):
            total += 1
    return total


def scrape_transitos(fetcher: Fetcher, conn: sqlite3.Connection, dry_run: bool = False) -> int:
    log.warning("transito desactivado en Café Astrology: las URLs actuales no forman matriz exacta")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Scraper Café Astrology → AstroMalik corpus.db")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en BD ni traducir")
    parser.add_argument(
        "--tipo",
        default="all",
        choices=["natal_signos", "natal_casas", "aspectos", "transitos", "all"],
        help="Sección a scrapear (default: all)",
    )
    parser.add_argument("--delay", type=float, default=DELAY_ENTRE_PETICIONES, help="Segundos entre peticiones")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print("  AstroMalik — Scraper Café Astrology")
    print(f"  Modo: {'DRY-RUN' if args.dry_run else 'REAL'} | Sección: {args.tipo}")
    print(f"  BD: {DB_PATH}")
    print(f"{'=' * 60}\n")

    conn = init_db(DB_PATH)
    fetcher = Fetcher(delay=args.delay)
    totales = {}

    if args.tipo in ("natal_signos", "all"):
        print("\n[1/4] Planetas en signos...")
        totales["natal_planeta_signo"] = scrape_planeta_signo(fetcher, conn, args.dry_run)

    if args.tipo in ("natal_casas", "all"):
        print("\n[2/4] Planetas en casas...")
        totales["natal_planeta_casa"] = scrape_planeta_casa(fetcher, conn, args.dry_run)

    if args.tipo in ("aspectos", "all"):
        print("\n[3/4] Aspectos natales...")
        totales["aspecto_natal"] = scrape_aspectos(fetcher, conn, args.dry_run)

    if args.tipo in ("transitos", "all"):
        print("\n[4/4] Tránsitos...")
        totales["transito"] = scrape_transitos(fetcher, conn, args.dry_run)

    print(f"\n{'=' * 60}")
    print("  RESUMEN")
    print(f"{'=' * 60}")
    for tipo, n in totales.items():
        print(f"  {tipo:<30} {n:>4} nuevas entradas")

    print("\n  Cobertura total en BD:")
    stats_db(conn)
    conn.close()
    print(f"\n  corpus.db guardado en: {DB_PATH}\n")


if __name__ == "__main__":
    main()
