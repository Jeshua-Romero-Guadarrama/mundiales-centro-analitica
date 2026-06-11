# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Servicio de ingesta: combina semilla + API + scraping y recalcula ratings."""
from __future__ import annotations

import json
import unicodedata
from datetime import datetime, timezone

from ..analytics import ratings
from ..infrastructure import database as db
from ..infrastructure.seed import seed_fixtures, seed_teams
from ..infrastructure.sources import football_api, wikipedia

ALIASES = {
    "South Korea": "Korea Republic", "Korea, South": "Korea Republic",
    "IR Iran": "Iran", "Iran (Islamic Republic of)": "Iran",
    "United States": "USA", "United States of America": "USA",
    "Cote d'Ivoire": "Ivory Coast", "Côte d'Ivoire": "Ivory Coast",
    "Türkiye": "Turkey", "Turkiye": "Turkey",
}


def _canon(name: str) -> str:
    name = (name or "").strip()
    return ALIASES.get(name, name)


def _norm(s: str) -> str:
    """Normaliza un nombre (sin acentos, minúsculas) para emparejar selecciones."""
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def ensure_seeded() -> None:
    db.init_db()
    if db.count("teams") == 0:
        for t in seed_teams():
            db.upsert_team(t["name"], t["code"], t["grp"], t["elo"])
        print("[ingest] equipos semilla cargados")
    if db.count("matches") == 0:
        for m in seed_fixtures():
            db.upsert_match(m)
        print("[ingest] calendario semilla cargado")


def run_update() -> dict:
    ensure_seeded()
    summary = {"api_matches": 0, "api_teams": 0, "wiki_results": 0,
               "source": "seed", "errors": []}

    try:
        api_teams = football_api.fetch_teams()
        for t in api_teams:
            db.upsert_team(_canon(t["name"]), t.get("code", ""), t.get("grp", ""))
        summary["api_teams"] = len(api_teams)

        api_matches = football_api.fetch_matches()
        for m in api_matches:
            m["home"], m["away"] = _canon(m["home"]), _canon(m["away"])
            db.upsert_match(m)
        summary["api_matches"] = len(api_matches)
        if api_matches:
            summary["source"] = "football-data.org"
    except Exception as exc:
        summary["errors"].append(f"api: {exc}")

    try:
        known = {t["name"] for t in db.get_teams()}
        applied = 0
        for m in wikipedia.fetch_results():
            home, away = _canon(m["home"]), _canon(m["away"])
            if home in known and away in known:
                m["home"], m["away"] = home, away
                db.upsert_match(m)
                applied += 1
        summary["wiki_results"] = applied
        if applied and summary["source"] == "seed":
            summary["source"] = "wikipedia"
    except Exception as exc:
        summary["errors"].append(f"wiki: {exc}")

    # Clasificaciones reales de los grupos (refleja los partidos ya jugados).
    try:
        standings = wikipedia.fetch_group_standings()
        if standings:
            canon = {_norm(t["name"]): t["name"] for t in db.get_teams()}
            norm_st = {
                grp: [{**f, "name": canon.get(_norm(f["name"]), f["name"])} for f in filas]
                for grp, filas in standings.items()
            }
            db.set_meta("standings_scraped", json.dumps(norm_st))
            jugados = sum(f["pld"] for filas in norm_st.values() for f in filas) // 2
            db.set_meta("played_count", str(jugados))
            summary["standings_groups"] = len(norm_st)
            summary["played"] = jugados
    except Exception as exc:
        summary["errors"].append(f"standings: {exc}")

    try:
        ratings.recompute_all()
    except Exception as exc:
        summary["errors"].append(f"ratings: {exc}")

    db.set_meta("last_update", datetime.now(timezone.utc).isoformat())
    db.set_meta("last_update_summary", str(summary))
    print(f"[ingest] actualizacion completada: {summary}")
    return summary
