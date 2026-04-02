"""Endpoints REST para cartas (motor en app.astro_core)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.astro_core import build_natal_interpretations, compute_natal_chart
from app.jd_local import julday_from_local_iana

router = APIRouter(prefix="/api/charts", tags=["charts"])

_HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DB = os.path.join(_HERE, "..", "..", "data", "corpus.db")


class NatalRequest(BaseModel):
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: str = Field(..., description="HH:MM hora local 24 h")
    timezone: str = Field(..., description="IANA, ej. Europe/Madrid")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


@router.post("/natal")
def natal_chart(body: NatalRequest) -> dict:
    try:
        jd, meta = julday_from_local_iana(
            body.birth_date.strip(),
            body.birth_time.strip(),
            body.timezone.strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    chart = compute_natal_chart(jd, body.latitude, body.longitude)
    interpretations = build_natal_interpretations(chart, os.path.normpath(CORPUS_DB))

    return {
        "input": {
            "birth_date": body.birth_date.strip(),
            "birth_time": body.birth_time.strip(),
            "timezone": body.timezone.strip(),
            "latitude": body.latitude,
            "longitude": body.longitude,
        },
        "jd": jd,
        "time": meta,
        "chart": chart,
        "interpretations": interpretations,
    }
