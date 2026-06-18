"""Окружение Alembic.

Здесь:
  - подгружаем переменные окружения из .env (python-dotenv);
  - берём строку подключения из DATABASE_URL и кладём в конфиг Alembic;
  - в качестве target_metadata используем метаданные SQLModel, чтобы работал
    автогенератор миграций (`alembic revision --autogenerate`).
"""
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Импортируем все модели, чтобы они зарегистрировались в SQLModel.metadata
import app.models  # noqa: F401

# Загружаем .env и прокидываем DATABASE_URL в конфигурацию Alembic
load_dotenv()
config = context.config
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Настройка логирования из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные, по которым Alembic сравнивает модели и схему БД
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Миграции в offline-режиме (генерация SQL без подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Миграции в online-режиме (с подключением к БД)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
