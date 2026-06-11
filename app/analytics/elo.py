# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Modelo Elo (probabilidad 1/X/2 segun diferencia de rating)."""
from __future__ import annotations

import math

from ..core.config import GOALS_PER_100_ELO, HOME_ADVANTAGE_ELO, WC_AVG_GOALS
from . import poisson_math

KEY = "elo"
NAME = "Elo (fuerza de equipos)"
DESC = ("Calcula la probabilidad de victoria/empate/derrota a partir de la "
        "diferencia de rating Elo, que se actualiza con cada resultado.")
DRAW_BASE = 0.28


def match_lambdas(home: dict, away: dict) -> tuple[float, float]:
    diff = home["elo"] + HOME_ADVANTAGE_ELO - away["elo"]
    supremacy = (diff / 100.0) * GOALS_PER_100_ELO
    half = WC_AVG_GOALS / 2.0
    return max(0.15, half + supremacy / 2.0), max(0.15, half - supremacy / 2.0)


def predict(home: dict, away: dict) -> dict:
    diff = home["elo"] + HOME_ADVANTAGE_ELO - away["elo"]
    exp_home = 1.0 / (1.0 + 10 ** (-diff / 400.0))
    p_draw = DRAW_BASE * math.exp(-((diff / 300.0) ** 2))
    p_home = max(exp_home - p_draw / 2.0, 0.0)
    p_away = max((1.0 - exp_home) - p_draw / 2.0, 0.0)
    total = p_home + p_draw + p_away
    p_home, p_draw, p_away = p_home / total, p_draw / total, p_away / total

    lh, la = match_lambdas(home, away)
    scores = poisson_math.outcomes_from_matrix(poisson_math.score_matrix(lh, la))
    return {
        "model": KEY, "home": home["name"], "away": away["name"],
        "prob_home": round(p_home, 4), "prob_draw": round(p_draw, 4),
        "prob_away": round(p_away, 4),
        "expected_home_goals": round(lh, 2), "expected_away_goals": round(la, 2),
        "most_likely_score": scores["most_likely_score"],
        "top_scores": scores["top_scores"], "over_2_5": scores["over_2_5"],
        "btts": scores["btts"],
    }
