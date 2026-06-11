# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Adaptador de la API football-data.org (fuente principal de datos)."""
from __future__ import annotations

from ...core.config import (COMPETITION_CODE, FOOTBALL_DATA_API_KEY,
                            FOOTBALL_DATA_BASE)
from .. import http


def is_enabled() -> bool:
    return bool(FOOTBALL_DATA_API_KEY)


def _headers() -> dict:
    return {"X-Auth-Token": FOOTBALL_DATA_API_KEY}


def fetch_matches() -> list[dict]:
    if not is_enabled():
        return []
    url = f"{FOOTBALL_DATA_BASE}/competitions/{COMPETITION_CODE}/matches"
    try:
        r = http.get(url, headers=_headers(), timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        print(f"[api] partidos no disponibles: {exc}")
        return []

    out: list[dict] = []
    for m in data.get("matches", []):
        score = m.get("score", {}).get("fullTime", {})
        status = {"FINISHED": "FINISHED", "IN_PLAY": "IN_PLAY",
                  "PAUSED": "IN_PLAY"}.get(m.get("status", ""), "SCHEDULED")
        out.append({
            "ext_id": f"fd-{m.get('id')}",
            "utc_date": m.get("utcDate"),
            "stage": m.get("stage"),
            "grp": (m.get("group") or "").replace("GROUP_", "").strip() or None,
            "home": (m.get("homeTeam") or {}).get("name") or "",
            "away": (m.get("awayTeam") or {}).get("name") or "",
            "home_goals": score.get("home"),
            "away_goals": score.get("away"),
            "status": status,
            "source": "football-data.org",
        })
    return [m for m in out if m["home"] and m["away"]]


def fetch_teams() -> list[dict]:
    if not is_enabled():
        return []
    url = f"{FOOTBALL_DATA_BASE}/competitions/{COMPETITION_CODE}/teams"
    try:
        r = http.get(url, headers=_headers(), timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        print(f"[api] equipos no disponibles: {exc}")
        return []
    out = [{"name": t.get("name"), "code": t.get("tla") or "", "grp": ""}
           for t in data.get("teams", [])]
    return [t for t in out if t["name"]]
