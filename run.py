# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Punto de arranque del Dashboard del Mundial.

Uso:  python run.py
Luego abre http://127.0.0.1:8000 en tu navegador.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
