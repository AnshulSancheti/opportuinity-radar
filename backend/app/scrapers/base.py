import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ScrapeError, ScrapeRun


class BaseScraper(ABC):
    source_name: str
    module: str
    request_delay_ms: int | None = None
    timeout_seconds: int | None = None
    max_retries: int | None = None
    max_pages: int = 1
    user_agent: str | None = None

    def __init__(self, db: Session):
        self.db = db
        settings = get_settings()
        self.request_delay_ms = self.request_delay_ms or settings.scraper_default_delay_ms
        self.timeout_seconds = self.timeout_seconds or settings.scraper_default_timeout_seconds
        self.max_retries = self.max_retries or settings.scraper_default_max_retries
        self.user_agent = self.user_agent or settings.scraper_user_agent
        self._last_request_at: float | None = None

    def _rate_limit(self) -> None:
        if self._last_request_at is not None:
            elapsed_ms = (time.monotonic() - self._last_request_at) * 1000
            wait_ms = self.request_delay_ms - elapsed_ms
            if wait_ms > 0:
                time.sleep(wait_ms / 1000)
        self._last_request_at = time.monotonic()

    def fetch_url(self, url: str) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            self._rate_limit()
            try:
                with httpx.Client(follow_redirects=True, timeout=self.timeout_seconds, headers={"User-Agent": self.user_agent}) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return response
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))
        raise last_error  # type: ignore[misc]

    @abstractmethod
    def fetch(self) -> list[dict]:
        pass

    def parse(self, raw: dict) -> dict:
        return raw

    def normalize(self, item: dict) -> dict:
        return item

    def run(self) -> ScrapeRun:
        run = ScrapeRun(source_name=self.source_name, module=self.module, status="running")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        inserted = updated = skipped = 0
        try:
            raw_items = self.fetch()
            run.items_found = len(raw_items)
            for raw in raw_items:
                try:
                    parsed = self.parse(raw)
                    normalized = self.normalize(parsed)
                    result = self.save_item(normalized)
                    if result == "inserted":
                        inserted += 1
                    elif result == "updated":
                        updated += 1
                    else:
                        skipped += 1
                except Exception as exc:
                    skipped += 1
                    self._log_error(run, url=raw.get("url"), exc=exc)
            run.items_inserted = inserted
            run.items_updated = updated
            run.items_skipped = skipped
            run.status = "partial_failure" if skipped and (inserted or updated) else "success"
            if skipped and not inserted and not updated and run.items_found:
                run.status = "failed"
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            self._log_error(run, exc=exc)
        finally:
            run.finished_at = datetime.now(timezone.utc)
            self.db.commit()
        return run

    @abstractmethod
    def save_item(self, item: dict) -> str:
        pass

    def _log_error(self, run: ScrapeRun, url: str | None = None, exc: Exception | None = None) -> None:
        error = ScrapeError(
            scrape_run_id=run.id,
            source_name=self.source_name,
            module=self.module,
            url=url,
            error_type=type(exc).__name__ if exc else None,
            error_message=str(exc) if exc else None,
            traceback=traceback.format_exc() if exc else None,
        )
        self.db.add(error)
        self.db.commit()
