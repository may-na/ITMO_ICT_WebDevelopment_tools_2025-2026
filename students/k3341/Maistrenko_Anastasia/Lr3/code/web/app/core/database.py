"""Подключение к базе данных и управление сессиями.

Здесь создаётся «движок» SQLAlchemy/SQLModel и определяется зависимость
get_session(), которую FastAPI внедряет в обработчики через Depends().
"""
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# echo=True выводит в консоль все SQL-запросы — удобно при отладке
engine = create_engine(settings.database_url, echo=settings.db_echo)


def get_session() -> Iterator[Session]:
    """Зависимость FastAPI: открывает сессию на время запроса и закрывает её."""
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """Создать все таблицы из метаданных SQLModel.

    В рабочем процессе схемой управляет Alembic (migrations/), эта функция —
    лишь удобство для быстрого локального старта без миграций.
    """
    SQLModel.metadata.create_all(engine)
