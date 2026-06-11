# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Ensamblado de la aplicacion (composition root).

Arquitectura por capas:
    core           -> configuracion
    domain         -> entidades y esquemas de negocio
    infrastructure -> base de datos y fuentes externas (API, scraping)
    analytics      -> modelos estadisticos y evaluacion
    services       -> orquestacion (ingesta, planificador)
    api            -> rutas REST
    web            -> interfaz (HTML/CSS/JS)
"""
from __future__ import annotations

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .core.config import ALLOWED_ORIGINS, PUBLIC_MODE, STATIC_DIR
from .services import ingestion
from .services.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    ingestion.ensure_seeded()
    threading.Thread(target=_safe_update, daemon=True).start()
    start_scheduler()
    yield


def _safe_update():
    try:
        ingestion.run_update()
    except Exception as exc:
        print(f"[startup] actualizacion inicial fallo: {exc}")


def create_app() -> FastAPI:
    # En modo publico se oculta la documentacion interna de la API.
    docs = None if PUBLIC_MODE else "/docs"
    app = FastAPI(title="Mundial 2026 - Centro de Analitica", version="1.0",
                  lifespan=lifespan, docs_url=docs, redoc_url=None,
                  openapi_url=None if PUBLIC_MODE else "/openapi.json")

    if ALLOWED_ORIGINS:
        app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS,
                           allow_methods=["GET", "POST"], allow_headers=["*"])

    @app.middleware("http")
    async def cabeceras_seguridad(request: Request, call_next):
        """Anade cabeceras de seguridad a cada respuesta (defensa basica)."""
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return resp

    app.include_router(router)

    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
