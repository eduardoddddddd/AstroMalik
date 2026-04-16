"""Rutas centralizadas del proyecto AstroMalik.

Importar desde aquí en lugar de definir CORPUS_DB / USER_DB localmente
en cada módulo. De este modo, si cambia la ubicación de los datos,
solo hay que modificar este archivo.
"""

from __future__ import annotations

from pathlib import Path

# backend/
ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
CORPUS_DB = DATA / "corpus.db"
USER_DB = DATA / "user.db"
