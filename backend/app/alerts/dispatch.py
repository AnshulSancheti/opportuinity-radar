from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import AlertDelivery, AlertRule, Article, Hackathon, Job
from app.services.telegram import send_telegram_message


def item_matches_rule(item: dict, rule: AlertRule) -> bool:
    if rule.module != "all" and rule.module != item["module"]:
        return False
    haystack = " ".join(str(v) for v in item.get("fields", {}).values()).lower()
    if rule.keyword and rule.keyword.lower() not in haystack:
        return False
    if rule.source_name and rule.source_name.lower() not in haystack:
        return False
    if rule.location and rule.location.lower() not in haystack:
        return False
    if rule.skill and rule.skill.lower() not in haystack:
        return False
    if rule.category and rule.category.lower() not in haystack:
        return False
    return True


def dispatch_alerts(db: Session) -> int:
    rules = db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True))).all()
    if not rules:
        return 0

    candidates: list[dict] = []
    for article in db.scalars(select(Article).order_by(Article.created_at.desc()).limit(50)).all():
        candidates.append({
            "module": "news",
            "item_type": "article",
            "item_id": article.id,
            "fields": {
                "title": article.title,
                "source": article.source_name,
                "category": article.category,
                "summary": article.summary,
            },
        })
    for hack in db.scalars(select(Hackathon).where(Hackathon.status == "active").order_by(Hackathon.created_at.desc()).limit(50)).all():
        candidates.append({
            "module": "hackathons",
            "item_type": "hackathon",
            "item_id": hack.id,
            "fields": {
                "name": hack.name,
                "organizer": hack.organizer,
                "location": hack.location,
                "url": hack.url,
            },
        })

    sent = 0
    for rule in rules:
        for item in candidates:
            if not item_matches_rule(item, rule):
                continue
            existing = db.scalar(
                select(AlertDelivery).where(
                    AlertDelivery.rule_id == rule.id,
                    AlertDelivery.item_type == item["item_type"],
                    AlertDelivery.item_id == item["item_id"],
                )
            )
            if existing:
                continue
            title = item["fields"].get("title") or item["fields"].get("name", "New item")
            message = f"*{rule.name}*\n\n{title}\n\n" + "\n".join(
                f"{k}: {v}" for k, v in item["fields"].items() if v
            )
            status = send_telegram_message(message)
            delivery = AlertDelivery(
                rule_id=rule.id,
                item_type=item["item_type"],
                item_id=item["item_id"],
                delivery_status="sent" if status else "failed",
            )
            db.add(delivery)
            if status:
                sent += 1
    db.commit()
    return sent


def main() -> None:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        count = dispatch_alerts(db)
        print(f"Alerts dispatched: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
