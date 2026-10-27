import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import COOKIE_NAME, current_account, hash_password, token_hash, verify_password
from app.config import get_settings
from app.database import get_db
from app.models import Account, AccountSession, AuthAttempt
import secrets

router = APIRouter()


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class Registration(Credentials):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        if not value.strip():
            raise ValueError("Enter your name")
        return value.strip()


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    name: str


def throttle(request: Request, email: str, db: Session):
    now = datetime.now(timezone.utc)
    db.execute(delete(AuthAttempt).where(AuthAttempt.created_at < now - timedelta(hours=1)))
    # Hash identifiers so the throttle table contains neither emails nor IPs.
    keys = [token_hash("email:" + email), token_hash("ip:" + (request.client.host if request.client else "unknown"))]
    for key, limit in zip(keys, (10, 40)):
        count = db.scalar(select(func.count()).select_from(AuthAttempt).where(AuthAttempt.key == key, AuthAttempt.created_at > now - timedelta(minutes=15)))
        if count >= limit:
            raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
    db.add_all([AuthAttempt(key=key) for key in keys])
    db.commit()


def start_session(account: Account, request: Request, response: Response, db: Session):
    now = datetime.now(timezone.utc)
    old = request.cookies.get(COOKIE_NAME)
    if old:
        db.execute(delete(AccountSession).where(AccountSession.token_hash == token_hash(old)))
    db.execute(delete(AccountSession).where(AccountSession.expires_at <= now))
    token = secrets.token_urlsafe(32)
    db.add(AccountSession(token_hash=token_hash(token), user_id=account.id, expires_at=now + timedelta(days=7)))
    db.commit()
    response.set_cookie(COOKIE_NAME, token, max_age=604800, httponly=True, secure=get_settings().api_env == "production", samesite="lax", path="/")
    response.headers["Cache-Control"] = "no-store"
    return account


@router.post("/register", response_model=AccountResponse, status_code=201)
def register(body: Registration, request: Request, response: Response, db: Session = Depends(get_db)):
    throttle(request, body.email, db)
    account = Account(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add(account)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with that email already exists")
    return start_session(account, request, response, db)


@router.post("/login", response_model=AccountResponse)
def login(body: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    throttle(request, body.email, db)
    account = db.scalar(select(Account).where(Account.email == body.email))
    # Do the same expensive hash for unknown emails to reduce timing leakage.
    encoded = account.password_hash if account else DUMMY_HASH
    valid = verify_password(body.password, encoded)
    if not account or not valid:
        raise HTTPException(401, "Email or password is incorrect")
    return start_session(account, request, response, db)


@router.get("/me", response_model=AccountResponse)
def me(account: Account = Depends(current_account)):
    return account


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.execute(delete(AccountSession).where(AccountSession.token_hash == token_hash(token)))
        db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "signed out"}


DUMMY_HASH = hash_password(secrets.token_urlsafe(32))
