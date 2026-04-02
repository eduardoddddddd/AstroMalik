"""
Julian Day desde fecha/hora local + zona IANA (zoneinfo).
Separado de la lógica de aspectos/casas en astro_core.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe


def julday_from_local_iana(
    birth_date: str,
    birth_time_hhmm: str,
    tz_name: str,
) -> tuple[float, dict]:
    """
    Convierte nacimiento local a JD con swe.julday en UT (UTC).
    birth_date: YYYY-MM-DD
    birth_time_hhmm: HH:MM (24 h)
    """
    tz_name = tz_name.strip()
    try:
        tz = ZoneInfo(tz_name)
    except Exception as exc:
        raise ValueError(f"Zona horaria IANA no válida: {tz_name}") from exc

    parts = birth_date.strip().split("-")
    if len(parts) != 3:
        raise ValueError("birth_date debe ser YYYY-MM-DD")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])

    tp = birth_time_hhmm.strip().split(":")
    hh = int(tp[0])
    mm = int(tp[1]) if len(tp) > 1 else 0
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError("Hora local fuera de rango")

    local = datetime(y, m, d, hh, mm, tzinfo=tz)
    utc = local.astimezone(ZoneInfo("UTC"))
    ut = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
    jd = swe.julday(utc.year, utc.month, utc.day, ut)
    meta = {
        "timezone_iana": tz_name,
        "local_iso": local.isoformat(),
        "utc_iso": utc.isoformat(),
        "ut_fractional_hours": round(ut, 6),
    }
    return jd, meta
