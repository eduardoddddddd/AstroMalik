# -*- coding: utf-8 -*-
import sqlite3, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

db = r"C:\Users\Edu\AstroMalik\backend\data\corpus.db"
if not os.path.exists(db):
    print("corpus.db NO ENCONTRADO en", db)
    sys.exit(1)

conn = sqlite3.connect(db)
print("=== ESTADO CORPUS.DB ===\n")
rows = conn.execute(
    "SELECT tipo, fuente_nombre, COUNT(*) FROM interpretaciones "
    "GROUP BY tipo, fuente_nombre ORDER BY tipo, fuente_nombre"
).fetchall()
for r in rows:
    print(f"  {r[0]:<25} {r[1]:<20} {r[2]:>4} filas")

total = conn.execute("SELECT COUNT(*) FROM interpretaciones").fetchone()[0]
print(f"\n  TOTAL: {total} filas")

# Muestra de 1 fila por tipo
print("\n=== MUESTRA 1 FILA POR TIPO ===")
for tipo in ["transito","sinastria","aspecto_natal","natal_planeta_signo","natal_planeta_casa"]:
    row = conn.execute(
        "SELECT clave, fuente_nombre, LENGTH(texto_largo), texto_largo "
        "FROM interpretaciones WHERE tipo=? LIMIT 1", (tipo,)
    ).fetchone()
    if row:
        print(f"\n  [{tipo}]  clave={row[0]}  fuente={row[1]}  chars={row[2]}")
        print(f"  {row[3][:200]}...")
    else:
        print(f"\n  [{tipo}]  -- SIN DATOS --")

conn.close()
