from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/creature"
    redis_url: str | None = None
    
    @property
    def broadcast_url(self) -> str:
        return self.redis_url or "memory://"
    
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()

