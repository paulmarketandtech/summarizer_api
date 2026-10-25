import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.storage.models import Base
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session_fixture():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(db_session):
    # 2. Override your app's database connection
    # Note: If you are using FastAPI's 'Depends(get_session)', use this syntax:
    #   from dependencies import get_session
    #   app.dependency_overrides[get_session] = lambda: db_session

    # If your get_session() is a custom regular function/context manager used inside the endpoint,
    # we can monkeypatch it or adjust it. Assuming standard FastAPI dependency injection:

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides after test finishes
    app.dependency_overrides.clear()
