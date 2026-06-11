# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Conjunto historico real (Mundial 2022, Qatar) para calibrar/validar modelos.

Marcadores en tiempo reglamentario (90'). Las eliminatorias resueltas por
penaltis se registran como empate, que es el resultado en 90'. Se utiliza
exclusivamente como conjunto de validacion (backtest), de forma independiente
a los datos del torneo en curso.
"""
from __future__ import annotations

# (orden cronologico, home, away, goles_home, goles_away)
RESULTS_2022: list[tuple[str, str, int, int]] = [
    ("Qatar", "Ecuador", 0, 2),
    ("England", "Iran", 6, 2),
    ("Senegal", "Netherlands", 0, 2),
    ("USA", "Wales", 1, 1),
    ("Argentina", "Saudi Arabia", 1, 2),
    ("Denmark", "Tunisia", 0, 0),
    ("Mexico", "Poland", 0, 0),
    ("France", "Australia", 4, 1),
    ("Morocco", "Croatia", 0, 0),
    ("Germany", "Japan", 1, 2),
    ("Spain", "Costa Rica", 7, 0),
    ("Belgium", "Canada", 1, 0),
    ("Switzerland", "Cameroon", 1, 0),
    ("Uruguay", "Korea Republic", 0, 0),
    ("Portugal", "Ghana", 3, 2),
    ("Brazil", "Serbia", 2, 0),
    ("Netherlands", "Ecuador", 1, 1),
    ("England", "USA", 0, 0),
    ("Argentina", "Mexico", 2, 0),
    ("Poland", "Saudi Arabia", 2, 0),
    ("France", "Denmark", 2, 1),
    ("Spain", "Germany", 1, 1),
    ("Brazil", "Switzerland", 1, 0),
    ("Portugal", "Uruguay", 2, 0),
    ("Croatia", "Belgium", 0, 0),
    ("Japan", "Spain", 2, 1),
    ("Korea Republic", "Portugal", 2, 1),
    ("Cameroon", "Brazil", 1, 0),
    # --- Octavos ---
    ("Netherlands", "USA", 3, 1),
    ("Argentina", "Australia", 2, 1),
    ("France", "Poland", 3, 1),
    ("England", "Senegal", 3, 0),
    ("Japan", "Croatia", 1, 1),
    ("Brazil", "Korea Republic", 4, 1),
    ("Morocco", "Spain", 0, 0),
    ("Portugal", "Switzerland", 6, 1),
    # --- Cuartos ---
    ("Croatia", "Brazil", 1, 1),
    ("Netherlands", "Argentina", 2, 2),
    ("Morocco", "Portugal", 1, 0),
    ("England", "France", 1, 2),
    # --- Semifinales ---
    ("Argentina", "Croatia", 3, 0),
    ("France", "Morocco", 2, 0),
    # --- Tercer puesto y final ---
    ("Croatia", "Morocco", 2, 1),
    ("Argentina", "France", 3, 3),
]

# Elos prior aproximados de selecciones de 2022 cuyo nombre no coincide con el
# del cuadro 2026 (o que no participan en 2026). Asi la calibracion sobre datos
# reales de 2022 mantiene ratings sensatos para todos los equipos.
EXTRA_PRIOR_ELO: dict[str, float] = {
    "USA": 1840.0,
    "Korea Republic": 1790.0,
    "Wales": 1760.0,
    "Cameroon": 1740.0,
    "Denmark": 1835.0,
    "Poland": 1790.0,
    "Costa Rica": 1705.0,
    "Serbia": 1800.0,
}
