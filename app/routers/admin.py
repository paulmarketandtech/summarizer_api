from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db_write, require_api_key  # ← read-write + auth
from app.schemas.summary import TitlesOut
from app.storage.database import get_session
from app.storage.models import Video

router = APIRouter(prefix="/api/admin", tags=["admin"])

"""
example functions for reference
"""


@router.get("/titles", response_model=TitlesOut)
def get_titles():
    with get_session() as session:
        titles = session.scalars(select(Video.title)).all()  # list[str]
        return TitlesOut(titles=titles)


@router.post("/feed", dependencies=[Depends(require_api_key)])
def feed_video(url: str, db: Session = Depends(get_db_write)):
    # This session CAN write. Protected by API key.
    new_video = Video(url=url)
    db.add(new_video)
    db.commit()
    return {"status": "created"}
