"""Transit period calculations for AstroMalik."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from app.astro_core import (
    ASPECTS,
    PLANETS,
    calc_planets,
    calc_planets_from_chart,
    compute_natal_chart,
    find_transit_aspects,
    get_interpretacion_transito,
)
from app.jd_local import julday_from_local_iana

CORPUS_DB = Path(__file__).resolve().parents[1] / "data" / "corpus.db"
EVENT_GAP_DAYS = 5
MAX_PERIOD_DAYS = 3660

PLANET_NAMES = {
    "SOL": "Sol",
    "LUNA": "Luna",
    "MERCURIO": "Mercurio",
    "VENUS": "Venus",
    "MARTE": "Marte",
    "JUPITER": "Jupiter",
    "SATURNO": "Saturno",
    "URANO": "Urano",
    "NEPTUNO": "Neptuno",
    "PLUTON": "Pluton",
}

ASPECT_NAMES = {
    "CONJUNCION": "Conjuncion",
    "SEXTIL": "Sextil",
    "CUADRADO": "Cuadratura",
    "TRIGONO": "Trigono",
    "OPOSICION": "Oposicion",
}

ASPECT_COLORS = {
    "CONJUNCION": "#d97706",
    "SEXTIL": "#2563eb",
    "CUADRADO": "#dc2626",
    "TRIGONO": "#15803d",
    "OPOSICION": "#a21caf",
}

PLANET_WEIGHTS = {
    "PLUTON": 10.0,
    "NEPTUNO": 9.0,
    "URANO": 8.0,
    "SATURNO": 7.0,
    "JUPITER": 6.0,
    "MARTE": 4.0,
    "VENUS": 2.0,
    "MERCURIO": 2.0,
    "SOL": 2.0,
    "LUNA": 1.0,
}

ASPECT_WEIGHTS = {
    "CONJUNCION": 5.0,
    "OPOSICION": 4.5,
    "CUADRADO": 4.0,
    "TRIGONO": 3.0,
    "SEXTIL": 2.0,
}

ASPECT_ORBS = {asp_key: orb for _angle, _label, asp_key, orb in ASPECTS}


def _stars_for_score(score: float) -> int:
    if score >= 25:
        return 5
    if score >= 15:
        return 4
    if score >= 8:
        return 3
    if score >= 3:
        return 2
    return 1


def _build_score(transit_key: str, aspect_key: str, min_orb: float) -> float:
    planet_weight = PLANET_WEIGHTS.get(transit_key, 1.0)
    aspect_weight = ASPECT_WEIGHTS.get(aspect_key, 1.0)
    max_orb = ASPECT_ORBS.get(aspect_key, 6.0)
    orb_factor = max(0.0, 1.0 - (min_orb / max_orb)) if max_orb else 0.5
    return round(planet_weight * aspect_weight * (0.5 + 0.5 * orb_factor), 1)


def compute_transit_period(
    *,
    birth_date: str,
    birth_time: str,
    timezone: str,
    latitude: float,
    longitude: float,
    from_date: str,
    to_date: str,
    exclude_moon: bool = True,
) -> dict:
    start = date.fromisoformat(from_date)
    end = date.fromisoformat(to_date)
    total_days = (end - start).days + 1

    if total_days < 1:
        raise ValueError('La fecha "hasta" debe ser posterior o igual a "desde".')
    if total_days > MAX_PERIOD_DAYS:
        raise ValueError("Maximo 10 anos de rango.")

    natal_jd, natal_time = julday_from_local_iana(birth_date, birth_time, timezone)
    natal_chart = compute_natal_chart(natal_jd, latitude, longitude)
    natal_planets = calc_planets_from_chart(natal_chart)

    events: dict[str, dict] = {}
    last_event_key_by_base: dict[str, str] = {}

    for day_index in range(total_days):
        current_date = start + timedelta(days=day_index)
        current_jd, _meta = julday_from_local_iana(
            current_date.isoformat(),
            "12:00",
            timezone,
        )
        transit_planets = calc_planets(current_jd)
        aspects = find_transit_aspects(
            natal_planets,
            transit_planets,
            outer_only=False,
        )

        for aspect in aspects:
            transit_key = str(aspect["tr_key"])
            natal_key = str(aspect["n_key"])
            aspect_key = str(aspect["asp_key"])
            orb = round(float(aspect["orb"]), 2)

            if exclude_moon and transit_key == "LUNA":
                continue
            if transit_key == natal_key:
                continue

            base_key = f"{transit_key}:{aspect_key}:{natal_key}"
            current_iso = current_date.isoformat()
            event_key = last_event_key_by_base.get(base_key)

            if event_key is None:
                event_key = base_key
                events[event_key] = {
                    "transit_key": transit_key,
                    "transit_label": PLANET_NAMES.get(transit_key, transit_key.title()),
                    "natal_key": natal_key,
                    "natal_label": PLANET_NAMES.get(natal_key, natal_key.title()),
                    "aspect_key": aspect_key,
                    "aspect_label": ASPECT_NAMES.get(aspect_key, aspect_key.title()),
                    "color": ASPECT_COLORS.get(aspect_key, "#6b6560"),
                    "from_date": current_iso,
                    "to_date": current_iso,
                    "exact_date": current_iso,
                    "min_orb": orb,
                    "retrograde_on_exact": bool(
                        transit_planets[transit_key]["speed"] < 0
                    ),
                    "_last_date": current_date,
                }
                last_event_key_by_base[base_key] = event_key
                continue

            existing = events[event_key]
            last_date = existing["_last_date"]
            if (current_date - last_date).days > EVENT_GAP_DAYS:
                suffix = 2
                next_key = f"{base_key}:{suffix}"
                while next_key in events:
                    suffix += 1
                    next_key = f"{base_key}:{suffix}"
                event_key = next_key
                events[event_key] = {
                    "transit_key": transit_key,
                    "transit_label": PLANET_NAMES.get(transit_key, transit_key.title()),
                    "natal_key": natal_key,
                    "natal_label": PLANET_NAMES.get(natal_key, natal_key.title()),
                    "aspect_key": aspect_key,
                    "aspect_label": ASPECT_NAMES.get(aspect_key, aspect_key.title()),
                    "color": ASPECT_COLORS.get(aspect_key, "#6b6560"),
                    "from_date": current_iso,
                    "to_date": current_iso,
                    "exact_date": current_iso,
                    "min_orb": orb,
                    "retrograde_on_exact": bool(
                        transit_planets[transit_key]["speed"] < 0
                    ),
                    "_last_date": current_date,
                }
                last_event_key_by_base[base_key] = event_key
                continue

            existing["to_date"] = current_iso
            existing["_last_date"] = current_date
            if orb < float(existing["min_orb"]):
                existing["min_orb"] = orb
                existing["exact_date"] = current_iso
                existing["retrograde_on_exact"] = bool(
                    transit_planets[transit_key]["speed"] < 0
                )

    results: list[dict] = []
    for event in events.values():
        final_date = date.fromisoformat(str(event["to_date"]))
        start_date = date.fromisoformat(str(event["from_date"]))
        active_days = (final_date - start_date).days + 1
        score = _build_score(
            str(event["transit_key"]),
            str(event["aspect_key"]),
            float(event["min_orb"]),
        )
        stars = _stars_for_score(score)
        text, source = get_interpretacion_transito(
            str(CORPUS_DB),
            str(event["transit_key"]),
            str(event["natal_key"]),
            str(event["aspect_key"]),
        )

        results.append(
            {
                "transit_key": event["transit_key"],
                "transit_label": event["transit_label"],
                "natal_key": event["natal_key"],
                "natal_label": event["natal_label"],
                "aspect_key": event["aspect_key"],
                "aspect_label": event["aspect_label"],
                "color": event["color"],
                "from_date": event["from_date"],
                "to_date": event["to_date"],
                "exact_date": event["exact_date"],
                "active_days": active_days,
                "min_orb": float(event["min_orb"]),
                "retrograde_on_exact": bool(event["retrograde_on_exact"]),
                "score": score,
                "stars": stars,
                "text": text,
                "source": source,
            }
        )

    results.sort(
        key=lambda item: (
            -float(item["score"]),
            float(item["min_orb"]),
            str(item["exact_date"]),
        )
    )

    return {
        "input": {
            "birth_date": birth_date,
            "birth_time": birth_time,
            "timezone": timezone,
            "latitude": latitude,
            "longitude": longitude,
            "from_date": from_date,
            "to_date": to_date,
            "exclude_moon": exclude_moon,
        },
        "natal_time": natal_time,
        "natal_chart": natal_chart,
        "events": results,
        "summary": {
            "total_events": len(results),
            "events_with_text": sum(1 for item in results if item["text"]),
            "days_total": total_days,
        },
    }
