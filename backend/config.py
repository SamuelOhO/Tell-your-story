import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _parse_origins(value: str | None) -> list[str]:
    if not value:
        return ["http://localhost:5173"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def _parse_positive_int(value: str | None, default: int) -> int:
    if not value:
        return default
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    upstage_api_key: str | None
    openai_api_key: str | None
    openai_base_url: str | None
    llm_model: str
    allowed_origins: list[str]
    max_history_turns: int
    db_path: str
    summary_update_every: int

    @property
    def provider_api_key(self) -> str | None:
        return self.upstage_api_key or self.openai_api_key

    @property
    def max_history_messages(self) -> int:
        return self.max_history_turns * 2


@lru_cache
def get_settings() -> Settings:
    default_db_path = Path(__file__).resolve().parent / "data" / "tell_your_story.db"
    return Settings(
        upstage_api_key=os.getenv("UPSTAGE_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL", "solar-pro2"),
        allowed_origins=_parse_origins(os.getenv("ALLOWED_ORIGINS")),
        max_history_turns=_parse_positive_int(os.getenv("MAX_HISTORY_TURNS"), default=12),
        db_path=os.getenv("DB_PATH", str(default_db_path)),
        summary_update_every=_parse_positive_int(os.getenv("SUMMARY_UPDATE_EVERY"), default=6),
    )
