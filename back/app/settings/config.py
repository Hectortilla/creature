from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/creature"
    redis_url: str | None = None
    
    # Auth settings
    # Generate secret_key with: openssl rand -hex 32
    auth_secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    auth_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 30
    
    @property
    def broadcast_url(self) -> str:
        return self.redis_url or "memory://"
    
    model_config = {
        "env_file": ".env",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()

