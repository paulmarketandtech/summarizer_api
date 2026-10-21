from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

engine_readonly = create_engine(
    settings.DATABASE_URL_READONLY,
    pool_size=10,  # public gets more connections (more traffic)
    pool_pre_ping=True,  # detect stale connections
)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionReadOnly = sessionmaker(bind=engine_readonly, autoflush=False, autocommit=False)
SessionApp = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session_read_only() -> Session:
    session = SessionReadOnly()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_session() -> Session:
    session = SessionApp()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    from .models import Base

    Base.metadata.create_all(bind=engine)
