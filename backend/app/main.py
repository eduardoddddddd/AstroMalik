"""
API AstroMalik — salud, corpus, lugares y cartas guardadas.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import user_store
from app.places import merge_places
from app.routers import charts as charts_router
from app.user_store import delete_chart, get_one, init_db, insert_chart, list_saved

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CORPUS_DB = DATA / "corpus.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AstroMalik API", version="0.3.0", lifespan=lifespan)

app.include_router(charts_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "astromalik-api",
        "corpus_db": CORPUS_DB.exists(),
        "user_db": (DATA / "user.db").exists(),
    }


@app.get("/api/corpus/stats")
def corpus_stats() -> dict:
    if not CORPUS_DB.exists():
        return {"error": "corpus.db no encontrado", "path": str(CORPUS_DB)}
    conn = sqlite3.connect(f"file:{CORPUS_DB}?mode=ro", uri=True)
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM interpretaciones"
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT tipo, COUNT(*) FROM interpretaciones GROUP BY tipo"
        ).fetchall()
    finally:
        conn.close()
    return {
        "total": total,
        "by_type": {tipo: n for tipo, n in rows},
        "path": str(CORPUS_DB),
    }


@app.get("/api/places/search")
def places_search(q: str = "") -> dict:
    """Ciudades embebidas + resultados Nominatim (OSM)."""
    results = merge_places(q)
    return {"query": q.strip(), "results": results}


class SavedChartIn(BaseModel):
    profile_name: str = ""
    birth_date: str = Field(..., min_length=8)
    birth_time: str = Field(..., min_length=4)
    timezone: str = Field(..., min_length=3)
    place_label: str = ""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class SavedChartOut(BaseModel):
    id: int
    profile_name: str
    birth_date: str
    birth_time: str
    timezone: str
    place_label: str
    latitude: float
    longitude: float
    created_at: str


@app.get("/api/saved-charts", response_model=list[SavedChartOut])
def saved_list() -> list[dict]:
    return list_saved()


@app.post("/api/saved-charts", response_model=SavedChartOut)
def saved_create(body: SavedChartIn) -> dict:
    new_id = insert_chart(
        profile_name=body.profile_name.strip(),
        birth_date=body.birth_date.strip(),
        birth_time=body.birth_time.strip(),
        timezone=body.timezone.strip(),
        place_label=body.place_label.strip(),
        latitude=body.latitude,
        longitude=body.longitude,
    )
    row = get_one(new_id)
    if not row:
        raise HTTPException(status_code=500, detail="No se pudo leer la carta guardada")
    return row


@app.get("/api/saved-charts/{chart_id}", response_model=SavedChartOut)
def saved_get(chart_id: int) -> dict:
    row = get_one(chart_id)
    if not row:
        raise HTTPException(status_code=404, detail="Carta no encontrada")
    return row


@app.delete("/api/saved-charts/{chart_id}")
def saved_delete(chart_id: int) -> dict:
    if not delete_chart(chart_id):
        raise HTTPException(status_code=404, detail="Carta no encontrada")
    return {"ok": True, "id": chart_id}


def _port() -> int:
    raw = os.environ.get("ASTROMALIK_API_PORT", "8765")
    return int(raw)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=_port(),
        reload=True,
    )
