# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Modelo de Machine Learning (regresion logistica multinomial)."""
from __future__ import annotations

from ..infrastructure import database as db
from . import elo as elo_model
from . import poisson as poisson_model

KEY = "ml"
NAME = "Aprendizaje automático (ML)"
DESC = ("Regresión logística multinomial entrenada con los partidos disputados "
        "del torneo para estimar la probabilidad de cada resultado.")
MIN_MATCHES = 12
_cache = {"n": -1, "clf": None}


def _features(home: dict, away: dict) -> list[float]:
    return [home["elo"] - away["elo"], home["attack"] - away["attack"],
            away["defense"] - home["defense"]]


def _train():
    try:
        from sklearn.linear_model import LogisticRegression
    except Exception:
        return None
    finished = [m for m in db.get_matches("FINISHED")
                if m["home_goals"] is not None and m["away_goals"] is not None]
    if len(finished) < MIN_MATCHES:
        return None
    teams = {t["name"]: t for t in db.get_teams()}
    X, y = [], []
    for m in finished:
        h, a = teams.get(m["home"]), teams.get(m["away"])
        if not h or not a:
            continue
        X.append(_features(h, a))
        hg, ag = m["home_goals"], m["away_goals"]
        y.append(2 if hg > ag else (1 if hg == ag else 0))
    if len(set(y)) < 2:
        return None
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X, y)
    return clf


def _get_clf():
    key = len(db.get_matches("FINISHED"))
    if _cache["n"] != key:
        _cache["clf"] = _train()
        _cache["n"] = key
    return _cache["clf"]


def predict(home: dict, away: dict) -> dict:
    clf = _get_clf()
    if clf is None:
        e, p = elo_model.predict(home, away), poisson_model.predict(home, away)
        out = dict(p); out["model"] = KEY
        out["prob_home"] = round((e["prob_home"] + p["prob_home"]) / 2, 4)
        out["prob_draw"] = round((e["prob_draw"] + p["prob_draw"]) / 2, 4)
        out["prob_away"] = round((e["prob_away"] + p["prob_away"]) / 2, 4)
        out["note"] = "Estimación combinada de los modelos Elo y Poisson."
        return out
    classes = list(clf.classes_)
    proba = clf.predict_proba([_features(home, away)])[0]
    pm = {c: float(proba[i]) for i, c in enumerate(classes)}
    p = poisson_model.predict(home, away)
    return {
        "model": KEY, "home": home["name"], "away": away["name"],
        "prob_home": round(pm.get(2, 0.0), 4), "prob_draw": round(pm.get(1, 0.0), 4),
        "prob_away": round(pm.get(0, 0.0), 4),
        "expected_home_goals": p["expected_home_goals"],
        "expected_away_goals": p["expected_away_goals"],
        "most_likely_score": p["most_likely_score"], "top_scores": p["top_scores"],
        "over_2_5": p["over_2_5"], "btts": p["btts"],
        "note": "Entrenado con los resultados disputados del torneo.",
    }
