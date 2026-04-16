"""Endpoints REST para cartas (motor en app.astro_core)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.astro_core import build_natal_interpretations, compute_natal_chart
from app.config import CORPUS_DB
from app.jd_local import julday_from_local_iana
from app.transits import compute_transit_period

router = APIRouter(prefix="/api/charts", tags=["charts"])


class NatalRequest(BaseModel):
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: str = Field(..., description="HH:MM hora local 24 h")
    timezone: str = Field(..., description="IANA, ej. Europe/Madrid")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class TransitPeriodRequest(BaseModel):
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: str = Field(..., description="HH:MM hora local 24 h")
    timezone: str = Field(..., description="IANA, ej. Europe/Madrid")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    from_date: str = Field(..., description="YYYY-MM-DD")
    to_date: str = Field(..., description="YYYY-MM-DD")
    exclude_moon: bool = True


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
    interpretations = build_natal_interpretations(chart, str(CORPUS_DB))

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


@router.post("/transits")
def transit_period(body: TransitPeriodRequest) -> dict:
    try:
        return compute_transit_period(
            birth_date=body.birth_date.strip(),
            birth_time=body.birth_time.strip(),
            timezone=body.timezone.strip(),
            latitude=body.latitude,
            longitude=body.longitude,
            from_date=body.from_date.strip(),
            to_date=body.to_date.strip(),
            exclude_moon=body.exclude_moon,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
