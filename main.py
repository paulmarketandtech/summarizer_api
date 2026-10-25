import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dependencies import get_db_read
from app.routers import admin, internal, pages, public

router = APIRouter()

IS_DEV = os.getenv("ENV", "prod").lower() in {"dev", "development", "local"}
if IS_DEV:
    import fastapi_swagger_dark as fsd

    fsd.install(router)

app = FastAPI(
    title="YT Summarizer API",
    docs_url=None,
    redoc_url="/redoc" if IS_DEV else None,
    openapi_url="/openapi.json" if IS_DEV else None,
)

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "app" / "static"),
    name="static",
)


app.include_router(router)
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(internal.router)
app.include_router(pages.router)


templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health_check(db: Annotated[Session, Depends(get_db_read)]):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except SQLAlchemyError as e:
        return {"status": "degraded", "db": str(e)}
