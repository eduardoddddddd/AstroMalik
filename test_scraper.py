"""test_scraper.py — prueba rápida con 2 URLs reales"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from scraper.sources.cafe_astrology import (
    init_db, Fetcher, scrape_planeta_signo, stats_db,
    DB_PATH, URLS_PLANETA_SIGNO
)

# Solo 2 entradas para test rápido
URLS_PLANETA_SIGNO.clear()
URLS_PLANETA_SIGNO[("sun", "aries")]   = "https://cafeastrology.com/sun-in-aries.html"
URLS_PLANETA_SIGNO[("moon", "taurus")] = "https://cafeastrology.com/moon-in-taurus.html"

conn = init_db(DB_PATH)
f    = Fetcher(delay=1.5)
n    = scrape_planeta_signo(f, conn, dry_run=False)
print(f"\nInsertadas: {n}")
print("Cobertura BD:")
stats_db(conn)
conn.close()
