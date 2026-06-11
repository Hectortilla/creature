from functools import lru_cache
from urllib.parse import urlparse

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/creature"
    redis_url: str | None = None

    # Game engine RNG seed (env GAME_SEED). None = system entropy (prod default);
    # a fixed value reproduces deal/turn-order/dice for the e2e gameplay harness.
    game_seed: int | None = None

    # Auth settings
    # Generate secret_key with: openssl rand -hex 32
    auth_secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    auth_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 30

    # Observability (logs / metrics / tracing). See app/settings/logging.py,
    # app/settings/observability.py, and docs/references/observability.md.
    log_level: str = "INFO"
    log_json: bool = False
    service_name: str = "creature-api"
    metrics_enabled: bool = True
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str | None = None

    @property
    def broadcast_url(self) -> str:
        return self.redis_url or "memory://"

    @property
    def channel_namespace(self) -> str:
        """Pub/sub namespace (the DB name) — isolates channels across stacks sharing one Redis."""
        return urlparse(self.database_url).path.lstrip("/")

    model_config = {
        "env_file": ".env",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
