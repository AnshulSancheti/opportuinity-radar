from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Article
from app.services.categorizer import categorize
from app.services.cleaner import canonicalize_url, clean_text, make_content_hash


def upsert_article(db: Session, data: dict) -> str:
    title = clean_text(data.get("title"))
    if not title:
        return "skipped"

    url = data.get("url")
    canonical = canonicalize_url(url) if url else None
    content_hash = make_content_hash(canonical or title, data.get("source_name"))

    existing = None
    if canonical:
        existing = db.scalar(select(Article).where(Article.url == canonical))
    if not existing:
        existing = db.scalar(select(Article).where(Article.content_hash == content_hash))

    now = datetime.now(timezone.utc)
    summary = clean_text(data.get("summary"))
    category = data.get("category") or categorize(title, summary)

    if existing:
        existing.last_seen_at = now
        existing.title = title
        if summary:
            existing.summary = summary
        if data.get("score") is not None:
            existing.score = data.get("score")
        if data.get("image_url"):
            existing.image_url = data.get("image_url")
        existing.category = category
        db.commit()
        return "updated"

    article = Article(
        title=title,
        url=canonical,
        canonical_url=canonical,
        source_name=data["source_name"],
        author=data.get("author"),
        published_at=data.get("published_at"),
        summary=summary,
        raw_excerpt=summary,
        category=category,
        tags=data.get("tags") or [],
        score=data.get("score"),
        image_url=data.get("image_url"),
        content_hash=content_hash,
        first_seen_at=now,
        last_seen_at=now,
    )
    db.add(article)
    db.commit()
    return "inserted"
