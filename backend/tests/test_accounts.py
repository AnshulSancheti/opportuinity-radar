"""Account workflows use an outer rollback: no test accounts or actions persist."""
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth import COOKIE_NAME, token_hash, verify_password
from app.database import engine, get_db
from app.main import app
from app.models import Account, AccountSession, Article, AuthAttempt, Hackathon, UserAction


@pytest.fixture
def clients():
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint")
    app.dependency_overrides[get_db] = lambda: db
    a, b = TestClient(app), TestClient(app)
    article = Article(title="Account test article", source_name="test", url=f"https://example.com/{uuid.uuid4()}")
    hack = Hackathon(name="Account test hackathon", source_name="test", url=f"https://example.com/{uuid.uuid4()}", status="active")
    db.add_all([article, hack]); db.commit()
    yield a, b, db, article.id, hack.id
    a.close(); b.close()
    app.dependency_overrides.clear()
    db.close(); transaction.rollback(); connection.close()


def register(client, name="Alice"):
    email = f"{name.lower()}-{uuid.uuid4().hex}@example.com"
    r = client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "Testing-password-123"})
    assert r.status_code == 201, r.text
    return email, r


def action(client, kind, item_id, value="saved"):
    return client.post("/api/v1/actions", json={"item_type": kind, "item_id": item_id, "action": value})


def test_registration_password_hash_and_session(clients):
    a, _, db, _, _ = clients
    email, response = register(a)
    assert "password" not in response.text
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie
    account = db.scalar(select(Account).where(Account.email == email))
    assert account.password_hash != "Testing-password-123"
    assert verify_password("Testing-password-123", account.password_hash)
    session = db.get(AccountSession, token_hash(a.cookies.get(COOKIE_NAME)))
    assert session and session.user_id == account.id
    assert a.get("/api/v1/auth/me").json()["email"] == email


def test_login_logout_revokes_session_and_normalizes_email(clients):
    a, b, _, _, _ = clients
    email, _ = register(a)
    old_token = a.cookies.get(COOKIE_NAME)
    assert a.post("/api/v1/auth/logout", json={}).status_code == 200
    b.cookies.set(COOKIE_NAME, old_token)
    assert b.get("/api/v1/auth/me").status_code == 401
    assert a.post("/api/v1/auth/login", json={"email": email.upper(), "password": "Testing-password-123"}).status_code == 200
    assert a.post("/api/v1/auth/login", json={"email": email, "password": "Wrong-password-123"}).status_code == 401


def test_duplicate_and_invalid_registration(clients):
    a, b, _, _, _ = clients
    email, _ = register(a)
    assert b.post("/api/v1/auth/register", json={"name": "Other", "email": email.upper(), "password": "Testing-password-123"}).status_code == 409
    for values in ({"email": "bad", "password": "Testing-password-123", "name": "Alice"}, {"email": "a@example.com", "password": "short", "name": "Alice"}, {"email": "a@example.com", "password": "Testing-password-123", "name": "  "}):
        assert b.post("/api/v1/auth/register", json=values).status_code == 422


def test_anonymous_requests_are_rejected(clients):
    a, _, _, article, hack = clients
    for path in ("/api/v1/auth/me", "/api/v1/actions", "/api/v1/actions/saved"):
        assert a.get(path).status_code == 401
    assert action(a, "article", article).status_code == 401
    assert a.delete(f"/api/v1/actions?item_type=hackathon&item_id={hack}&action=applied").status_code == 401


def test_owner_isolation_idempotence_and_enriched_collection(clients):
    a, b, _, article, hack = clients
    register(a); register(b, "Bob")
    assert action(a, "article", article).status_code == 200
    assert action(a, "hackathon", hack).status_code == 200
    assert action(a, "hackathon", hack, "applied").status_code == 200
    first = action(a, "article", article).json()["id"]
    assert action(a, "article", article).json()["id"] == first
    saved = a.get("/api/v1/actions/saved").json()
    assert len(saved) == 2 and all(i["title"] and i["url"] for i in saved)
    assert len(a.get("/api/v1/actions/saved?action=applied").json()) == 1
    assert b.get("/api/v1/actions").json() == []
    assert b.get("/api/v1/actions/saved").json() == []
    b.delete(f"/api/v1/actions?item_type=article&item_id={article}&action=saved")
    assert len(a.get("/api/v1/actions/saved").json()) == 2
    assert action(b, "article", article).status_code == 200
    a.delete(f"/api/v1/actions?item_type=article&item_id={article}&action=saved")
    assert len(b.get("/api/v1/actions/saved").json()) == 1
    a.delete(f"/api/v1/actions?item_type=hackathon&item_id={hack}&action=applied")
    assert a.get("/api/v1/actions/saved?action=applied").json() == []


def test_action_validation_and_missing_items(clients):
    a, _, _, article, _ = clients
    register(a)
    assert action(a, "article", article, "applied").status_code == 422
    assert action(a, "job", article).status_code == 422
    assert action(a, "article", article, "unknown").status_code == 422
    assert action(a, "article", 9223372036854775807).status_code == 404


def test_expired_sessions_and_legacy_actions_are_private(clients):
    a, _, db, article, _ = clients
    register(a)
    db.add(UserAction(user_id=None, item_type="article", item_id=article, action="saved")); db.commit()
    assert a.get("/api/v1/actions/saved").json() == []
    session = db.get(AccountSession, token_hash(a.cookies.get(COOKIE_NAME)))
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1); db.commit()
    assert a.get("/api/v1/actions").status_code == 401


def test_csrf_and_content_type_guard(clients):
    a, _, _, _, _ = clients
    assert a.post("/api/v1/auth/logout", json={}, headers={"Origin": "https://attacker.example"}).status_code == 403
    assert a.post("/api/v1/auth/logout", content="x=y").status_code == 415
    assert a.post("/api/v1/auth/logout", json={}, headers={"Origin": "http://localhost:3000"}).status_code == 200


def test_login_throttle(clients):
    a, _, db, _, _ = clients
    email = f"missing-{uuid.uuid4().hex}@example.com"
    db.add_all([AuthAttempt(key=token_hash("email:" + email)) for _ in range(10)]); db.commit()
    assert a.post("/api/v1/auth/login", json={"email": email, "password": "Testing-password-123"}).status_code == 429


def test_jobs_and_matching_removed(clients):
    a, _, _, _, _ = clients
    assert a.get("/api/v1/jobs").status_code == 404
    assert a.get("/api/v1/matches/status").status_code == 404
    assert "total_jobs" not in a.get("/api/v1/admin/stats").json()
    assert a.get("/api/v1/news").status_code == 200
    assert a.get("/api/v1/hackathons").status_code == 200
