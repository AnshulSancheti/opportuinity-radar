import argparse
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.scrapers.hackathons.mlh import MLHScraper
from app.scrapers.hackathons.static_list import StaticListScraper
from app.scrapers.jobs.ashby import AshbyScraper
from app.scrapers.jobs.greenhouse import GreenhouseScraper
from app.scrapers.jobs.lever import LeverScraper
from app.scrapers.jobs.recruitee import RecruiteeScraper
from app.scrapers.jobs.workable import WorkableScraper
from app.scrapers.news.devto import DevToScraper
from app.scrapers.news.hacker_news import HackerNewsScraper
from app.scrapers.news.rss import RSSScraper


def load_sources() -> dict:
    path = Path(__file__).resolve().parents[2] / "sources.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_module(db: Session, module: str, source: str | None = None) -> None:
    config = load_sources()
    scrapers = []

    if module == "news":
        news_cfg = config.get("news", {})
        if news_cfg.get("hacker_news", {}).get("enabled", True):
            if source in (None, "hacker_news"):
                scrapers.append(HackerNewsScraper(db))
        if news_cfg.get("devto", {}).get("enabled", True):
            if source in (None, "devto"):
                scrapers.append(DevToScraper(db))
        if source is None or source == "rss":
            for feed in news_cfg.get("rss", []):
                scrapers.append(RSSScraper(db, feed["url"], feed["source_name"]))
    elif module == "jobs":
        jobs_cfg = config.get("jobs", {})
        if source is None or source == "greenhouse":
            for entry in jobs_cfg.get("greenhouse", []):
                scrapers.append(GreenhouseScraper(db, entry["company"], entry["board_token"]))
        if source is None or source == "lever":
            for entry in jobs_cfg.get("lever", []):
                scrapers.append(LeverScraper(db, entry["company"], entry["company_slug"]))
        if source is None or source == "ashby":
            for entry in jobs_cfg.get("ashby", []):
                scrapers.append(AshbyScraper(db, entry["company"], entry["board_name"]))
        if source is None or source == "workable":
            for entry in jobs_cfg.get("workable", []):
                scrapers.append(WorkableScraper(db, entry["company"], entry["account_slug"]))
        if source is None or source == "recruitee":
            for entry in jobs_cfg.get("recruitee", []):
                scrapers.append(RecruiteeScraper(db, entry["company"], entry["subdomain"]))
    elif module == "hackathons":
        hacks_cfg = config.get("hackathons", {})
        if hacks_cfg.get("mlh", {}).get("enabled", True):
            if source in (None, "mlh"):
                scrapers.append(MLHScraper(db))
        if hacks_cfg.get("static_list", {}).get("enabled", True):
            if source in (None, "static_list"):
                scrapers.append(StaticListScraper(db))

    for scraper in scrapers:
        print(f"Running {scraper.source_name}...")
        run = scraper.run()
        print(f"  {run.status}: found={run.items_found} inserted={run.items_inserted} updated={run.items_updated}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Opportunity Radar scrapers")
    parser.add_argument("--module", choices=["news", "jobs", "hackathons"], required=True)
    parser.add_argument("--source", default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        run_module(db, args.module, args.source)
    finally:
        db.close()


if __name__ == "__main__":
    main()
