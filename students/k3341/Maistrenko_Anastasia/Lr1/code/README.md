# Personal Finance API — код приложения

Серверная часть ЛР1 на FastAPI + SQLModel + PostgreSQL.

## Требования

- Python 3.10+
- PostgreSQL

## Установка и запуск

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                 # указать DATABASE_URL, SECRET_KEY
createdb finance_db                  # создать БД (имя — как в DATABASE_URL)

alembic upgrade head                 # применить миграции
uvicorn app.main:app --reload        # запустить сервер
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## Миграции

```bash
alembic revision --autogenerate -m "описание"   # создать новую миграцию
alembic upgrade head                             # применить
alembic downgrade -1                             # откатить на шаг
```

## Структура

```text
app/
├── core/        # config.py, database.py, security.py
├── models/      # SQLModel-таблицы
├── schemas/     # Pydantic/SQLModel модели запросов и ответов
├── api/
│   ├── deps.py      # get_current_user (аутентификация по JWT)
│   └── routes/      # auth, accounts, categories, transactions, budgets, tags
└── main.py      # сборка приложения FastAPI
```

## Переменные окружения (`.env`)

| Переменная                    | Назначение                         |
|-------------------------------|------------------------------------|
| `DATABASE_URL`                | строка подключения к PostgreSQL    |
| `SECRET_KEY`                  | ключ подписи JWT                   |
| `ALGORITHM`                   | алгоритм подписи (по умолч. HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | время жизни токена                 |
| `DB_ECHO`                     | логировать SQL (true/false)        |
