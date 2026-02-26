import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)


def _parse_origins(value: str | None) -> list[str]:
    raw = value if value is not None else "http://localhost:5173"
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if not origins:
        raise ValueError("ALLOWED_ORIGINS must include at least one origin.")
    for origin in origins:
        if not origin.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid ALLOWED_ORIGINS entry '{origin}'. Use http:// or https:// prefixed origins."
            )
    return origins


def _parse_int_in_range(
    env_name: str,
    value: str | None,
    default: int,
    *,
    min_value: int,
    max_value: int,
) -> int:
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError:
        raise ValueError(f"{env_name} must be an integer. Received: '{value}'.")
    if parsed < min_value or parsed > max_value:
        raise ValueError(
            f"{env_name} must be between {min_value} and {max_value}. Received: {parsed}."
        )
    return parsed


def _read_optional_api_key(*env_names: str) -> str | None:
    for env_name in env_names:
        value = os.getenv(env_name)
        if value is not None and value.strip():
            return value.strip()
    return None


def _read_required_text(env_name: str, *, default: str | None = None) -> str:
    value = os.getenv(env_name, default)
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{env_name} is required and cannot be blank.")
    return normalized


@dataclass(frozen=True)
class Settings:
    app_env: str
    upstage_api_key: str | None
    openai_api_key: str | None
    openai_base_url: str | None
    llm_model: str
    allowed_origins: list[str]
    max_history_turns: int
    db_path: str
    summary_update_every: int
    log_level: str

    @property
    def provider_api_key(self) -> str | None:
        return self.upstage_api_key or self.openai_api_key

    @property
    def max_history_messages(self) -> int:
        return self.max_history_turns * 2


@lru_cache
def get_settings() -> Settings:
    default_db_path = Path(__file__).resolve().parent / "data" / "tell_your_story.db"
    app_env = _read_required_text("APP_ENV", default="dev").lower()
    if app_env not in {"dev", "prod", "test"}:
        raise ValueError(f"APP_ENV must be one of dev/prod/test. Received: '{app_env}'.")

    openai_base_url = os.getenv("OPENAI_BASE_URL")
    if openai_base_url is not None and openai_base_url.strip():
        normalized_base_url = openai_base_url.strip()
        if not normalized_base_url.startswith(("http://", "https://")):
            raise ValueError("OPENAI_BASE_URL must start with http:// or https://.")
        openai_base_url = normalized_base_url
    else:
        openai_base_url = None

    log_level = _read_required_text("LOG_LEVEL", default="INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(
            f"LOG_LEVEL must be one of DEBUG/INFO/WARNING/ERROR/CRITICAL. Received: '{log_level}'."
        )

    return Settings(
        app_env=app_env,
        upstage_api_key=_read_optional_api_key("UPSTAGE_API_KEY"),
        openai_api_key=_read_optional_api_key("OPENAI_API_KEY"),
        openai_base_url=openai_base_url,
        llm_model=_read_required_text("LLM_MODEL", default="solar-pro2"),
        allowed_origins=_parse_origins(os.getenv("ALLOWED_ORIGINS")),
        max_history_turns=_parse_int_in_range(
            "MAX_HISTORY_TURNS",
            os.getenv("MAX_HISTORY_TURNS"),
            default=12,
            min_value=1,
            max_value=100,
        ),
        db_path=_read_required_text("DB_PATH", default=str(default_db_path)),
        summary_update_every=_parse_int_in_range(
            "SUMMARY_UPDATE_EVERY",
            os.getenv("SUMMARY_UPDATE_EVERY"),
            default=6,
            min_value=1,
            max_value=100,
        ),
        log_level=log_level,
    )
