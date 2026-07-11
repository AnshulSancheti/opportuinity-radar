from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AlertRule
from app.schemas import AlertRuleCreate, AlertRuleResponse

router = APIRouter()


@router.get("/rules", response_model=list[AlertRuleResponse])
def list_rules(db: Session = Depends(get_db)) -> list[AlertRuleResponse]:
    rules = db.scalars(select(AlertRule).order_by(AlertRule.created_at.desc())).all()
    return [AlertRuleResponse.model_validate(r) for r in rules]


@router.post("/rules", response_model=AlertRuleResponse)
def create_rule(body: AlertRuleCreate, db: Session = Depends(get_db)) -> AlertRuleResponse:
    rule = AlertRule(**body.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return AlertRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"status": "deleted"}
