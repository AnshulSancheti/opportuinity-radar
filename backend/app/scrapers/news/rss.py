import feedparser
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.article_service import upsert_article
from app.services.cleaner import clean_text
from app.services.date_parser import parse_date
from app.services.image_extractor import extract_rss_image


class RSSScraper(BaseScraper):
    source_name = "rss"
    module = "news"

    def __init__(self, db: Session, feed_url: str, feed_name: str):
        super().__init__(db)
        self.feed_url = feed_url
        self.feed_name = feed_name
        self.source_name = feed_name

    def fetch(self) -> list[dict]:
        response = self.fetch_url(self.feed_url)
        parsed = feedparser.parse(response.text)
        items = []
        for entry in parsed.entries:
            published = None
            if hasattr(entry, "published"):
                published = parse_date(entry.published)
            elif hasattr(entry, "updated"):
                published = parse_date(entry.updated)
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link"),
                "source_name": self.feed_name,
                "author": entry.get("author"),
                "published_at": published,
                "summary": clean_text(entry.get("summary") or entry.get("description")),
                "image_url": extract_rss_image(entry),
            })
        return items

    def save_item(self, item: dict) -> str:
        return upsert_article(self.db, item)
