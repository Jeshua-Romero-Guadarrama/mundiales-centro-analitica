# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Recalculo de ratings (Elo + ataque/defensa) desde los partidos jugados."""
from __future__ import annotations

from ..core.config import ELO_K, HOME_ADVANTAGE_ELO, WC_AVG_GOALS
from ..infrastructure import database as db
from ..infrastructure.seed import GROUPS

PSEUDO_MATCHES = 4.0


def _base_elos() -> dict[str, float]:
    base = {}
    for teams in GROUPS.values():
        for name, _code, elo in teams:
            base[name] = float(elo)
    return base


def _finished_sorted() -> list[dict]:
    finished = [m for m in db.get_matches("FINISHED")
                if m["home_goals"] is not None and m["away_goals"] is not None]
    finished.sort(key=lambda m: (m["utc_date"] is None, m["utc_date"] or ""))
    return finished


def goal_multiplier(gd: int) -> float:
    gd = abs(gd)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8.0


def recompute_elo() -> dict[str, float]:
    base = _base_elos()
    elos = {t["name"]: base.get(t["name"], t["elo"] or 1500.0) for t in db.get_teams()}
    for m in _finished_sorted():
        h, a = m["home"], m["away"]
        elos.setdefault(h, 1500.0); elos.setdefault(a, 1500.0)
        diff = elos[h] + HOME_ADVANTAGE_ELO - elos[a]
        exp_h = 1.0 / (1.0 + 10 ** (-diff / 400.0))
        hg, ag = m["home_goals"], m["away_goals"]
        res_h = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
        delta = ELO_K * goal_multiplier(hg - ag) * (res_h - exp_h)
        elos[h] += delta; elos[a] -= delta
    for name, elo in elos.items():
        db.update_team_rating(name, elo=round(elo, 1))
    return elos


def recompute_attack_defense(elos: dict[str, float]) -> None:
    teams = db.get_teams()
    if not teams:
        return
    avg = WC_AVG_GOALS / 2.0
    field_avg = sum(elos.get(t["name"], 1500.0) for t in teams) / len(teams)
    stats = {t["name"]: {"n": 0, "gf": 0, "ga": 0} for t in teams}
    for m in _finished_sorted():
        for team, gf, ga in ((m["home"], m["home_goals"], m["away_goals"]),
                             (m["away"], m["away_goals"], m["home_goals"])):
            if team in stats:
                stats[team]["n"] += 1; stats[team]["gf"] += gf; stats[team]["ga"] += ga
    for t in teams:
        name = t["name"]; s = stats[name]
        tilt = (elos.get(name, 1500.0) - field_avg) / 200.0
        prior_s = min(max(avg + tilt * 0.5, 0.4), 2.6)
        prior_c = min(max(avg - tilt * 0.5, 0.4), 2.6)
        bs = (s["gf"] + prior_s * PSEUDO_MATCHES) / (s["n"] + PSEUDO_MATCHES)
        bc = (s["ga"] + prior_c * PSEUDO_MATCHES) / (s["n"] + PSEUDO_MATCHES)
        db.update_team_rating(name, attack=round(bs / avg, 4), defense=round(bc / avg, 4))


def recompute_all() -> None:
    recompute_attack_defense(recompute_elo())
