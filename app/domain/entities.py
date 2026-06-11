# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Entidades del dominio y esquemas de respuesta de la API.

Capa de dominio: define las formas de datos del negocio (selecciones,
partidos, predicciones). No depende de infraestructura ni de frameworks web.
"""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

# --- Constantes del torneo ---
GROUP_COUNT = 12
TEAMS_PER_GROUP = 4
QUALIFIERS = 32  # 2 por grupo + 8 mejores terceros


@dataclass(slots=True)
class Team:
    name: str
    code: str
    grp: str
    elo: float
    attack: float = 1.0
    defense: float = 1.0


@dataclass(slots=True)
class Match:
    id: int
    home: str
    away: str
    utc_date: str | None
    stage: str | None
    grp: str | None
    home_goals: int | None
    away_goals: int | None
    status: str


# --- Esquemas de salida (API) ---
class MatchPrediction(BaseModel):
    model: str
    match_id: int | None = None
    home: str
    away: str
    prob_home: float
    prob_draw: float
    prob_away: float
    expected_home_goals: float | None = None
    expected_away_goals: float | None = None
    most_likely_score: str | None = None
    over_2_5: float | None = None
    btts: float | None = None
    note: str | None = None
