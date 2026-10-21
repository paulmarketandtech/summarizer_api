import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_URL_READONLY: str = os.getenv("DATABASE_URL_READONLY")

    OLLAMA_URL: str = os.getenv("OLLAMA_HOST")
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # model_config = {"env_file": ".env"}


settings = Settings()
