# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Registro unico de modelos: la web elige cual usar."""
from __future__ import annotations

from . import elo, ml, montecarlo, poisson

MATCH_MODELS = {poisson.KEY: poisson, elo.KEY: elo, ml.KEY: ml}
DEFAULT_MODEL = poisson.KEY


def list_models() -> list[dict]:
    items = [{"key": m.KEY, "name": m.NAME, "desc": m.DESC, "kind": "match"}
             for m in MATCH_MODELS.values()]
    items.append({"key": montecarlo.KEY, "name": montecarlo.NAME,
                  "desc": montecarlo.DESC, "kind": "tournament"})
    return items


def predict_match(model_key: str, home: dict, away: dict) -> dict:
    model = MATCH_MODELS.get(model_key, MATCH_MODELS[DEFAULT_MODEL])
    return model.predict(home, away)
