"""Búsqueda de lugares: lista embebida + Nominatim (OSM)."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "cities_seed.json"

# Política Nominatim: máx. ~1 req/s; uso moderado en dev. Producción: instancia propia o caché.
UA = "AstroMalik/0.1 (personal astrology app; local dev)"


def _load_seed() -> list[dict]:
    if not SEED_PATH.exists():
        return []
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    out = []
    for row in raw:
        out.append(
            {
                "label": row["label"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "source": "seed",
            }
        )
    return out


_SEED_CACHE: list[dict] | None = None


def seed_cities() -> list[dict]:
    global _SEED_CACHE
    if _SEED_CACHE is None:
        _SEED_CACHE = _load_seed()
    return _SEED_CACHE


def filter_seed(q: str, limit: int = 12) -> list[dict]:
    qn = q.strip().lower()
    if len(qn) < 2:
        return []
    hits = []
    for row in seed_cities():
        if qn in row["label"].lower():
            hits.append(row)
        if len(hits) >= limit:
            break
    return hits


def nominatim_search(q: str, limit: int = 8) -> list[dict]:
    q = q.strip()
    if len(q) < 2:
        return []
    params = urllib.parse.urlencode(
        {
            "q": q,
            "format": "json",
            "limit": limit,
            "addressdetails": "0",
        }
    )
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode())
    results = []
    for row in data:
        try:
            results.append(
                {
                    "label": row.get("display_name", ""),
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "source": "nominatim",
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return results


def _same_place(a: dict, b: dict, eps: float = 0.02) -> bool:
    return (
        abs(a["lat"] - b["lat"]) < eps
        and abs(a["lon"] - b["lon"]) < eps
    )


def merge_places(q: str, nominatim_limit: int = 6) -> list[dict]:
    """Ciudades predefinidas primero, luego Nominatim, sin duplicados cercanos."""
    seed_hits = filter_seed(q, limit=15)
    seen = list(seed_hits)
    remote: list[dict] = []
    try:
        remote = nominatim_search(q, limit=nominatim_limit)
    except Exception:
        remote = []
    for r in remote:
        if not any(_same_place(r, s) for s in seen):
            seen.append(r)
    return seen[:20]
