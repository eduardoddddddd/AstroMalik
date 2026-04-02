"""Persistencia de cartas guardadas (SQLite local)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER_DB = ROOT / "data" / "user.db"

DDL = """
CREATE TABLE IF NOT EXISTS saved_charts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_name TEXT NOT NULL DEFAULT '',
  birth_date TEXT NOT NULL,
  birth_time TEXT NOT NULL,
  timezone TEXT NOT NULL,
  place_label TEXT NOT NULL DEFAULT '',
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_saved_charts_created ON saved_charts(created_at DESC);
"""


def init_db() -> None:
    USER_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(USER_DB)
    try:
        conn.executescript(DDL)
        conn.commit()
    finally:
        conn.close()


def list_saved() -> list[dict]:
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT id, profile_name, birth_date, birth_time, timezone, "
            "place_label, latitude, longitude, created_at "
            "FROM saved_charts ORDER BY datetime(created_at) DESC"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_one(chart_id: int) -> dict | None:
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT id, profile_name, birth_date, birth_time, timezone, "
            "place_label, latitude, longitude, created_at "
            "FROM saved_charts WHERE id = ?",
            (chart_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def insert_chart(
    profile_name: str,
    birth_date: str,
    birth_time: str,
    timezone: str,
    place_label: str,
    latitude: float,
    longitude: float,
) -> int:
    conn = sqlite3.connect(USER_DB)
    try:
        cur = conn.execute(
            "INSERT INTO saved_charts (profile_name, birth_date, birth_time, "
            "timezone, place_label, latitude, longitude) VALUES (?,?,?,?,?,?,?)",
            (
                profile_name,
                birth_date,
                birth_time,
                timezone,
                place_label,
                latitude,
                longitude,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def delete_chart(chart_id: int) -> bool:
    conn = sqlite3.connect(USER_DB)
    try:
        cur = conn.execute("DELETE FROM saved_charts WHERE id = ?", (chart_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
