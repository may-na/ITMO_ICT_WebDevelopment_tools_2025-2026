# Подключение к БД и миграции

## Конфигурация (`app/core/config.py`)

Параметры читаются из переменных окружения (файл `.env`) через
pydantic-settings, поэтому секреты не хранятся в коде:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/finance_db"
    secret_key: str = "super-secret-change-me-please"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    db_echo: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
```

## Подключение (`app/core/database.py`)

```python
from sqlmodel import Session, SQLModel, create_engine
from app.core.config import settings

engine = create_engine(settings.database_url, echo=settings.db_echo)


def get_session():
    """Зависимость FastAPI: открывает сессию на время запроса."""
    with Session(engine) as session:
        yield session
```

Каждый обработчик получает сессию через `session: Session = Depends(get_session)`.

## Миграции Alembic

`migrations/env.py` использует метаданные SQLModel и берёт строку подключения из
`DATABASE_URL`. Создание и применение миграции:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Реальный вывод автогенерации (фрагмент) — Alembic обнаружил все 8 таблиц:

```text
INFO  [alembic.autogenerate.compare] Detected added table 'user'
INFO  [alembic.autogenerate.compare] Detected added table 'account'
INFO  [alembic.autogenerate.compare] Detected added table 'budget'
INFO  [alembic.autogenerate.compare] Detected added table 'category'
INFO  [alembic.autogenerate.compare] Detected added table 'tag'
INFO  [alembic.autogenerate.compare] Detected added table 'budget_category_link'
INFO  [alembic.autogenerate.compare] Detected added table 'transaction'
INFO  [alembic.autogenerate.compare] Detected added table 'transaction_tag_link'
Generating .../migrations/versions/81aa61fb58d7_initial_schema.py ... done
```

После `alembic upgrade head` в БД создаются все таблицы:

```text
$ psql finance_db -c "\dt"
 account | alembic_version | budget | budget_category_link |
 category | tag | transaction | transaction_tag_link | user
```

## Создание БД

```bash
createdb finance_db
# либо: psql -c "CREATE DATABASE finance_db;"
```
