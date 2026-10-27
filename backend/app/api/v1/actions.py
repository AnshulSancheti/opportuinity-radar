from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from app.auth import current_account
from app.database import get_db
from app.models import Account, Article, Hackathon, UserAction
from app.schemas import UserActionResponse

router = APIRouter()


class ActionInput(BaseModel):
    item_type: Literal["article", "hackathon"]
    item_id: int = Field(gt=0, le=9223372036854775807)
    action: Literal["saved", "applied"]


def validate_item(body: ActionInput, db: Session):
    if body.action == "applied" and body.item_type != "hackathon":
        raise HTTPException(422, "Only hackathons can be marked applied")
    model = Article if body.item_type == "article" else Hackathon
    if db.get(model, body.item_id) is None:
        raise HTTPException(404, "Item not found")


@router.get("", response_model=list[UserActionResponse])
def list_actions(db: Session = Depends(get_db), account: Account = Depends(current_account)):
    return db.scalars(select(UserAction).where(UserAction.user_id == account.id, UserAction.item_type.in_(["article", "hackathon"]), UserAction.action.in_(["saved", "applied"])).order_by(UserAction.created_at.desc())).all()


@router.post("", response_model=UserActionResponse)
def create_action(body: ActionInput, db: Session = Depends(get_db), account: Account = Depends(current_account)):
    validate_item(body, db)
    db.execute(insert(UserAction).values(user_id=account.id, **body.model_dump()).on_conflict_do_nothing(index_elements=["user_id", "item_type", "item_id", "action"]))
    db.commit()
    return db.scalar(select(UserAction).where(UserAction.user_id == account.id, UserAction.item_type == body.item_type, UserAction.item_id == body.item_id, UserAction.action == body.action))


@router.delete("")
def delete_action(item_type: Literal["article", "hackathon"], action: Literal["saved", "applied"], item_id: int = Query(ge=1, le=9223372036854775807), db: Session = Depends(get_db), account: Account = Depends(current_account)):
    row = db.scalar(select(UserAction).where(UserAction.user_id == account.id, UserAction.item_type == item_type, UserAction.item_id == item_id, UserAction.action == action))
    if row:
        db.delete(row)
        db.commit()
    return {"status": "removed"}


@router.get("/saved")
def saved_items(action: Literal["saved", "applied"] = "saved", db: Session = Depends(get_db), account: Account = Depends(current_account)):
    result = []
    for model, kind, title_field, detail_field in ((Article, "article", "title", "source_name"), (Hackathon, "hackathon", "name", "organizer")):
        rows = db.execute(select(UserAction, model).join(model, UserAction.item_id == model.id).where(UserAction.user_id == account.id, UserAction.item_type == kind, UserAction.action == action)).all()
        for record, item in rows:
            result.append({"id": record.id, "item_type": kind, "item_id": item.id, "action": action, "created_at": record.created_at, "title": getattr(item, title_field), "subtitle": getattr(item, detail_field), "url": item.url, "deadline": getattr(item, "registration_deadline", None), "status": getattr(item, "status", None), "source_name": item.source_name, "end_date": getattr(item, "end_date", None)})
    return sorted(result, key=lambda row: row["created_at"], reverse=True)
