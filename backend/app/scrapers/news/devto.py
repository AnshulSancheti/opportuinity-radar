from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.article_service import upsert_article
from app.services.cleaner import clean_text


class DevToScraper(BaseScraper):
    source_name = "devto"
    module = "news"
    request_delay_ms = 500

    TAGS = ["python", "javascript", "devops", "ai", "webdev", "startup"]

    def fetch(self) -> list[dict]:
        items = []
        seen_urls: set[str] = set()
        for tag in self.TAGS:
            url = f"https://dev.to/api/articles?tag={tag}&per_page=15"
            response = self.fetch_url(url)
            for article in response.json():
                link = article.get("url")
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)
                published = None
                if article.get("published_at"):
                    published = datetime.fromisoformat(
                        article["published_at"].replace("Z", "+00:00")
                    )
                items.append({
                    "title": article.get("title", ""),
                    "url": link,
                    "source_name": "Dev.to",
                    "author": article.get("user", {}).get("username"),
                    "published_at": published,
                    "summary": clean_text(article.get("description")),
                    "tags": article.get("tag_list") or [tag],
                    "image_url": article.get("cover_image") or article.get("social_image"),
                })
        return items

    def save_item(self, item: dict) -> str:
        return upsert_article(self.db, item)
