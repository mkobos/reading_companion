import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_upload_size_bytes: int
    rate_limit_max_requests: int
    rate_limit_window_seconds: float
    gcs_bucket_name: str | None
    allow_origins: list[str]
    discussion_agent_url: str
    discussion_agent_timeout_seconds: float
    suggestions_model: str
    journal_model: str
    llm_timeout_seconds: float


def load_settings() -> Settings:
    allow_origins_raw = os.environ.get("ALLOW_ORIGINS", "")
    return Settings(
        max_upload_size_bytes=int(os.environ.get("MAX_UPLOAD_SIZE_BYTES", "2000000")),
        rate_limit_max_requests=int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "10")),
        rate_limit_window_seconds=float(
            os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60")
        ),
        gcs_bucket_name=os.environ.get("GCS_BUCKET_NAME") or None,
        allow_origins=[o.strip() for o in allow_origins_raw.split(",") if o.strip()],
        discussion_agent_url=os.environ.get("DISCUSSION_AGENT_URL", "http://localhost:8080"),
        discussion_agent_timeout_seconds=float(
            os.environ.get("DISCUSSION_AGENT_TIMEOUT_SECONDS", "30")
        ),
        suggestions_model=os.environ.get("SUGGESTIONS_MODEL", "gemini-flash-latest"),
        journal_model=os.environ.get("JOURNAL_MODEL", "gemini-flash-latest"),
        llm_timeout_seconds=float(os.environ.get("LLM_TIMEOUT_SECONDS", "15")),
    )
