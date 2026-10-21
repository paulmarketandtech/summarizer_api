"""
import os

from src.infrastructure.production.yt_transcript import YouTubeFetcher
from src.infrastructure.sandbox.local_file_manager import LocalFileManager
from src.interfaces import TranscriptFetcher

MODE = os.getenv("APP_MODE", "sandbox")


# TODO: file to be deleted?
def get_transcript() -> TranscriptFetcher:
    print("how often do i get here?")
    if MODE == "sandbox":
        local_file_manager = LocalFileManager()
        return local_file_manager.get_transcript_content()
    youtube_fetcher = YouTubeFetcher()
    return youtube_fetcher.download_yt_transcript()
"""

from typing import Generator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.storage.config import settings
from app.storage.database import SessionApp, SessionReadOnly

# ── DB Sessions ─────────────────────────────────────────


def get_db_read() -> Generator[Session, None, None]:
    """Read-only session for public endpoints.
    Even if there's a bug in your code, this user CANNOT write."""
    db = SessionReadOnly()
    try:
        yield db  # FastAPI injects this into the route
    finally:
        db.close()  # Always close, even if the route crashes


def get_db_write() -> Generator[Session, None, None]:
    """Read-write session for admin/internal endpoints."""
    db = SessionApp()
    try:
        yield db
    finally:
        db.close()


# ── Auth ────────────────────────────────────────────────


def require_api_key(request: Request) -> None:
    """Check X-API-Key header. Used on /admin/* routes."""
    key = request.headers.get("X-API-Key")
    if key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


def require_localhost(request: Request) -> None:
    """Only allow requests from localhost. Used on /internal/* routes."""
    if request.client.host not in ("127.0.0.1", "::1"):
        raise HTTPException(status_code=403, detail="Localhost only")
