# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Repositorio de datos (SQLite). Capa de infraestructura."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from ..core.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT UNIQUE NOT NULL,
    code    TEXT,
    grp     TEXT,
    elo     REAL NOT NULL DEFAULT 1500,
    attack  REAL NOT NULL DEFAULT 1.0,
    defense REAL NOT NULL DEFAULT 1.0
);
CREATE TABLE IF NOT EXISTS matches (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ext_id     TEXT UNIQUE,
    utc_date   TEXT,
    stage      TEXT,
    grp        TEXT,
    home       TEXT NOT NULL,
    away       TEXT NOT NULL,
    home_goals INTEGER,
    away_goals INTEGER,
    status     TEXT NOT NULL DEFAULT 'SCHEDULED',
    source     TEXT
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # WAL permite lecturas concurrentes mientras se escribe: evita que las
        # peticiones (p. ej. el health check) se bloqueen durante la ingesta.
        conn.execute("PRAGMA journal_mode=WAL")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---- meta ----
def set_meta(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def get_meta(key: str, default: str | None = None) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


# ---- teams ----
def upsert_team(name: str, code: str = "", grp: str = "", elo: float | None = None) -> None:
    with get_conn() as conn:
        existing = conn.execute("SELECT id FROM teams WHERE name=?", (name,)).fetchone()
        if existing:
            if grp:
                conn.execute("UPDATE teams SET grp=? WHERE name=?", (grp, name))
            if code:
                conn.execute("UPDATE teams SET code=? WHERE name=?", (code, name))
            if elo is not None:
                conn.execute("UPDATE teams SET elo=? WHERE name=?", (elo, name))
        else:
            conn.execute(
                "INSERT INTO teams(name, code, grp, elo) VALUES(?, ?, ?, ?)",
                (name, code, grp, elo if elo is not None else 1500.0),
            )


def get_teams() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM teams ORDER BY grp, name").fetchall()
        return [dict(r) for r in rows]


def update_team_rating(name: str, elo: float | None = None,
                       attack: float | None = None, defense: float | None = None) -> None:
    sets, params = [], []
    if elo is not None:
        sets.append("elo=?"); params.append(elo)
    if attack is not None:
        sets.append("attack=?"); params.append(attack)
    if defense is not None:
        sets.append("defense=?"); params.append(defense)
    if not sets:
        return
    params.append(name)
    with get_conn() as conn:
        conn.execute(f"UPDATE teams SET {', '.join(sets)} WHERE name=?", params)


# ---- matches ----
def upsert_match(m: dict) -> None:
    with get_conn() as conn:
        existing = None
        if m.get("ext_id"):
            existing = conn.execute(
                "SELECT id FROM matches WHERE ext_id=?", (m["ext_id"],)
            ).fetchone()
        if existing is None:
            existing = conn.execute(
                "SELECT id FROM matches WHERE home=? AND away=? AND utc_date=?",
                (m["home"], m["away"], m.get("utc_date")),
            ).fetchone()
        if existing:
            conn.execute(
                """UPDATE matches SET utc_date=?, stage=?, grp=?, home_goals=?,
                   away_goals=?, status=?, source=? WHERE id=?""",
                (m.get("utc_date"), m.get("stage"), m.get("grp"),
                 m.get("home_goals"), m.get("away_goals"),
                 m.get("status", "SCHEDULED"), m.get("source"), existing["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO matches(ext_id, utc_date, stage, grp, home, away,
                   home_goals, away_goals, status, source)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (m.get("ext_id"), m.get("utc_date"), m.get("stage"), m.get("grp"),
                 m["home"], m["away"], m.get("home_goals"), m.get("away_goals"),
                 m.get("status", "SCHEDULED"), m.get("source")),
            )


def get_matches(status: str | None = None) -> list[dict]:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM matches WHERE status=? ORDER BY utc_date", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM matches ORDER BY utc_date").fetchall()
        return [dict(r) for r in rows]


def get_match(match_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM matches WHERE id=?", (match_id,)).fetchone()
        return dict(row) if row else None


def delete_matches_by_source(source: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM matches WHERE source=?", (source,))


def count(table: str) -> int:
    with get_conn() as conn:
        return conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
