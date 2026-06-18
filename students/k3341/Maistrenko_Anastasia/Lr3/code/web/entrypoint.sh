#!/bin/sh
# Точка входа веб-сервиса: применяем миграции и запускаем сервер.
# База к этому моменту готова (в docker-compose web ждёт healthcheck БД).
set -e

echo "Применяем миграции Alembic..."
alembic upgrade head

echo "Запускаем uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
