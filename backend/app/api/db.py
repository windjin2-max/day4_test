from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()


@router.get("/db/health")
def db_health_check() -> dict[str, str]:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
