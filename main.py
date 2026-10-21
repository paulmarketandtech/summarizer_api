from pathlib import Path

import fastapi_swagger_dark as fsd
from fastapi import APIRouter, Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db_read
from app.routers import admin, internal, pages, public

app = FastAPI(title="YT Summarizer API", docs_url=None)
router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "app" / "static"),
    name="static",
)

fsd.install(router)
app.include_router(router)
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(internal.router)
app.include_router(pages.router)

templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health(db: Session = Depends(get_db_read)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "degraded", "db": str(e)}
