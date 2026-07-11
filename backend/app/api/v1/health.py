from fastapi import APIRouter

from app.database import check_database_connection

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    db_ok = check_database_connection()
    return {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "unavailable"}
