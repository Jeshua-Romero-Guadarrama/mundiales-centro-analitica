# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Utilidades de probabilidad de marcadores (distribucion de Poisson)."""
from __future__ import annotations

import numpy as np
from scipy.stats import poisson

from ..core.config import MAX_GOALS_GRID


def score_matrix(lambda_home: float, lambda_away: float, max_goals: int = MAX_GOALS_GRID) -> np.ndarray:
    home_p = poisson.pmf(np.arange(max_goals + 1), max(lambda_home, 1e-6))
    away_p = poisson.pmf(np.arange(max_goals + 1), max(lambda_away, 1e-6))
    matrix = np.outer(home_p, away_p)
    total = matrix.sum()
    if total > 0:
        matrix /= total
    return matrix


def outcomes_from_matrix(matrix: np.ndarray) -> dict:
    n = matrix.shape[0]
    p_home = float(np.tril(matrix, -1).sum())
    p_draw = float(np.trace(matrix))
    p_away = float(np.triu(matrix, 1).sum())

    flat = [(i, j, float(matrix[i, j])) for i in range(n) for j in range(n)]
    flat.sort(key=lambda x: x[2], reverse=True)
    top = [{"score": f"{i}-{j}", "prob": round(p, 4)} for i, j, p in flat[:5]]
    ml = f"{flat[0][0]}-{flat[0][1]}" if flat else None

    over = sum(matrix[i, j] for i in range(n) for j in range(n) if i + j >= 3)
    btts = float(matrix[1:, 1:].sum())

    return {
        "prob_home": round(p_home, 4), "prob_draw": round(p_draw, 4),
        "prob_away": round(p_away, 4), "most_likely_score": ml,
        "top_scores": top, "over_2_5": round(float(over), 4),
        "btts": round(btts, 4),
    }
