from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserAction
from app.schemas import UserActionCreate, UserActionResponse

router = APIRouter()


@router.post("", response_model=UserActionResponse)
def create_action(body: UserActionCreate, db: Session = Depends(get_db)) -> UserActionResponse:
    existing = db.scalar(
        select(UserAction).where(
            UserAction.item_type == body.item_type,
            UserAction.item_id == body.item_id,
            UserAction.action == body.action,
            UserAction.user_id.is_(None),
        )
    )
    if existing:
        return UserActionResponse.model_validate(existing)
    action = UserAction(item_type=body.item_type, item_id=body.item_id, action=body.action)
    db.add(action)
    db.commit()
    db.refresh(action)
    return UserActionResponse.model_validate(action)


@router.delete("")
def delete_action(
    item_type: str,
    item_id: int,
    action: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    row = db.scalar(
        select(UserAction).where(
            UserAction.item_type == item_type,
            UserAction.item_id == item_id,
            UserAction.action == action,
            UserAction.user_id.is_(None),
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Action not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


@router.get("/saved", response_model=list[UserActionResponse])
def list_saved(db: Session = Depends(get_db)) -> list[UserActionResponse]:
    rows = db.scalars(
        select(UserAction).where(UserAction.action == "saved").order_by(UserAction.created_at.desc())
    ).all()
    return [UserActionResponse.model_validate(r) for r in rows]
