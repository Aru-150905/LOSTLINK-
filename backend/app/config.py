from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to backend/.env so it loads no matter what directory uvicorn
# is launched from (the README runs uvicorn from the project root).
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LostLink API"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    resend_api_key: str = ""
    email_from: str = "LostLink <noreply@lostlink.app>"

    storage_bucket: str = "item-images"
    match_top_k: int = 5
    match_candidate_limit: int = 50

    # Minimum confidence (0-1) for a candidate to count as a match. Raised from
    # the old hard-coded 0.05 which let near-random pairs through.
    match_threshold: float = 0.35

    # Preload CLIP + MiniLM at startup instead of on the first request.
    warmup_models: bool = False

    # Max accepted image upload size in bytes (5 MB, matches the storage bucket).
    max_image_bytes: int = 5 * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
