"""
Núcleo de efemérides — misma lógica que malik-service-hub/apps/astrobot/astrobot.py
(AstroBot v2). No alterar bucles de casas/aspectos sin revisar contra esa base.

Documentación de apoyo: nota Joplin «pyswisseph — Manual Exprés de Efemérides».
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any

import swisseph as swe

# ── Config efemérides (servidor: /opt/astromalik/data/ephe; local: None o env) ──
def configure_ephemeris_path() -> None:
    raw = os.environ.get("SWISSEPH_EPHE_PATH", "").strip()
    if raw in ("", "none", "None"):
        swe.set_ephe_path(None)
    else:
        swe.set_ephe_path(raw)


configure_ephemeris_path()

PLANETS = [
    (swe.SUN, "☉ Sol", "SOL"),
    (swe.MOON, "☽ Luna", "LUNA"),
    (swe.MERCURY, "☿ Mercurio", "MERCURIO"),
    (swe.VENUS, "♀ Venus", "VENUS"),
    (swe.MARS, "♂ Marte", "MARTE"),
    (swe.JUPITER, "♃ Júpiter", "JUPITER"),
    (swe.SATURN, "♄ Saturno", "SATURNO"),
    (swe.URANUS, "⛢ Urano", "URANO"),
    (swe.NEPTUNE, "♆ Neptuno", "NEPTUNO"),
    (swe.PLUTO, "♇ Plutón", "PLUTON"),
]

OUTER = {"JUPITER", "SATURNO", "URANO", "NEPTUNO", "PLUTON", "MARTE"}

SIGNS = [
    "♈ Aries",
    "♉ Tauro",
    "♊ Géminis",
    "♋ Cáncer",
    "♌ Leo",
    "♍ Virgo",
    "♎ Libra",
    "♏ Escorpio",
    "♐ Sagitario",
    "♑ Capricornio",
    "♒ Acuario",
    "♓ Piscis",
]

# Nombres de signos tal como aparecen en corpus.db (sin emoji, sin tildes conflictivas)
SIGNS_KEY = [
    "ARIES", "TAURO", "GEMINIS", "CANCER", "LEO", "VIRGO",
    "LIBRA", "ESCORPIO", "SAGITARIO", "CAPRICORNIO", "ACUARIO", "PISCIS",
]

ASPECTS = [
    (0, "☌ Conjunción", "CONJUNCION", 8),
    (60, "⚹ Sextil", "SEXTIL", 5),
    (90, "□ Cuadratura", "CUADRADO", 7),
    (120, "△ Trígono", "TRIGONO", 7),
    (180, "☍ Oposición", "OPOSICION", 8),
]


def deg_to_sign(deg: float) -> str:
    deg = deg % 360
    s = int(deg / 30)
    d = int(deg % 30)
    m = int(((deg % 30) - d) * 60)
    return f"{SIGNS[s]} {d:02d}°{m:02d}'"


def deg_to_sign_key(deg: float) -> str:
    """Devuelve clave de signo para corpus, ej. 'ARIES'."""
    return SIGNS_KEY[int((deg % 360) / 30)]


def calc_planets(jd: float) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for pid, label, key in PLANETS:
        pos, _ret = swe.calc_ut(jd, pid)
        spd = float(pos[3])
        retro = " ℞" if spd < 0 else ""
        result[key] = {
            "deg": float(pos[0]),
            "label": label,
            "retro": retro,
            "speed": spd,
        }
    return result


def calc_houses(
    jd: float, lat: float, lon: float, hsys: bytes = b"P"
) -> tuple[Any, float, float]:
    cusps, ascmc = swe.houses(jd, lat, lon, hsys)
    return cusps, ascmc[0], ascmc[1]


def planet_house_from_cusps(deg: float, cusps) -> int:
    """Misma lógica que cmd_carta en astrobot.py (bucle por casas)."""
    house = 1
    deg = deg % 360
    for i in range(12):
        cs, ce = cusps[i], cusps[(i + 1) % 12]
        if ce < cs:
            if deg >= cs or deg < ce:
                house = i + 1
                break
        else:
            if cs <= deg < ce:
                house = i + 1
                break
    return house


def find_transit_aspects(
    natal_planets: dict, transit_planets: dict, outer_only: bool = False
) -> list[dict]:
    found = []
    for tr_key, tr_data in transit_planets.items():
        if outer_only and tr_key not in OUTER:
            continue
        for n_key, n_data in natal_planets.items():
            diff = abs((tr_data["deg"] - n_data["deg"] + 360) % 360)
            if diff > 180:
                diff = 360 - diff
            for angle, asp_label, asp_key, orb in ASPECTS:
                if abs(diff - angle) <= orb:
                    found.append(
                        {
                            "tr_label": tr_data["label"] + tr_data["retro"],
                            "tr_key": tr_key,
                            "n_label": n_data["label"],
                            "n_key": n_key,
                            "asp_label": asp_label,
                            "asp_key": asp_key,
                            "orb": abs(diff - angle),
                            "exact_deg": diff,
                        }
                    )
    found.sort(key=lambda x: x["orb"])
    return found


def get_interpretacion_transito(
    corpus_db: str, tr_key: str, natal_key: str, asp_key: str
) -> tuple[str | None, str | None]:
    """Claves corpus tipo transito: SATURNO_tr_SOL_OPOSICION."""
    clave = f"{tr_key}_tr_{natal_key}_{asp_key}"
    try:
        con = sqlite3.connect(f"file:{corpus_db}?mode=ro", uri=True)
        cur = con.cursor()
        cur.execute(
            """
            SELECT texto_largo, texto_corto, calidad, fuente_nombre
            FROM interpretaciones
            WHERE clave=? AND tipo='transito'
            ORDER BY calidad DESC, LENGTH(texto_largo) DESC LIMIT 1
            """,
            (clave,),
        )
        row = cur.fetchone()
        con.close()
        if row:
            texto = (row[0] or row[1] or "").strip()
            fuente = row[3] or ""
            if texto:
                if len(texto) > 3800:
                    texto = texto[:3800].rsplit(" ", 1)[0] + "…"
                return texto, fuente
    except Exception:
        pass
    return None, None


def compute_natal_aspects(planets: dict[str, dict]) -> list[dict]:
    """Aspectos entre planetas natales (pares no repetidos, orden PLANETS)."""
    keys = [k for _pid, _lab, k in PLANETS]
    found = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            ka, kb = keys[i], keys[j]
            da, db = planets[ka]["deg"], planets[kb]["deg"]
            diff = abs((da - db + 360) % 360)
            if diff > 180:
                diff = 360 - diff
            for angle, asp_label, asp_key, orb in ASPECTS:
                if abs(diff - angle) <= orb:
                    found.append(
                        {
                            "key_a": ka,
                            "label_a": planets[ka]["label"],
                            "key_b": kb,
                            "label_b": planets[kb]["label"],
                            "asp_label": asp_label,
                            "asp_key": asp_key,
                            "orb": round(abs(diff - angle), 2),
                            "corpus_clave": f"{ka}_{kb}_{asp_key}",
                        }
                    )
    found.sort(key=lambda x: x["orb"])
    return found


def lookup_corpus(
    corpus_db: str,
    claves: list[str],
    tipos: tuple[str, ...] = ("natal_planeta_signo", "natal_planeta_casa", "aspecto_natal"),
) -> dict[str, dict]:
    """Consulta batch en corpus.db; devuelve dict clave→{texto, fuente, tipo}."""
    if not claves:
        return {}
    placeholders = ",".join("?" * len(claves))
    tipos_ph = ",".join("?" * len(tipos))
    try:
        con = sqlite3.connect(f"file:{corpus_db}?mode=ro", uri=True)
        cur = con.cursor()
        cur.execute(
            f"""
            SELECT clave, tipo, texto_largo, texto_corto, fuente_nombre, calidad
            FROM interpretaciones
            WHERE tipo IN ({tipos_ph}) AND clave IN ({placeholders})
            ORDER BY calidad DESC, LENGTH(COALESCE(texto_largo,'')) DESC
            """,
            (*tipos, *claves),
        )
        rows = cur.fetchall()
        con.close()
    except Exception:
        return {}

    result: dict[str, dict] = {}
    for clave, tipo, tl, tc, fuente, _cal in rows:
        if clave in result:
            continue  # ya tenemos el mejor (ordenado por calidad)
        texto = (tl or tc or "").strip()
        if not texto:
            continue
        if len(texto) > 4000:
            texto = texto[:4000].rsplit(" ", 1)[0] + "…"
        result[clave] = {"tipo": tipo, "texto": texto, "fuente": fuente or ""}
    return result


def build_natal_interpretations(chart: dict, corpus_db: str) -> list[dict]:
    """
    Genera la lista de interpretaciones para una carta natal completa.
    Incluye planeta/signo, planeta/casa y aspectos entre planetas.
    """
    bodies = chart["bodies"]
    asc_deg = chart["ascendant"]["longitude"]
    mc_deg = chart["mc"]["longitude"]

    # Claves planeta/signo y planeta/casa
    claves: list[str] = []
    meta: dict[str, dict] = {}

    for b in bodies:
        sk = deg_to_sign_key(b["longitude"])
        ck_signo = f"{b['key']}_{sk}"
        ck_casa = f"{b['key']}_CASA_{b['house']}"
        claves += [ck_signo, ck_casa]
        meta[ck_signo] = {
            "tipo": "natal_planeta_signo",
            "titulo": f"{b['label']} en {SIGNS[int(b['longitude'] % 360 / 30)]}",
            "orden": 1,
        }
        meta[ck_casa] = {
            "tipo": "natal_planeta_casa",
            "titulo": f"{b['label']} en Casa {b['house']}",
            "orden": 2,
        }

    # Claves aspecto natal entre planetas
    planets_raw = calc_planets_from_chart(chart)
    nat_aspects = compute_natal_aspects(planets_raw)
    for asp in nat_aspects:
        c = asp["corpus_clave"]
        claves.append(c)
        meta[c] = {
            "tipo": "aspecto_natal",
            "titulo": f"{asp['label_a']} {asp['asp_label']} {asp['label_b']} (orbe {asp['orb']}°)",
            "orden": 3,
        }

    # Aspectos planeta/ASC y planeta/MC
    asc_pts = {"ASC": asc_deg, "MC": mc_deg}
    planet_degs = {b["key"]: (b["longitude"], b["label"]) for b in bodies}
    for pt_key, pt_deg in asc_pts.items():
        for p_key, (p_deg, p_lab) in planet_degs.items():
            diff = abs((p_deg - pt_deg + 360) % 360)
            if diff > 180:
                diff = 360 - diff
            for angle, asp_label, asp_key, orb in ASPECTS:
                if abs(diff - angle) <= orb:
                    c = f"{p_key}_{pt_key}_{asp_key}"
                    claves.append(c)
                    meta[c] = {
                        "tipo": "aspecto_natal",
                        "titulo": f"{p_lab} {asp_label} {pt_key} (orbe {abs(diff-angle):.1f}°)",
                        "orden": 3,
                    }

    textos = lookup_corpus(corpus_db, claves)

    result = []
    for clave in claves:
        if clave not in textos:
            continue
        m = meta[clave]
        result.append(
            {
                "clave": clave,
                "tipo": m["tipo"],
                "titulo": m["titulo"],
                "texto": textos[clave]["texto"],
                "fuente": textos[clave]["fuente"],
                "orden": m["orden"],
            }
        )

    result.sort(key=lambda x: (x["orden"], x["titulo"]))
    return result


def calc_planets_from_chart(chart: dict) -> dict[str, dict]:
    """Reconstruye el dict de planetas desde la lista 'bodies' del chart."""
    return {
        b["key"]: {
            "deg": b["longitude"],
            "label": b["label"],
            "retro": " ℞" if b["retrograde"] else "",
            "speed": -1.0 if b["retrograde"] else 1.0,
        }
        for b in chart["bodies"]
    }


def compute_natal_chart(jd: float, lat: float, lon: float) -> dict[str, Any]:
    """
    Carta natal Placidus — equivalente a cmd_carta en astrobot (sin Telegram).
    """
    planets = calc_planets(jd)
    cusps, asc, mc = calc_houses(jd, lat, lon, b"P")

    asc_f = deg_to_sign(asc)
    mc_f = deg_to_sign(mc)

    bodies = []
    for _pid, _lab, key in PLANETS:
        d = planets[key]
        deg = d["deg"]
        h = planet_house_from_cusps(deg, cusps)
        bodies.append(
            {
                "key": key,
                "label": d["label"],
                "longitude": deg,
                "formatted": deg_to_sign(deg),
                "house": h,
                "retrograde": d["speed"] < 0,
            }
        )

    cusps_out = [float(cusps[i] % 360) for i in range(12)]

    return {
        "house_system": "Placidus",
        "ascendant": {"longitude": float(asc % 360), "formatted": asc_f},
        "mc": {"longitude": float(mc % 360), "formatted": mc_f},
        "cusps": cusps_out,
        "bodies": bodies,
    }
