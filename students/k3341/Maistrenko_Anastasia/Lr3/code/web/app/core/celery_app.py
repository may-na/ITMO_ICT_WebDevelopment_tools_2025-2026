"""Конфигурация Celery и фоновая задача парсинга (подзадача 3).

Celery — асинхронная очередь задач; брокером и хранилищем результатов выступает
Redis. Задача parse_url_task загружает страницу, извлекает <title> и сохраняет
его в ту же БД, что использует основное приложение (таблица parsed_page).
"""
import os

import psycopg2
import requests
from bs4 import BeautifulSoup
from celery import Celery

from app.core.config import settings

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery("lab3", broker=BROKER_URL, backend=RESULT_BACKEND)
celery_app.conf.update(task_track_started=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Lab3Worker/1.0)"}


def _ensure_table() -> None:
    """Создать таблицу parsed_page, если её ещё нет (идемпотентно)."""
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS parsed_page (
                    id         SERIAL PRIMARY KEY,
                    url        TEXT NOT NULL,
                    title      TEXT,
                    approach   TEXT,
                    parsed_at  TIMESTAMP DEFAULT now()
                );
                """
            )
        conn.commit()
    finally:
        conn.close()


def _save(url: str, title: str, approach: str) -> None:
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO parsed_page (url, title, approach) VALUES (%s, %s, %s);",
                (url, title, approach),
            )
        conn.commit()
    finally:
        conn.close()


@celery_app.task(name="parse_url")
def parse_url_task(url: str) -> dict:
    """Фоновая задача: загрузить страницу, распарсить заголовок, сохранить в БД."""
    _ensure_table()
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = (
        soup.title.string.strip()
        if soup.title and soup.title.string
        else "(без заголовка)"
    )
    _save(url, title, "celery")
    return {"url": url, "title": title}


# --- Бонус: периодическая задача (Celery beat) ------------------------------
# Каждые 2 минуты автоматически парсим example.com — демонстрация расписания.
celery_app.conf.beat_schedule = {
    "parse-example-every-2-minutes": {
        "task": "parse_url",
        "schedule": 120.0,
        "args": ("https://example.com",),
    }
}
