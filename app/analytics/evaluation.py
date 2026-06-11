# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Backtest y calibracion de los modelos (capa de analitica).

Ejecuta una validacion *walk-forward* (sin mirar el futuro): para cada partido
se predice con el estado de los ratings ANTES de jugarse y despues se revela el
resultado y se actualiza el estado. Calcula metricas estandar de calidad
probabilistica usadas en ciencia de datos deportiva:

  - Precision (acierto del resultado mas probable)
  - Log-loss (verosimilitud; menor = mejor)
  - Brier score multiclase (error cuadratico; menor = mejor)
  - RPS (Ranked Probability Score, penaliza segun el orden 1/X/2; menor = mejor)
  - Diagrama de fiabilidad (confianza prevista vs acierto observado)
"""
from __future__ import annotations

import math

import numpy as np

from ..core.config import HOME_ADVANTAGE_ELO, ELO_K, WC_AVG_GOALS
from ..infrastructure import database as db
from ..infrastructure.seed import GROUPS
from . import elo as elo_model
from . import poisson as poisson_model
from .historical import EXTRA_PRIOR_ELO, RESULTS_2022
from .ratings import goal_multiplier

MIN_ML = 12
EPS = 1e-12


def _priors() -> dict[str, float]:
    base = {name: float(elo) for teams in GROUPS.values() for name, _c, elo in teams}
    base.update(EXTRA_PRIOR_ELO)
    return base


def _dataset(include_live: bool) -> tuple[list[tuple], str]:
    data = list(RESULTS_2022)
    label = "Mundial 2022 (datos reales)"
    if include_live:
        live = [(m["home"], m["away"], m["home_goals"], m["away_goals"])
                for m in db.get_matches("FINISHED")
                if m["home_goals"] is not None and m["away_goals"] is not None]
        if live:
            data = data + live
            label = f"Mundial 2022 + {len(live)} partidos de 2026"
    return data, label


def _team_dict(name, elos, stats, field_avg) -> dict:
    avg = WC_AVG_GOALS / 2.0
    elo = elos.get(name, 1500.0)
    s = stats.get(name, {"n": 0, "gf": 0, "ga": 0})
    tilt = (elo - field_avg) / 200.0
    prior_s = min(max(avg + tilt * 0.5, 0.4), 2.6)
    prior_c = min(max(avg - tilt * 0.5, 0.4), 2.6)
    bs = (s["gf"] + prior_s * 4.0) / (s["n"] + 4.0)
    bc = (s["ga"] + prior_c * 4.0) / (s["n"] + 4.0)
    return {"name": name, "elo": elo, "attack": bs / avg, "defense": bc / avg}


def _probs(pred: dict) -> list[float]:
    return [pred["prob_home"], pred["prob_draw"], pred["prob_away"]]


def _metrics(records: list[tuple[list[float], int]]) -> dict:
    if not records:
        return {"n": 0}
    acc = ll = brier = rps = 0.0
    bins = {i: {"conf_sum": 0.0, "hits": 0, "n": 0} for i in range(10)}
    for probs, actual in records:
        p = np.clip(np.array(probs, dtype=float), EPS, 1.0)
        p = p / p.sum()
        pred_cls = int(np.argmax(p))
        acc += 1.0 if pred_cls == actual else 0.0
        ll += -math.log(p[actual])
        y = np.zeros(3); y[actual] = 1.0
        brier += float(np.sum((p - y) ** 2))
        cum_p = np.cumsum(p); cum_y = np.cumsum(y)
        rps += float(np.sum((cum_p[:-1] - cum_y[:-1]) ** 2)) / 2.0
        conf = float(p[pred_cls])
        b = min(int(conf * 10), 9)
        bins[b]["conf_sum"] += conf
        bins[b]["hits"] += 1 if pred_cls == actual else 0
        bins[b]["n"] += 1
    n = len(records)
    reliability = [
        {"conf": round(v["conf_sum"] / v["n"], 3), "acc": round(v["hits"] / v["n"], 3),
         "n": v["n"]}
        for v in bins.values() if v["n"] > 0
    ]
    return {
        "n": n,
        "accuracy": round(acc / n, 4),
        "log_loss": round(ll / n, 4),
        "brier": round(brier / n, 4),
        "rps": round(rps / n, 4),
        "reliability": reliability,
    }


_CACHE: dict = {"key": None, "result": None}


def backtest(include_live: bool = True) -> dict:
    data, label = _dataset(include_live)
    # El backtest es determinista dado el conjunto de partidos: se cachea para
    # no recalcular la validacion completa en cada visita (coste alto de CPU).
    cache_key = (len(data), include_live)
    if _CACHE["key"] == cache_key and _CACHE["result"] is not None:
        return _CACHE["result"]
    priors = _priors()
    field_avg = sum(priors.values()) / len(priors)
    elos = dict(priors)
    stats: dict[str, dict] = {}

    rec = {"elo": [], "poisson": [], "ml": []}
    X, y = [], []
    base_counts = {0: 0, 1: 0, 2: 0}

    try:
        from sklearn.linear_model import LogisticRegression
        have_sklearn = True
    except Exception:
        have_sklearn = False

    for home, away, hg, ag in data:
        hd = _team_dict(home, elos, stats, field_avg)
        ad = _team_dict(away, elos, stats, field_avg)
        actual = 0 if hg > ag else (1 if hg == ag else 2)  # 0 local,1 empate,2 visit

        rec["elo"].append((_probs(elo_model.predict(hd, ad)), actual))
        rec["poisson"].append((_probs(poisson_model.predict(hd, ad)), actual))

        feats = [hd["elo"] - ad["elo"], hd["attack"] - ad["attack"],
                 ad["defense"] - hd["defense"]]
        if have_sklearn and len(X) >= MIN_ML and len(set(y)) >= 2:
            clf = LogisticRegression(max_iter=1000).fit(X, y)
            proba = clf.predict_proba([feats])[0]
            cls = list(clf.classes_)
            pm = {c: float(proba[i]) for i, c in enumerate(cls)}
            ml_probs = [pm.get(2, 0.0), pm.get(1, 0.0), pm.get(0, 0.0)]
        else:
            ep = _probs(elo_model.predict(hd, ad))
            pp = _probs(poisson_model.predict(hd, ad))
            ml_probs = [(ep[i] + pp[i]) / 2 for i in range(3)]
        rec["ml"].append((ml_probs, actual))

        # ---- revelar y actualizar estado ----
        diff = elos.get(home, 1500.0) + HOME_ADVANTAGE_ELO - elos.get(away, 1500.0)
        exp_h = 1.0 / (1.0 + 10 ** (-diff / 400.0))
        res_h = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
        delta = ELO_K * goal_multiplier(hg - ag) * (res_h - exp_h)
        elos[home] = elos.get(home, 1500.0) + delta
        elos[away] = elos.get(away, 1500.0) - delta
        for team, gf, ga in ((home, hg, ag), (away, ag, hg)):
            s = stats.setdefault(team, {"n": 0, "gf": 0, "ga": 0})
            s["n"] += 1; s["gf"] += gf; s["ga"] += ga
        # etiqueta ML: 2 local, 1 empate, 0 visitante
        y.append(2 if hg > ag else (1 if hg == ag else 0))
        X.append(feats)
        base_counts[actual] += 1

    n = len(data)
    majority = max(base_counts.values()) / n if n else 0
    out_models = {}
    for key, model in (("elo", elo_model), ("poisson", poisson_model), ("ml", None)):
        m = _metrics(rec[key])
        m["key"] = key
        out_models[key] = m

    result = {
        "dataset": label,
        "n_matches": n,
        "baseline": {
            "log_loss_uniforme": round(math.log(3), 4),  # 1.0986 (azar 1/X/2)
            "accuracy_mayoritaria": round(majority, 4),
        },
        "models": out_models,
        "tips": _improvement_tips(out_models, n),
    }
    _CACHE["key"], _CACHE["result"] = cache_key, result
    return result


def _improvement_tips(models: dict, n: int) -> list[str]:
    tips = [
        f"Tamano de muestra actual: {n} partidos. Mas partidos reducen la "
        "varianza de las metricas y mejoran sobre todo al modelo de ML.",
        "Anade variables: descanso entre partidos, bajas/lesiones, viajes, "
        "altitud y forma reciente (ultimos 5) para enriquecer el modelo de ML.",
        "Calibra las probabilidades con Platt scaling o regresion isotonica si "
        "el diagrama de fiabilidad se aleja de la diagonal.",
        "Ajusta la ventaja de localia y el factor K del Elo por validacion "
        "cruzada minimizando el RPS.",
        "En Poisson, prueba el ajuste de Dixon-Coles para marcadores bajos "
        "(0-0, 1-0, 0-1, 1-1), que estan correlacionados.",
    ]
    best = min(models.values(), key=lambda m: m.get("rps", 9))
    tips.insert(0, f"Mejor modelo ahora por RPS: '{best['key']}' "
                   f"(RPS {best.get('rps')}, precision {best.get('accuracy')}).")
    return tips
