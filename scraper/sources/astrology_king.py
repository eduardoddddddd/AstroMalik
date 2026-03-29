"""
scraper/sources/astrology_king.py
Scraper para Astrology King.

Objetivo:
  - `aspecto_natal`: extraer la sección natal de páginas de aspectos.
  - `transito`: extraer la sección de tránsito de páginas de tránsitos.

Regla crítica de AstroMalik:
  - En la BD solo se guarda texto en castellano.
  - Si la traducción falla, la fila se descarta.

Uso:
    python scraper/sources/astrology_king.py [--dry-run] [--tipo TIPO] [--limit N]

Tipos:
    aspectos | transitos | all
"""

from __future__ import annotations

import argparse
import logging
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "backend" / "data" / "corpus.db"
SCHEMA = BASE_DIR / "corpus" / "schema.sql"

BASE_URL = "https://astrologyking.com"
ASPECTS_INDEX_URL = f"{BASE_URL}/aspects/"
TRANSITS_INDEX_URL = f"{BASE_URL}/transits/"
FUENTE_NOMBRE = "Astrology King"
AUTOR = "Jamie Partridge"
FUENTE_CALIDAD = 4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

DELAY = 0.35
MAX_REINTENTOS = 3
MAX_TRAD_CHARS = 3200

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("astrology_king")

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
    "chiron": "QUIRON",
    "ascendant": "ASC",
    "midheaven": "MC",
}

ASPECTOS_ES = {
    "conjunct": "CONJUNCION",
    "sextile": "SEXTIL",
    "square": "CUADRADO",
    "trine": "TRIGONO",
    "opposite": "OPOSICION",
    "quincunx": "QUINCUNCIO",
}

ORDEN_CUERPOS = [
    "SOL",
    "LUNA",
    "MERCURIO",
    "VENUS",
    "MARTE",
    "JUPITER",
    "SATURNO",
    "URANO",
    "NEPTUNO",
    "PLUTON",
    "QUIRON",
    "ASC",
    "MC",
]

PLANET_RE = r"(Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto|Chiron|Ascendant|Midheaven)"
ASPECT_RE = r"(Conjunct|Sextile|Square|Trine|Opposite|Quincunx)"
LINK_TEXT_RE = re.compile(rf"^(?P<p1>{PLANET_RE}) (?P<asp>{ASPECT_RE}) (?P<p2>{PLANET_RE})(?: Transit)?$", re.I)


class Fetcher:
    def __init__(self, delay: float = DELAY):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay

    def get_soup(self, url: str) -> BeautifulSoup | None:
        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                time.sleep(self.delay)
                response = self.session.get(url, timeout=30)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                response.encoding = "utf-8"
                return BeautifulSoup(response.text, "html.parser")
            except requests.RequestException as exc:
                log.warning(f"Intento {intento}/{MAX_REINTENTOS} fallido: {url} — {exc}")
                if intento < MAX_REINTENTOS:
                    time.sleep(self.delay * intento)
        return None


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(Path(SCHEMA).read_text(encoding="utf-8"))
    conn.commit()
    return conn


def insertar(conn: sqlite3.Connection, row: dict, dry_run: bool = False) -> bool:
    if dry_run:
        log.info(f"[DRY] {row['tipo']} | {row['clave']} | {row['fuente_url']}")
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
    return cursor.rowcount > 0


def stats_db(conn: sqlite3.Connection) -> None:
    for row in conn.execute(
        "SELECT tipo, fuente_nombre, COUNT(*) FROM interpretaciones "
        "GROUP BY tipo, fuente_nombre ORDER BY tipo, fuente_nombre"
    ):
        print(row)


def normalizar_espacios(texto: str) -> str:
    texto = texto.replace("\xa0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def limpiar_parrafo(texto: str) -> str:
    texto = normalizar_espacios(texto)
    if not texto:
        return ""
    if texto.startswith("Home /"):
        return ""
    if re.match(r"^[A-Z][a-z]+ [a-z]+ [A-Z][a-z]+ maximum orb", texto):
        return ""
    if re.fullmatch(r"(?:[A-Z][a-z]{2,9}\s+\d{1,2},?\s+\d{4}\s*){1,20}", texto):
        return ""
    return texto


def es_heading_natal(texto: str) -> bool:
    lower = texto.lower()
    return " natal" in f" {lower} " or lower.endswith(" natal")


def es_heading_transit(texto: str) -> bool:
    lower = texto.lower()
    return " transit" in f" {lower} " or lower.endswith(" transit")


def es_heading_corte(texto: str) -> bool:
    lower = texto.lower().strip()
    if "celebrit" in lower:
        return True
    if "famous people" in lower:
        return True
    if "references" in lower:
        return True
    if "sources" in lower:
        return True
    if re.search(r"\b(19|20)\d{2}\b", lower):
        return True
    return False


def obtener_contenedor(soup: BeautifulSoup) -> Tag | None:
    for selector in ["article", "div.entry-content", "main", "body"]:
        node = soup.select_one(selector)
        if node:
            return node
    return None


def extraer_bloque(contenedor: Tag, modo: str) -> str:
    nodos = contenedor.find_all(["h2", "h3", "p", "li"])
    piezas: list[str] = []
    recogiendo = modo == "transito"
    tiene_heading_natal = False
    tiene_heading_transit = False

    for nodo in nodos:
        texto = nodo.get_text(" ", strip=True)
        if not texto:
            continue

        if nodo.name in {"h2", "h3"}:
            if es_heading_natal(texto):
                tiene_heading_natal = True
                if modo == "natal":
                    recogiendo = True
                    piezas = []
                    continue
                if modo == "transito" and recogiendo:
                    break
            if es_heading_transit(texto):
                tiene_heading_transit = True
                if modo == "transito":
                    recogiendo = True
                    piezas = []
                    continue
                if modo == "natal":
                    break
            if es_heading_corte(texto) and recogiendo:
                break
            continue

        texto = limpiar_parrafo(texto)
        if not texto:
            continue

        if modo == "natal":
            if not tiene_heading_natal:
                if tiene_heading_transit:
                    break
                piezas.append(texto)
            elif recogiendo:
                piezas.append(texto)
        else:
            if tiene_heading_transit:
                if recogiendo:
                    piezas.append(texto)
            elif recogiendo:
                piezas.append(texto)

    if modo == "natal" and not tiene_heading_natal:
        resultado = []
        for pieza in piezas:
            lower = pieza.lower()
            if " transit " in f" {lower} " and len(resultado) >= 2:
                break
            resultado.append(pieza)
        piezas = resultado

    if len(piezas) > 1:
        return normalizar_espacios("\n\n".join(piezas))
    return ""


def traducir_es_obligatorio(texto: str) -> str:
    from deep_translator import GoogleTranslator

    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    if not parrafos:
        return ""

    trozos: list[str] = []
    actual: list[str] = []
    longitud = 0

    for parrafo in parrafos:
        incremento = len(parrafo) + (2 if actual else 0)
        if actual and longitud + incremento > MAX_TRAD_CHARS:
            trozos.append("\n\n".join(actual))
            actual = [parrafo]
            longitud = len(parrafo)
        else:
            actual.append(parrafo)
            longitud += incremento
    if actual:
        trozos.append("\n\n".join(actual))

    traductor = GoogleTranslator(source="en", target="es")
    traducidos = []
    for trozo in trozos:
        traducido = traductor.translate(trozo)
        if not traducido:
            raise RuntimeError("Respuesta vacía del traductor")
        traducidos.append(traducido)

    return normalizar_espacios("\n\n".join(traducidos))


def resumen(texto: str, limite: int = 300) -> str:
    plano = normalizar_espacios(texto.replace("\n", " "))
    if len(plano) <= limite:
        return plano
    corte = plano[:limite]
    if " " in corte:
        corte = corte.rsplit(" ", 1)[0]
    return corte + "…"


def ordenar_canonico(p1: str, p2: str) -> tuple[str, str]:
    def idx(valor: str) -> int:
        return ORDEN_CUERPOS.index(valor) if valor in ORDEN_CUERPOS else 999

    return (p1, p2) if idx(p1) <= idx(p2) else (p2, p1)


def parsear_link_aspecto(texto_link: str) -> tuple[str, str, str] | None:
    match = LINK_TEXT_RE.match(texto_link.strip())
    if not match:
        return None

    p1 = PLANETAS_ES[match.group("p1").lower()]
    p2 = PLANETAS_ES[match.group("p2").lower()]
    aspecto = ASPECTOS_ES[match.group("asp").lower()]
    return p1, p2, aspecto


def descubrir_links_indice(fetcher: Fetcher, index_url: str) -> list[dict]:
    soup = fetcher.get_soup(index_url)
    if not soup:
        raise RuntimeError(f"No se pudo leer índice: {index_url}")

    links = []
    vistos = set()

    for anchor in soup.find_all("a", href=True):
        texto = anchor.get_text(" ", strip=True)
        parsed = parsear_link_aspecto(texto)
        if not parsed:
            continue

        href = urljoin(index_url, anchor["href"].strip())
        if not href.startswith(BASE_URL):
            continue

        p1, p2, aspecto = parsed
        key = (href, p1, p2, aspecto)
        if key in vistos:
            continue
        vistos.add(key)
        links.append(
            {
                "url": href,
                "p1": p1,
                "p2": p2,
                "aspecto": aspecto,
                "texto": texto,
            }
        )

    return links


def preparar_row(tipo: str, clave: str, url: str, texto_en: str) -> dict | None:
    try:
        texto_es = traducir_es_obligatorio(texto_en)
    except Exception as exc:
        log.warning(f"Traducción fallida; se descarta {clave}: {exc}")
        return None

    if not texto_es or len(texto_es) < 120:
        log.warning(f"Texto traducido insuficiente; se descarta {clave}")
        return None

    return {
        "tipo": tipo,
        "clave": clave,
        "autor": AUTOR,
        "fuente_url": url,
        "fuente_nombre": FUENTE_NOMBRE,
        "idioma_origen": "en",
        "texto_corto": resumen(texto_es),
        "texto_largo": texto_es,
        "calidad": FUENTE_CALIDAD,
    }


def scrape_aspectos(fetcher: Fetcher, conn: sqlite3.Connection, dry_run: bool = False, limit: int | None = None) -> int:
    total = 0
    vistos_clave = set()
    links = descubrir_links_indice(fetcher, ASPECTS_INDEX_URL)

    for item in links[:limit] if limit else links:
        p1, p2 = ordenar_canonico(item["p1"], item["p2"])
        clave = f"{p1}_{p2}_{item['aspecto']}"
        if clave in vistos_clave:
            continue
        vistos_clave.add(clave)

        soup = fetcher.get_soup(item["url"])
        if not soup:
            continue

        contenedor = obtener_contenedor(soup)
        if not contenedor:
            continue

        texto_en = extraer_bloque(contenedor, "natal")
        if not texto_en:
            log.warning(f"Sin bloque natal: {item['url']}")
            continue

        row = preparar_row("aspecto_natal", clave, item["url"], texto_en)
        if row and insertar(conn, row, dry_run=dry_run):
            total += 1
            log.info(f"OK aspecto_natal | {clave}")

    return total


def scrape_transitos(fetcher: Fetcher, conn: sqlite3.Connection, dry_run: bool = False, limit: int | None = None) -> int:
    total = 0
    vistos_clave = set()
    links = descubrir_links_indice(fetcher, TRANSITS_INDEX_URL)

    for item in links[:limit] if limit else links:
        clave = f"{item['p1']}_tr_{item['p2']}_{item['aspecto']}"
        if clave in vistos_clave:
            continue
        vistos_clave.add(clave)

        soup = fetcher.get_soup(item["url"])
        if not soup:
            continue

        contenedor = obtener_contenedor(soup)
        if not contenedor:
            continue

        texto_en = extraer_bloque(contenedor, "transito")
        if not texto_en:
            log.warning(f"Sin bloque tránsito: {item['url']}")
            continue

        row = preparar_row("transito", clave, item["url"], texto_en)
        if row and insertar(conn, row, dry_run=dry_run):
            total += 1
            log.info(f"OK transito | {clave}")

    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraper de Astrology King")
    parser.add_argument("--tipo", choices=["aspectos", "transitos", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delay", type=float, default=DELAY)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    fetcher = Fetcher(delay=args.delay)
    conn = init_db(DB_PATH)

    total = 0
    if args.tipo in {"aspectos", "all"}:
        total += scrape_aspectos(fetcher, conn, dry_run=args.dry_run, limit=args.limit)
    if args.tipo in {"transitos", "all"}:
        total += scrape_transitos(fetcher, conn, dry_run=args.dry_run, limit=args.limit)

    print(f"\nInsertadas: {total}")
    stats_db(conn)
    conn.close()


if __name__ == "__main__":
    main()
