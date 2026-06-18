"""Точка входа приложения FastAPI «Личные финансы».

Запуск (из каталога code/):
    uvicorn app.main:app --reload

Интерактивная документация Swagger UI: http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from app.api.routes import (
    accounts,
    auth,
    budgets,
    categories,
    parser,
    tags,
    transactions,
)

app = FastAPI(
    title="Personal Finance API",
    description=(
        "Серверное приложение для учёта личных финансов (ЛР1).\n\n"
        "Возможности: счета, категории доходов/расходов, транзакции с тегами, "
        "бюджеты с лимитами по категориям. Аутентификация — по JWT.\n\n"
        "ЛР3: вызов парсера по HTTP и через очередь Celery — маршруты /parser/*."
    ),
    version="1.0.0",
)

# Подключаем маршруты по доменным областям
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(tags.router)
app.include_router(parser.router)


@app.get("/", tags=["Служебные"])
def root() -> dict:
    """Корневой эндпоинт для быстрой проверки, что сервис жив."""
    return {"app": "Personal Finance API", "status": "ok", "docs": "/docs"}
