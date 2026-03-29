# -*- coding: utf-8 -*-
"""
scraper/sources/grupo_venus.py
Scraper para GrupoVenus.com — textos en castellano, estructura ASP directa.

URL patrón: /sacainter.asp?tabla=TABLA&cla=CLAVE
  tabla=transiaw  → tránsitos (planetas lentos sobre puntos natales)
  tabla=tracompu  → sinastría (aspectos entre dos cartas)
  tabla=starsolu  → aspectos natales Sol + planetas

La clave 'cla' codifica: PLANETA(3) + ASPECTO(3) + PUNTO_NATAL(3+)
  Planetas:  JUP SAT URA NEP PLU MAR VEN MER SOL LUN
  Aspectos:  CJC OPO CUA TRI SEX
  Puntos:    SOL LUN MER VEN MAR JUP SAT URA NEP PLU ASC MC+

Texto en castellano nativo → NO necesita traducción.

Uso:
    python scraper/sources/grupo_venus.py [--dry-run] [--tipo TIPO]
Tipos: transitos | sinastria | aspectos | all (default)
"""

import sqlite3, time, re, argparse, logging
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE_DIR      = Path(__file__).resolve().parents[2]
DB_PATH       = BASE_DIR / "backend" / "data" / "corpus.db"
SCHEMA        = BASE_DIR / "corpus" / "schema.sql"
BASE_URL      = "https://grupovenus.com"
FUENTE_NOMBRE = "Grupo Venus"
FUENTE_CALIDAD = 4

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
           "Accept-Language": "es-ES,es;q=0.9"}
DELAY   = 1.0
MAX_REINTENTOS = 3

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("grupo_venus")

# ── Decodificador de claves GrupoVenus ───────────────────────────────────────

# Códigos de 3 letras → nombres en castellano
DECODE_PLANETA = {
    "JUP": "JUPITER", "SAT": "SATURNO", "URA": "URANO",
    "NEP": "NEPTUNO", "PLU": "PLUTON",  "MAR": "MARTE",
    "VEN": "VENUS",   "MER": "MERCURIO","SOL": "SOL",
    "LUN": "LUNA",    "CHI": "QUIRON",
}
DECODE_ASPECTO = {
    "CJC": "CONJUNCION", "OPO": "OPOSICION", "CUA": "CUADRADO",
    "TRI": "TRIGONO",    "SEX": "SEXTIL",
}
DECODE_PUNTO = {
    "SOL": "SOL",     "LUN": "LUNA",    "MER": "MERCURIO",
    "VEN": "VENUS",   "MAR": "MARTE",   "JUP": "JUPITER",
    "SAT": "SATURNO", "URA": "URANO",   "NEP": "NEPTUNO",
    "PLU": "PLUTON",  "ASC": "ASC",     "MC+": "MC",
    "CHI": "QUIRON",
}

def decodificar_clave_gv(cla: str, tabla: str) -> dict | None:
    """
    Decodifica la clave cruda de GrupoVenus al formato estándar AstroMalik.
    Devuelve dict con {tipo, clave_astro, planeta, aspecto, punto}
    o None si no se puede decodificar.

    Ejemplos:
      tabla=transiaw, cla=JUPCJCASC → transito, JUPITER_tr_ASC_CONJUNCION
      tabla=tracompu, cla=SOLTRINEP → sinastria, SYN_SOL_NEPTUNO_TRIGONO
      tabla=starsolu, cla=SOLCJCLUN → aspecto_natal, SOL_LUNA_CONJUNCION
    """
    cla = cla.strip().upper()

    # Formato: PLANETA(3) + ASPECTO(3) + PUNTO(3+)
    if len(cla) < 9:
        return None

    cod_planeta = cla[0:3]
    cod_aspecto = cla[3:6]
    cod_punto   = cla[6:]    # puede ser 3 o 4 chars (MC+ tiene 3)

    planeta = DECODE_PLANETA.get(cod_planeta)
    aspecto = DECODE_ASPECTO.get(cod_aspecto)
    punto   = DECODE_PUNTO.get(cod_punto)

    if not planeta or not aspecto or not punto:
        log.debug(f"No decodificado: {cla} (p={cod_planeta}, a={cod_aspecto}, pt={cod_punto})")
        return None

    if tabla == "transiaw":
        tipo  = "transito"
        clave = f"{planeta}_tr_{punto}_{aspecto}"
    elif tabla == "tracompu":
        tipo  = "sinastria"
        # orden canónico: primero el planeta "mayor"
        clave = f"SYN_{planeta}_{punto}_{aspecto}"
    elif tabla == "starsolu":
        tipo  = "aspecto_natal"
        # orden canónico
        orden = ["SOL","LUNA","MERCURIO","VENUS","MARTE","JUPITER",
                 "SATURNO","URANO","NEPTUNO","PLUTON"]
        p1, p2 = planeta, punto
        idx1 = orden.index(p1) if p1 in orden else 99
        idx2 = orden.index(p2) if p2 in orden else 99
        if idx1 > idx2:
            p1, p2 = p2, p1
        clave = f"{p1}_{p2}_{aspecto}"
    else:
        return None

    return {"tipo": tipo, "clave": clave, "planeta": planeta,
            "aspecto": aspecto, "punto": punto, "tabla": tabla}

# ── Generador de todas las URLs de GrupoVenus ────────────────────────────────

PLANETAS_TR  = ["JUP","SAT","URA","NEP","PLU","MAR"]  # planetas tránsito
PLANETAS_NAT = ["SOL","LUN","MER","VEN","MAR","JUP","SAT","URA","NEP","PLU","ASC","MC+"]
PLANETAS_SYN = ["SOL","LUN","MER","VEN","MAR","JUP","SAT","URA","NEP","PLU"]
ASPECTOS_COD = ["CJC","OPO","CUA","TRI","SEX"]

def generar_urls_transitos():
    """Genera todas las URLs de tránsitos: planetas lentos × aspectos × puntos natales."""
    urls = {}
    for planeta in PLANETAS_TR:
        for asp in ASPECTOS_COD:
            for punto in PLANETAS_NAT:
                cla = f"{planeta}{asp}{punto}"
                url = f"{BASE_URL}/sacainter.asp?tabla=transiaw&cla={cla}"
                urls[cla] = url
    return urls

def generar_urls_sinastria():
    """Genera URLs de sinastría."""
    urls = {}
    for p1 in PLANETAS_SYN:
        for asp in ASPECTOS_COD:
            for p2 in PLANETAS_SYN:
                if p1 != p2:
                    cla = f"{p1}{asp}{p2}"
                    url = f"{BASE_URL}/sacainter.asp?tabla=tracompu&cla={cla}"
                    urls[cla] = url
    return urls

def generar_urls_aspectos():
    """Genera URLs de aspectos natales (tabla starsolu)."""
    urls = {}
    planetas = ["SOL","LUN","MER","VEN","MAR","JUP","SAT","URA","NEP","PLU"]
    for p1 in planetas:
        for asp in ASPECTOS_COD:
            for p2 in planetas:
                if p1 != p2:
                    cla = f"{p1}{asp}{p2}"
                    url = f"{BASE_URL}/sacainter.asp?tabla=starsolu&cla={cla}"
                    urls[cla] = url
    return urls


# ── Extractor HTML de GrupoVenus ─────────────────────────────────────────────

class FetcherGV:
    def __init__(self, delay=DELAY):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay

    def get(self, url):
        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                time.sleep(self.delay)
                r = self.session.get(url, timeout=20)
                if r.status_code == 404: return None
                r.raise_for_status()
                r.encoding = r.apparent_encoding or "iso-8859-1"  # GrupoVenus usa latin-1
                return BeautifulSoup(r.text, "html.parser")
            except requests.RequestException as e:
                log.warning(f"Intento {intento}: {url} — {e}")
                if intento < MAX_REINTENTOS:
                    time.sleep(self.delay * intento)
        return None


def extraer_texto_gv(soup, url):
    """
    GrupoVenus tiene estructura ASP clásica.
    El contenido interpretativo está en el body principal.
    """
    if not soup: return "", ""

    # GrupoVenus usa tablas HTML antiguas — el texto está en <td>
    # Eliminar nav, headers, footers
    for tag in soup.find_all(["script","style","nav","form"]):
        tag.decompose()

    # Buscar el bloque de texto principal
    # La estructura típica: título en <b> o <h2>, texto en párrafos o <td>
    contenido = soup.find("body")
    if not contenido:
        return "", ""

    texto = contenido.get_text(separator="\n", strip=True)

    # Limpiar líneas muy cortas (navegación, etc.)
    lineas = [l.strip() for l in texto.split("\n")
              if len(l.strip()) > 30]
    texto_largo = "\n\n".join(lineas)
    if texto_largo and "starlight solutions" in texto_largo.lower():
        log.warning(f"  contenido externo/no valido detectado: {url}")
        return "", ""

    if not texto_largo:
        return "", ""

    texto_corto = " ".join(lineas[:3])[:300].rsplit(" ",1)[0] + "…"
    return texto_largo, texto_corto

# ── BD helpers (reutiliza mismas funciones que cafe_astrology) ────────────────

def init_db(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    schema_sql = Path(SCHEMA).read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
    return conn

def insertar(conn, row, dry_run=False):
    if dry_run:
        log.info(f"[DRY] {row['tipo']} | {row['clave']}")
        return True
    sql = """INSERT OR IGNORE INTO interpretaciones
             (tipo,clave,autor,fuente_url,fuente_nombre,idioma_origen,
              texto_corto,texto_largo,calidad)
             VALUES (:tipo,:clave,:autor,:fuente_url,:fuente_nombre,:idioma_origen,
                     :texto_corto,:texto_largo,:calidad)"""
    cur = conn.execute(sql, row)
    conn.commit()
    if cur.rowcount > 0:
        log.info(f"  OK {row['tipo']} | {row['clave']}")
        return True
    log.debug(f"  ya existe: {row['clave']}")
    return False

def stats_db(conn):
    for row in conn.execute("SELECT tipo, COUNT(*) FROM interpretaciones GROUP BY tipo"):
        print(f"  {row[0]:<25} {row[1]:>4} entradas")


# ── Scraper principal por tabla ───────────────────────────────────────────────

def scrape_tabla(fetcher, conn, tabla, urls_dict, dry_run=False):
    total = 0
    for cla, url in urls_dict.items():
        decoded = decodificar_clave_gv(cla, tabla)
        if not decoded:
            log.debug(f"  skip no-decodificado: {cla}")
            continue

        log.info(f"-> {decoded['clave']}  {url}")
        soup = fetcher.get(url)
        if not soup:
            continue

        texto_largo, texto_corto = extraer_texto_gv(soup, url)
        if not texto_largo or len(texto_largo) < 80:
            log.warning(f"  texto vacio/corto: {url}")
            continue

        row = {
            "tipo":          decoded["tipo"],
            "clave":         decoded["clave"],
            "autor":         "Grupo Venus",
            "fuente_url":    url,
            "fuente_nombre": FUENTE_NOMBRE,
            "idioma_origen": "es",          # nativo castellano, sin traduccion
            "texto_corto":   texto_corto,
            "texto_largo":   texto_largo,
            "calidad":       FUENTE_CALIDAD,
        }
        if insertar(conn, row, dry_run):
            total += 1
    return total


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Scraper Grupo Venus -> AstroMalik corpus.db")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tipo", default="all",
                        choices=["transitos","sinastria","aspectos","all"])
    parser.add_argument("--delay", type=float, default=DELAY)
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  AstroMalik - Scraper Grupo Venus")
    print(f"  Modo: {'DRY-RUN' if args.dry_run else 'REAL'} | Seccion: {args.tipo}")
    print(f"{'='*55}\n")

    conn    = init_db(DB_PATH)
    fetcher = FetcherGV(delay=args.delay)
    totales = {}

    if args.tipo in ("transitos","all"):
        print("[1/3] Transitos...")
        urls = generar_urls_transitos()
        print(f"  Combinaciones a probar: {len(urls)}")
        totales["transito"] = scrape_tabla(fetcher, conn, "transiaw", urls, args.dry_run)

    if args.tipo in ("sinastria","all"):
        print("\n[2/3] Sinastria...")
        urls = generar_urls_sinastria()
        print(f"  Combinaciones a probar: {len(urls)}")
        totales["sinastria"] = scrape_tabla(fetcher, conn, "tracompu", urls, args.dry_run)

    if args.tipo in ("aspectos","all"):
        print("\n[3/3] Aspectos natales...")
        urls = generar_urls_aspectos()
        print(f"  Combinaciones a probar: {len(urls)}")
        totales["aspecto_natal"] = scrape_tabla(fetcher, conn, "starsolu", urls, args.dry_run)

    print(f"\n{'='*55}")
    print("  RESUMEN")
    print(f"{'='*55}")
    for tipo, n in totales.items():
        print(f"  {tipo:<25} {n:>4} nuevas entradas")
    print("\n  Cobertura total BD:")
    stats_db(conn)
    conn.close()

if __name__ == "__main__":
    main()
