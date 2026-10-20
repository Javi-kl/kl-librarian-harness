from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    KB_VAULT_PATH: Path

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("KB_VAULT_PATH")
    @classmethod
    def _validate_kb_path(cls, value: Path) -> Path:
        if not value.is_dir():
            raise ValueError(f"El vault no existe o no es un directorio: {value}")
        return value


class DeepSeekSettings(BaseSettings):
    DEEPSEEK_API_KEY: SecretStr
    DEEPSEEK_MODEL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings.model_validate({})
