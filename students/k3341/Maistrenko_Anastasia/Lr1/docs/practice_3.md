# Практика 3. Миграции, переменные окружения и .gitignore

**Цель:** настроить миграции БД с помощью **Alembic**, вынести секреты в файл
`.env` и исключить лишние файлы из репозитория через `.gitignore`.

## Alembic

SQLModel сам не умеет версионировать схему, поэтому используется Alembic.
Инициализация выполнялась командой:

```bash
alembic init migrations
```

После чего `migrations/env.py` настроен на метаданные SQLModel и на чтение
строки подключения из `.env` (`code/migrations/env.py`):

```python
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel
import app.models                       # чтобы все таблицы попали в метаданные

load_dotenv()
config = context.config
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = SQLModel.metadata     # по этим метаданным сравнивается схема
```

Так строка подключения **передаётся в Alembic из `.env`**, а не хранится в
`alembic.ini`. Чтобы автогенерация подхватывала типы SQLModel, в шаблон
`migrations/script.py.mako` добавлен `import sqlmodel`.

Рабочие команды:

```bash
alembic revision --autogenerate -m "initial schema"   # создать миграцию
alembic upgrade head                                   # применить
```

Подробнее о применении миграций и о реальном выводе — на странице
[Подключение к БД и миграции](database.md).

## Переменные окружения (.env)

Секреты и параметры окружения вынесены в `.env` и читаются через
pydantic-settings (`code/app/core/config.py`). В репозиторий попадает только
шаблон `.env.example`:

```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finance_db
SECRET_KEY=super-secret-change-me-please
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DB_ECHO=false
```

## .gitignore

Чтобы в репозиторий не попадали виртуальное окружение, кэш и — главное —
секреты, настроен `.gitignore` (`code/.gitignore`):

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
*.env
!.env.example
.DS_Store
```

## Задание практики

> Реализовать все улучшения практики; понять, как передавать URL БД в
> `alembic.ini` через `.env`.

Выполнено: настроены Alembic, `.env`/`.env.example`, `.gitignore`; строка
подключения передаётся Alembic из переменной окружения `DATABASE_URL`.
