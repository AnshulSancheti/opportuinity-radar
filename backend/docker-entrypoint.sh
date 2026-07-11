#!/bin/sh
# Wait for Postgres DNS + connection, run migrations, start API.
set -e

wait_for_db() {
  echo ">> Waiting for database..."
  attempt=1
  while [ "$attempt" -le 30 ]; do
    if python - <<'PY'
from sqlalchemy import create_engine, text
from app.config import get_settings

engine = create_engine(get_settings().database_url)
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
PY
    then
      echo "   OK: database reachable"
      return 0
    fi
    echo "   attempt $attempt/30 — retrying in 2s..."
    attempt=$((attempt + 1))
    sleep 2
  done
  echo "   ERROR: database not reachable after 30 attempts" >&2
  return 1
}

wait_for_db
echo ">> Running migrations"
alembic upgrade head
echo ">> Starting API"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
