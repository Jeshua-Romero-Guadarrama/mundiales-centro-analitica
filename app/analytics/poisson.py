# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Modelo de Poisson (ataque/defensa, estilo Dixon-Coles)."""
from __future__ import annotations

from ..core.config import WC_AVG_GOALS
from . import poisson_math

HOME_MULT = 1.10
KEY = "poisson"
NAME = "Poisson (marcadores)"
DESC = ("Modela los goles de cada equipo con la distribucion de Poisson usando "
        "fuerzas de ataque y defensa. Da la probabilidad de cada marcador exacto.")


def match_lambdas(home: dict, away: dict) -> tuple[float, float]:
    avg = WC_AVG_GOALS / 2.0
    lh = avg * home["attack"] * away["defense"] * HOME_MULT
    la = avg * away["attack"] * home["defense"] / HOME_MULT
    return max(lh, 0.15), max(la, 0.15)


def predict(home: dict, away: dict) -> dict:
    lh, la = match_lambdas(home, away)
    out = poisson_math.outcomes_from_matrix(poisson_math.score_matrix(lh, la))
    out.update({"model": KEY, "home": home["name"], "away": away["name"],
                "expected_home_goals": round(lh, 2), "expected_away_goals": round(la, 2)})
    return out
