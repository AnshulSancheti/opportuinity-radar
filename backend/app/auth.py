"""Password hashing and revocable, database-backed browser sessions."""
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, AccountSession

COOKIE_NAME = "radar_session"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=131072, r=8, p=1, maxmem=268435456)
    return f"scrypt${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=131072, r=8, p=1, maxmem=268435456)
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_account(request: Request, db: Session = Depends(get_db)) -> Account:
    token = request.cookies.get(COOKIE_NAME)
    session = db.get(AccountSession, token_hash(token)) if token else None
    if session is None or session.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Sign in to continue")
    account = db.get(Account, session.user_id)
    if account is None:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    return account
