"""Работа с базой данных для Задачи 2.

Используется та же БД, что и в ЛР1 (PostgreSQL, finance_db). Для результатов
парсинга заведена отдельная таблица ``parsed_page``.

Важная деталь для многозадачности: на каждое сохранение открывается новое
короткоживущее подключение psycopg2. Это безопасно и для потоков, и для
процессов (соединение нельзя разделять между процессами), и легко вызывается из
async-кода через asyncio.to_thread().
"""
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# По умолчанию — локальная БД из ЛР1 (Homebrew PostgreSQL на порту 5433)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://mayna@localhost:5433/finance_db"
)


def get_connection():
    """Открыть новое подключение к БД."""
    return psycopg2.connect(DATABASE_URL)


def init_db() -> None:
    """Создать таблицу parsed_page, если её ещё нет."""
    conn = get_connection()
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


def save_page(url: str, title: str, approach: str) -> None:
    """Сохранить заголовок страницы в БД (новое подключение на каждый вызов)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO parsed_page (url, title, approach) VALUES (%s, %s, %s);",
                (url, title, approach),
            )
        conn.commit()
    finally:
        conn.close()


def clear_pages() -> None:
    """Очистить таблицу parsed_page (удобно перед чистым замером)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE parsed_page RESTART IDENTITY;")
        conn.commit()
    finally:
        conn.close()


def count_pages() -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM parsed_page;")
            return cur.fetchone()[0]
    finally:
        conn.close()
