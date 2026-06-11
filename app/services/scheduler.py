# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Planificador de la actualizacion diaria automatica."""
from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from ..core.config import DAILY_UPDATE_HOUR, DAILY_UPDATE_MINUTE
from . import ingestion

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler:
        return _scheduler
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(ingestion.run_update, "cron", hour=DAILY_UPDATE_HOUR,
                  minute=DAILY_UPDATE_MINUTE, id="daily_update", replace_existing=True)
    sched.start()
    _scheduler = sched
    print(f"[scheduler] actualizacion diaria a las "
          f"{DAILY_UPDATE_HOUR:02d}:{DAILY_UPDATE_MINUTE:02d}")
    return sched
