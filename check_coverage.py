# -*- coding: utf-8 -*-
"""Analiza cobertura real del corpus vs máximo teórico."""
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

conn = sqlite3.connect(r"C:\Users\Edu\AstroMalik\backend\data\corpus.db")

PLANETAS  = ["SOL","LUNA","MERCURIO","VENUS","MARTE","JUPITER","SATURNO","URANO","NEPTUNO","PLUTON"]
ASPECTOS  = ["CONJUNCION","OPOSICION","CUADRADO","TRIGONO","SEXTIL"]
TR_SLOW   = ["JUPITER","SATURNO","URANO","NEPTUNO","PLUTON","MARTE"]
NAT_PUNTOS= ["SOL","LUNA","MERCURIO","VENUS","MARTE","JUPITER","SATURNO","URANO","NEPTUNO","PLUTON","ASC","MC"]

# ── TRÁNSITOS ─────────────────────────────────────────────────────────────────
print("=== TRÁNSITOS ===")
# Máximo teórico: planetas lentos × aspectos × puntos natales
teorico_tr = set()
for p in TR_SLOW:
    for a in ASPECTOS:
        for n in NAT_PUNTOS:
            if p != n:
                teorico_tr.add(f"{p}_tr_{n}_{a}")

reales_tr = set(r[0] for r in conn.execute(
    "SELECT DISTINCT clave FROM interpretaciones WHERE tipo='transito'"))

falta_tr = teorico_tr - reales_tr
tiene_tr = teorico_tr & reales_tr

print(f"  Teórico:   {len(teorico_tr)}")
print(f"  Cubierto:  {len(tiene_tr)}  ({100*len(tiene_tr)//len(teorico_tr)}%)")
print(f"  Falta:     {len(falta_tr)}")
if falta_tr:
    print("  Muestra huecos:")
    for c in sorted(falta_tr)[:10]:
        print(f"    {c}")

# ── SINASTRÍA ─────────────────────────────────────────────────────────────────
print("\n=== SINASTRÍA ===")
teorico_syn = set()
for p1 in PLANETAS:
    for a in ASPECTOS:
        for p2 in PLANETAS:
            if p1 != p2:
                teorico_syn.add(f"SYN_{p1}_{p2}_{a}")

reales_syn = set(r[0] for r in conn.execute(
    "SELECT DISTINCT clave FROM interpretaciones WHERE tipo='sinastria'"))

falta_syn = teorico_syn - reales_syn
tiene_syn = teorico_syn & reales_syn

print(f"  Teórico:   {len(teorico_syn)}")
print(f"  Cubierto:  {len(tiene_syn)}  ({100*len(tiene_syn)//len(teorico_syn)}%)")
print(f"  Falta:     {len(falta_syn)}")
if falta_syn:
    print("  Muestra huecos:")
    for c in sorted(falta_syn)[:10]:
        print(f"    {c}")

# ── ASPECTOS NATALES ──────────────────────────────────────────────────────────
print("\n=== ASPECTOS NATALES ===")
# Orden canónico: SOL_LUNA no LUNA_SOL
orden = PLANETAS
teorico_asp = set()
for i, p1 in enumerate(orden):
    for p2 in orden[i+1:]:
        for a in ASPECTOS:
            teorico_asp.add(f"{p1}_{p2}_{a}")

reales_asp = set(r[0] for r in conn.execute(
    "SELECT DISTINCT clave FROM interpretaciones WHERE tipo='aspecto_natal'"))

falta_asp  = teorico_asp - reales_asp
tiene_asp  = teorico_asp & reales_asp

print(f"  Teórico:   {len(teorico_asp)}")
print(f"  Cubierto:  {len(tiene_asp)}  ({100*len(tiene_asp)//len(teorico_asp)}%)")
print(f"  Falta:     {len(falta_asp)}")
if falta_asp:
    print("  Muestra huecos:")
    for c in sorted(falta_asp)[:10]:
        print(f"    {c}")

conn.close()
