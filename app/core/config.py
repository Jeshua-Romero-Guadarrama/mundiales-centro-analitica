# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Configuracion central (capa core). Sin dependencias de otras capas."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Raiz del proyecto:  app/core/config.py -> parents[2]
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# --- Rutas ---
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "mundial.db"
STATIC_DIR = Path(__file__).resolve().parents[1] / "web" / "static"

# --- Modo publico ---
# En despliegue en internet conviene PUBLIC_MODE=1: sirve solo la web y su API
# publica, sin documentacion interna ni recarga manual.
PUBLIC_MODE = os.getenv("PUBLIC_MODE", "0").strip().lower() in {"1", "true", "yes", "si"}
# Origenes permitidos para CORS (separados por comas). Por defecto, ninguno
# externo: la web se sirve desde el mismo origen, asi que no hace falta abrir CORS.
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

# --- Fuente de datos: API (football-data.org) ---
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "").strip()
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"
COMPETITION_CODE = "WC"

# --- Fuente de datos: scraping (Wikipedia) ---
WIKI_URLS = [
    "https://es.wikipedia.org/wiki/Copa_Mundial_de_F%C3%BAtbol_de_2026",
    "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup",
]
USER_AGENT = "DashboardMundial/1.0 (proyecto local; analitica deportiva)"

# --- Actualizacion diaria ---
DAILY_UPDATE_HOUR = int(os.getenv("DAILY_UPDATE_HOUR", "6"))
DAILY_UPDATE_MINUTE = int(os.getenv("DAILY_UPDATE_MINUTE", "0"))

# --- Parametros de los modelos ---
HOME_ADVANTAGE_ELO = 65.0
WC_AVG_GOALS = 2.6
ELO_K = 40.0
GOALS_PER_100_ELO = 0.40
MAX_GOALS_GRID = 8
