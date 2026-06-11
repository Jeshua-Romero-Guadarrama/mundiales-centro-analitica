# 🏆 Mundiales · Centro de Analítica

Aplicación de analítica deportiva para el Mundial. Obtiene datos por **web
scraping**, genera **predicciones con varios modelos estadísticos** (resultado,
marcador, probabilidades, campeón) y **valida y calibra** esos modelos con
métricas de ciencia de datos. Incluye un panel **en vivo** y se actualiza a diario.

Construida con **Python + FastAPI** sobre una **arquitectura por capas** y
desplegable con **Docker**.

---

## 🚀 Ejecutar con Docker

```bash
docker compose up -d --build
```

Abre **http://localhost:8000**

```bash
docker compose logs -f     # registros
docker compose down        # detener
```

## 🖥️ Ejecutar sin Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

---

## 📊 Modelos (se eligen en la web)

| Modelo | Qué hace |
|--------|----------|
| **Poisson** | Goles por equipo (ataque/defensa) → probabilidad de cada marcador exacto. |
| **Elo** | Probabilidad 1/X/2 según la fuerza de cada selección. |
| **Aprendizaje automático** | Regresión entrenada con los partidos ya jugados. |
| **Monte Carlo** | Simula el torneo miles de veces → probabilidad de ser campeón. |

## 🧪 Calibración

Validación *walk-forward* sobre datos reales, con métricas (precisión, log-loss,
Brier, RPS), diagrama de fiabilidad y gráficos de diagnóstico.

## ⚡ En vivo

Reloj, cuenta atrás al próximo partido, partido destacado, favoritos al título,
progreso del torneo y clasificaciones actualizadas.

---

## 🗂️ Arquitectura

```
app/
  core/           Configuración
  domain/         Entidades del negocio
  infrastructure/ Base de datos y fuentes de datos
  analytics/      Modelos estadísticos y evaluación
  services/       Ingesta y planificador
  api/            Rutas REST
  web/static/     Interfaz
```

Detalle en [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

**Autor:** Jeshua Romero Guadarrama · Licencia MIT.
