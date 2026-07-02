from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.db import router as db_router
from app.api.exploration import router as exploration_router
from app.api.health import router as health_router
from app.core.config import settings
from app.db.init_db import init_db


app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(db_router, prefix="/api", tags=["db"])
app.include_router(exploration_router, prefix="/api", tags=["exploration"])


@app.on_event("startup")
def startup_event() -> None:
    init_db()
