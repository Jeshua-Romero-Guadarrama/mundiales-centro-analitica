# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Datos del Mundial 2026: las 48 selecciones reales y sus 12 grupos (A-L).

La composicion de los grupos es la REAL del sorteo del Mundial 2026, obtenida
por web scraping de Wikipedia y fijada aqui para que la app funcione siempre,
incluso sin conexion. El motor de scraping sigue activo para incorporar los
RESULTADOS en cuanto se juegan los partidos.

Los valores Elo iniciales siguen la escala "World Football Elo" y se recalculan
con cada resultado del torneo.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import combinations

# Grupo -> [(nombre, codigo FIFA, elo inicial), ...]  (sorteo real del Mundial 2026)
GROUPS: dict[str, list[tuple[str, str, float]]] = {
    "A": [("Mexico", "MEX", 1860), ("South Korea", "KOR", 1790),
          ("Czech Republic", "CZE", 1810), ("South Africa", "RSA", 1730)],
    "B": [("Canada", "CAN", 1770), ("Bosnia and Herzegovina", "BIH", 1730),
          ("Qatar", "QAT", 1690), ("Switzerland", "SUI", 1865)],
    "C": [("Brazil", "BRA", 2000), ("Morocco", "MAR", 1890),
          ("Haiti", "HAI", 1600), ("Scotland", "SCO", 1790)],
    "D": [("United States", "USA", 1840), ("Paraguay", "PAR", 1740),
          ("Australia", "AUS", 1755), ("Turkey", "TUR", 1840)],
    "E": [("Germany", "GER", 1930), ("Curacao", "CUW", 1590),
          ("Ivory Coast", "CIV", 1800), ("Ecuador", "ECU", 1825)],
    "F": [("Netherlands", "NED", 1975), ("Japan", "JPN", 1845),
          ("Sweden", "SWE", 1800), ("Tunisia", "TUN", 1720)],
    "G": [("Belgium", "BEL", 1940), ("Egypt", "EGY", 1785),
          ("Iran", "IRN", 1795), ("New Zealand", "NZL", 1660)],
    "H": [("Spain", "ESP", 2050), ("Cape Verde", "CPV", 1655),
          ("Saudi Arabia", "KSA", 1690), ("Uruguay", "URU", 1895)],
    "I": [("France", "FRA", 2060), ("Senegal", "SEN", 1855),
          ("Iraq", "IRQ", 1680), ("Norway", "NOR", 1900)],
    "J": [("Argentina", "ARG", 2090), ("Algeria", "ALG", 1790),
          ("Austria", "AUT", 1825), ("Jordan", "JOR", 1670)],
    "K": [("Portugal", "POR", 1990), ("DR Congo", "COD", 1730),
          ("Uzbekistan", "UZB", 1700), ("Colombia", "COL", 1900)],
    "L": [("England", "ENG", 2010), ("Croatia", "CRO", 1895),
          ("Ghana", "GHA", 1745), ("Panama", "PAN", 1700)],
}


def seed_teams() -> list[dict]:
    """Devuelve las 48 selecciones con su grupo, codigo y Elo inicial."""
    out = []
    for grp, teams in GROUPS.items():
        for name, code, elo in teams:
            out.append({"name": name, "code": code, "grp": grp, "elo": float(elo)})
    return out


def seed_fixtures() -> list[dict]:
    """Genera el calendario de la fase de grupos (todos contra todos).

    Son los enfrentamientos REALES de cada grupo (p. ej. Mexico-Sudafrica);
    las fechas se reparten a lo largo de la fase de grupos del Mundial 2026.
    6 partidos por grupo x 12 grupos = 72 partidos.
    """
    fixtures: list[dict] = []
    base = datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc)
    day = 0
    for grp, teams in GROUPS.items():
        names = [t[0] for t in teams]
        for i, (home, away) in enumerate(combinations(names, 2)):
            utc = base + timedelta(days=day, hours=(i % 3) * 4)
            fixtures.append({
                "ext_id": f"wc26-{grp}-{home}-{away}".replace(" ", "_"),
                "utc_date": utc.isoformat(),
                "stage": "GROUP_STAGE", "grp": grp,
                "home": home, "away": away,
                "status": "SCHEDULED", "source": "fixtures-2026",
            })
        day += 1
    return fixtures
