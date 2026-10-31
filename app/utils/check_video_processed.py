from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()
from src.extraction.youtube_transcript import extract_youtube_id
from src.storage.database import get_session
from src.storage.models import Video
from src.storage.query_service import VideoQueryService


def get_all_yt_ids():

    with get_session() as session:
        service = VideoQueryService(session)

    records, _ = service.get_videos_basic()
    return [record.yt_id for record in records]


def check_id_in_db(url: str) -> tuple[bool, str | None]:
    new_id = extract_youtube_id(url)
    processed_ids = get_all_yt_ids()
    return new_id in processed_ids, new_id


def get_processed_summary(yt_id: str) -> tuple[str | None, str]:
    with get_session() as session:
        # video = session.query(Video).filter(Video.yt_id == yt_id).first()
        stmt = select(Video).where(Video.yt_id == yt_id)
        searched_video = session.execute(stmt).scalar()

        return searched_video.title, searched_video.summary.final_report


# print(get_processed_summary("QzTrr-pFSJM"))
# print(check_id_in_db("https://youtu.be/QzTrr-pFSJM?si=aVrJ2wa-0OG_Z76P"))
