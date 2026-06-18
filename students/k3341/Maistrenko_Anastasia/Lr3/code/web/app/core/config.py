"""Конфигурация приложения.

Значения читаются из переменных окружения (файл .env) с помощью
pydantic-settings. Так секреты (строка подключения к БД, ключ подписи JWT)
не хранятся в коде и не попадают в систему контроля версий.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Подключение к PostgreSQL
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finance_db"

    # Параметры аутентификации (JWT)
    secret_key: str = "super-secret-change-me-please"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Логирование SQL
    db_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Единый экземпляр настроек, импортируемый по всему приложению
settings = Settings()
