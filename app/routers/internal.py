from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_write, require_localhost

router = APIRouter(prefix="/api/internal", tags=["internal"])


@router.post("/process", dependencies=[Depends(require_localhost)])
def process_transcript(db: Session = Depends(get_db_write)):
    # Write access, but only from localhost
    # move to logic from app.py and src/app.py
    ...
