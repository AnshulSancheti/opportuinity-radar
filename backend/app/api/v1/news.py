from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Article, UserAction
from app.schemas import ArticleResponse, PaginatedResponse

router = APIRouter()


def hidden_article_ids(db: Session) -> set[int]:
    rows = db.scalars(
        select(UserAction.item_id).where(
            UserAction.item_type == "article", UserAction.action == "hidden"
        )
    ).all()
    return set(rows)


@router.get("", response_model=PaginatedResponse[ArticleResponse])
def list_news(
    db: Session = Depends(get_db),
    q: str | None = None,
    category: str | None = None,
    source: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_hidden: bool = False,
) -> PaginatedResponse[ArticleResponse]:
    query = select(Article)
    if q:
        query = query.where(
            or_(Article.title.ilike(f"%{q}%"), Article.summary.ilike(f"%{q}%"))
        )
    if category:
        query = query.where(Article.category == category)
    if source:
        query = query.where(Article.source_name.ilike(f"%{source}%"))
    if not include_hidden:
        hidden = hidden_article_ids(db)
        if hidden:
            query = query.where(Article.id.not_in(hidden))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    articles = db.scalars(
        query.order_by(Article.published_at.desc().nullslast(), Article.first_seen_at.desc())
        .offset(offset).limit(limit)
    ).all()
    return PaginatedResponse(
        items=[ArticleResponse.model_validate(a) for a in articles],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
def get_news(article_id: int, db: Session = Depends(get_db)) -> ArticleResponse:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleResponse.model_validate(article)
