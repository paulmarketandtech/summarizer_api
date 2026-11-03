import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
    MODE = os.getenv("APP_MODE", "sandbox")

    SANDBOX_DATA_DIR = Path(os.getenv("SANDBOX_DATA_DIR", "./scratchpad"))
    TRANSCRIPTS_DIR = SANDBOX_DATA_DIR / "transcripts"

    @classmethod
    def is_sandbox(cls) -> bool:
        return cls.MODE == "sandbox"

    @classmethod
    def is_production(cls) -> bool:
        return cls.MODE == "production"


config = Config()
