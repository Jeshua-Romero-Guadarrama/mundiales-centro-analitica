# Arquitectura

El proyecto sigue una **arquitectura por capas** inspirada en *Clean
Architecture*: las dependencias apuntan siempre hacia el interior (dominio), y
los detalles (base de datos, API externa, web) quedan en los bordes.

```
┌─────────────────────────────────────────────────────────────┐
│  web/ (HTML·CSS·JS)        api/ (FastAPI routers)            │  Presentación
├─────────────────────────────────────────────────────────────┤
│  services/  (ingesta, planificador) — orquestación de casos  │  Aplicación
├─────────────────────────────────────────────────────────────┤
│  analytics/ (poisson, elo, ml, montecarlo, ratings,          │  Analítica /
│              evaluation)                                     │  Dominio
│  domain/    (entidades y esquemas)                           │
├─────────────────────────────────────────────────────────────┤
│  infrastructure/ database(SQLite) · sources(API, scraping)   │  Infraestructura
│  core/           configuración                               │
└─────────────────────────────────────────────────────────────┘
```

## Regla de dependencias

- `core` no depende de nadie.
- `domain` define entidades; no conoce frameworks.
- `infrastructure` implementa el acceso a datos (SQLite) y a fuentes externas
  (football-data.org, Wikipedia).
- `analytics` contiene la lógica de modelos; depende de `infrastructure` solo
  para leer datos ya normalizados.
- `services` orquesta casos de uso (actualizar datos, planificar).
- `api` expone REST; `web` consume la API.
- `main.py` es el *composition root*: ensambla todo y arranca la app.

## Flujo de datos

```
fuentes (API / Wikipedia)
        │  services/ingestion.py  (normaliza + alias de nombres)
        ▼
infrastructure/database.py  (SQLite: teams, matches, meta)
        │  analytics/ratings.py  (recalcula Elo y ataque/defensa)
        ▼
analytics/{poisson,elo,ml,montecarlo}  ──►  api/routes.py  ──►  web/
analytics/evaluation.py  (backtest walk-forward + métricas)
```

## Decisiones de diseño

- **SQLite + `sqlite3`**: persistencia simple, sin servidor, con volumen Docker.
- **Fuente híbrida con degradación elegante**: API → scraping → semilla. La app
  nunca se queda sin datos para mostrar.
- **Recálculo de Elo idempotente**: se reconstruye desde los valores base
  reproduciendo los resultados en orden; el mismo histórico da el mismo Elo.
- **Validación walk-forward**: cada predicción se evalúa con el estado anterior
  al partido, evitando fuga de información (data leakage).
- **Planificador en proceso (APScheduler)**: actualización diaria sin cron
  externo, válida dentro del contenedor.
