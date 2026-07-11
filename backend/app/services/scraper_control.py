"""Background scraper execution for admin API."""

from __future__ import annotations

import logging
import threading

from app.database import SessionLocal
from app.scrapers.runner import run_module

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_running: set[str] = set()


def is_module_running(module: str) -> bool:
    with _lock:
        return module in _running


def running_modules() -> list[str]:
    with _lock:
        return sorted(_running)


def start_module_scrape(module: str) -> bool:
    """Start a module scrape in a background thread. Returns False if already running."""
    with _lock:
        if module in _running:
            return False
        _running.add(module)

    thread = threading.Thread(target=_run_module, args=(module,), daemon=True, name=f"scrape-{module}")
    thread.start()
    return True


def _run_module(module: str) -> None:
    db = SessionLocal()
    try:
        run_module(db, module)
    except Exception:
        logger.exception("Scraper module %s failed", module)
    finally:
        db.close()
        with _lock:
            _running.discard(module)
