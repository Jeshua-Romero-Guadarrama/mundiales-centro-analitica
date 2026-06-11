# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Simulacion Monte Carlo del torneo completo."""
from __future__ import annotations

import numpy as np

from ..infrastructure import database as db
from . import elo as elo_model
from . import poisson as poisson_model

KEY = "montecarlo"
NAME = "Monte Carlo (simulacion del torneo)"
DESC = ("Simula el torneo miles de veces para estimar la probabilidad de que "
        "cada seleccion gane su grupo, avance y conquiste el Mundial.")
BASE_MODELS = {"poisson": poisson_model, "elo": elo_model}


def _lambda_cache(base):
    cache: dict[tuple[str, str], tuple[float, float]] = {}

    def get(home, away):
        k = (home["name"], away["name"])
        if k not in cache:
            cache[k] = base.match_lambdas(home, away)
        return cache[k]
    return get


def simulate(n_sims: int = 2000, base_model: str = "poisson") -> dict:
    base = BASE_MODELS.get(base_model, poisson_model)
    teams = db.get_teams()
    if not teams:
        return {"sims": 0, "teams": []}
    by_name = {t["name"]: t for t in teams}
    lam = _lambda_cache(base)
    rng = np.random.default_rng()

    groups: dict[str, list[str]] = {}
    for t in teams:
        groups.setdefault(t["grp"] or "?", []).append(t["name"])

    finished, scheduled = [], []
    for m in db.get_matches():
        if (m["stage"] or "").upper().startswith("GROUP") or m["grp"]:
            if m["status"] == "FINISHED" and m["home_goals"] is not None:
                finished.append(m)
            elif m["status"] != "FINISHED":
                scheduled.append(m)

    tally = {t["name"]: {"win_group": 0, "qualify": 0, "qf": 0, "sf": 0,
                         "final": 0, "champion": 0} for t in teams}

    def sample(hn, an):
        lh, la = lam(by_name[hn], by_name[an])
        return int(rng.poisson(lh)), int(rng.poisson(la))

    def winner_ko(hn, an):
        hg, ag = sample(hn, an)
        if hg != ag:
            return hn if hg > ag else an
        p = 1.0 / (1.0 + 10 ** (-(by_name[hn]["elo"] - by_name[an]["elo"]) / 400.0))
        return hn if rng.random() < p else an

    round_names = {8: "qf", 4: "sf", 2: "final"}

    for _ in range(n_sims):
        stand = {n: {"pts": 0, "gd": 0, "gf": 0} for n in by_name}
        for m in finished:
            _apply(stand, m["home"], m["away"], m["home_goals"], m["away_goals"])
        for m in scheduled:
            hg, ag = sample(m["home"], m["away"])
            _apply(stand, m["home"], m["away"], hg, ag)

        thirds, qualifiers = [], []
        for names in groups.values():
            ranked = sorted(names, key=lambda nm: (stand[nm]["pts"], stand[nm]["gd"],
                            stand[nm]["gf"], rng.random()), reverse=True)
            if ranked:
                tally[ranked[0]]["win_group"] += 1
            for pos, nm in enumerate(ranked):
                seed = stand[nm]["pts"] * 100 + stand[nm]["gd"]
                if pos < 2:
                    qualifiers.append((seed, nm))
                elif pos == 2:
                    thirds.append((seed, nm))
        thirds.sort(reverse=True)
        qualifiers.extend(thirds[:8])
        for _s, nm in qualifiers:
            tally[nm]["qualify"] += 1

        bracket = [nm for _s, nm in sorted(qualifiers, reverse=True)]
        size = 1
        while size * 2 <= len(bracket):
            size *= 2
        bracket = bracket[:size]
        while len(bracket) > 1:
            stage = len(bracket)
            nxt = [winner_ko(bracket[i], bracket[stage - 1 - i]) for i in range(stage // 2)]
            half = stage // 2
            if half in round_names:
                for nm in nxt:
                    tally[nm][round_names[half]] += 1
            bracket = nxt
        if len(bracket) == 1:
            tally[bracket[0]]["champion"] += 1

    out = []
    for t in teams:
        c = tally[t["name"]]
        out.append({"name": t["name"], "code": t["code"], "grp": t["grp"], "elo": t["elo"],
                    **{k: round(v / n_sims, 4) for k, v in c.items()}})
    out.sort(key=lambda x: x["champion"], reverse=True)
    return {"sims": n_sims, "base_model": base_model, "teams": out}


def _apply(stand, home, away, hg, ag):
    if home not in stand or away not in stand:
        return
    stand[home]["gf"] += hg; stand[home]["gd"] += hg - ag
    stand[away]["gf"] += ag; stand[away]["gd"] += ag - hg
    if hg > ag:
        stand[home]["pts"] += 3
    elif ag > hg:
        stand[away]["pts"] += 3
    else:
        stand[home]["pts"] += 1; stand[away]["pts"] += 1
