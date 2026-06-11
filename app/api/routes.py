# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Rutas de la API REST (capa de presentacion)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..analytics import evaluation, montecarlo, registry
from ..core.config import FOOTBALL_DATA_API_KEY, PUBLIC_MODE
from ..infrastructure import database as db
from ..services import ingestion

router = APIRouter(prefix="/api")


def _team_map() -> dict[str, dict]:
    return {t["name"]: t for t in db.get_teams()}


@router.get("/status")
def status():
    return {
        "last_update": db.get_meta("last_update"),
        "server_time": datetime.now(timezone.utc).isoformat(),
        "teams": db.count("teams"),
        "matches": db.count("matches"),
        "finished": int(db.get_meta("played_count", "0") or 0) or len(db.get_matches("FINISHED")),
        "in_play": len(db.get_matches("IN_PLAY")),
        "scheduled": len(db.get_matches("SCHEDULED")),
        "api_enabled": bool(FOOTBALL_DATA_API_KEY),
    }


@router.get("/live")
def live():
    """Datos en vivo: marcadores, proximo partido, partido destacado,
    resultados recientes y progreso del torneo."""
    in_play = db.get_matches("IN_PLAY")
    scheduled = db.get_matches("SCHEDULED")
    finished = db.get_matches("FINISHED")
    now = datetime.now(timezone.utc).isoformat()

    upcoming = [m for m in scheduled if (m["utc_date"] or "") >= now]
    upcoming.sort(key=lambda m: m["utc_date"] or "")

    # Partido destacado: el próximo con mayor nivel (suma de Elo de ambos equipos).
    elos = {t["name"]: t["elo"] for t in db.get_teams()}
    featured = None
    if upcoming:
        featured = max(
            upcoming[:20],
            key=lambda m: elos.get(m["home"], 1500) + elos.get(m["away"], 1500),
        )

    # Resultados recientes (ultimos jugados).
    recent = [m for m in finished if m["home_goals"] is not None]
    recent.sort(key=lambda m: m["utc_date"] or "", reverse=True)

    total = len(scheduled) + len(finished) + len(in_play)
    played = int(db.get_meta("played_count", "0") or 0) or len(finished)
    return {
        "server_time": now,
        "in_play": in_play,
        "next_match": upcoming[0] if upcoming else None,
        "featured": featured,
        "upcoming": upcoming[:6],
        "recent": recent[:6],
        "progress": {
            "played": played,
            "total": total,
            "pct": round(played / total, 4) if total else 0,
        },
    }


@router.get("/models")
def models():
    return registry.list_models()


@router.get("/teams")
def teams():
    return db.get_teams()


@router.get("/matches")
def matches(status: str | None = Query(None)):
    return db.get_matches(status)


@router.get("/standings")
def standings():
    # Si hay clasificaciones reales (scrapeadas) con partidos jugados, se usan.
    raw = db.get_meta("standings_scraped")
    if raw:
        try:
            data = json.loads(raw)
        except Exception:
            data = None
        if data and any(r.get("pld", 0) > 0 for rows in data.values() for r in rows):
            codes = {t["name"]: t["code"] for t in db.get_teams()}
            out = {}
            for grp, rows in data.items():
                lst = [{
                    "name": r["name"], "code": codes.get(r["name"], ""), "grp": grp,
                    "pj": r["pld"], "g": r["w"], "e": r["d"], "p": r["l"],
                    "gf": r["gf"], "gc": r["ga"], "dg": r["gf"] - r["ga"], "pts": r["pts"],
                } for r in rows]
                lst.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
                out[grp] = lst
            return dict(sorted(out.items()))

    # Fallback: calcular la clasificación desde los partidos finalizados.
    table = {t["name"]: {"name": t["name"], "code": t["code"], "grp": t["grp"],
                         "pj": 0, "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0,
                         "dg": 0, "pts": 0} for t in db.get_teams()}
    for m in db.get_matches("FINISHED"):
        if m["home_goals"] is None or m["away_goals"] is None:
            continue
        h, a = table.get(m["home"]), table.get(m["away"])
        if not h or not a:
            continue
        hg, ag = m["home_goals"], m["away_goals"]
        for tt, gf, gc in ((h, hg, ag), (a, ag, hg)):
            tt["pj"] += 1; tt["gf"] += gf; tt["gc"] += gc; tt["dg"] += gf - gc
        if hg > ag:
            h["g"] += 1; h["pts"] += 3; a["p"] += 1
        elif ag > hg:
            a["g"] += 1; a["pts"] += 3; h["p"] += 1
        else:
            h["e"] += 1; a["e"] += 1; h["pts"] += 1; a["pts"] += 1
    grouped: dict[str, list] = {}
    for row in table.values():
        grouped.setdefault(row["grp"] or "?", []).append(row)
    for grp in grouped:
        grouped[grp].sort(key=lambda r: (r["pts"], r["dg"], r["gf"]), reverse=True)
    return dict(sorted(grouped.items()))


@router.get("/predict")
def predict(match_id: int = Query(...), model: str = Query(registry.DEFAULT_MODEL)):
    m = db.get_match(match_id)
    if not m:
        raise HTTPException(404, "Partido no encontrado")
    tmap = _team_map()
    home, away = tmap.get(m["home"]), tmap.get(m["away"])
    if not home or not away:
        raise HTTPException(422, "Equipos del partido no estan en la base de datos")
    pred = registry.predict_match(model, home, away)
    pred.update({"match_id": match_id, "utc_date": m["utc_date"],
                 "stage": m["stage"], "grp": m["grp"]})
    return pred


@router.get("/predictions")
def predictions(model: str = Query(registry.DEFAULT_MODEL),
                status: str = Query("SCHEDULED")):
    tmap = _team_map()
    out = []
    for m in db.get_matches(status):
        home, away = tmap.get(m["home"]), tmap.get(m["away"])
        if not home or not away:
            continue
        pred = registry.predict_match(model, home, away)
        pred.update({"match_id": m["id"], "utc_date": m["utc_date"],
                     "stage": m["stage"], "grp": m["grp"]})
        out.append(pred)
    return out


@router.get("/simulate")
def simulate(n: int = Query(2000, ge=200, le=8000), base: str = Query("poisson")):
    return montecarlo.simulate(n_sims=n, base_model=base)


@router.get("/evaluation")
def evaluation_endpoint():
    return evaluation.backtest(include_live=True)


@router.post("/refresh")
def refresh():
    # En modo publico no permitimos forzar la recarga desde fuera: la
    # actualizacion la hace el planificador diario de forma automatica.
    if PUBLIC_MODE:
        raise HTTPException(403, "Recarga manual deshabilitada en modo publico")
    return JSONResponse(ingestion.run_update())
