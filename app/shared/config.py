from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    KB_VAULT_PATH: Path

    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    @field_validator("KB_VAULT_PATH")
    @classmethod
    def _validate_kb_path(cls, value: Path) -> Path:
        if not value.is_dir():
            raise ValueError(f"El vault no existe o no es un directorio: {value}")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
