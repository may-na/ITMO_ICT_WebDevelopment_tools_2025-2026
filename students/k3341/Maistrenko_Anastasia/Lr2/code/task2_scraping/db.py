"""Работа с базой данных для Задачи 2.

Используется та же БД, что и в ЛР1 (PostgreSQL, finance_db). Для результатов
парсинга заведена отдельная таблица ``parsed_page``.

Важная деталь для многозадачности:
  - threading / multiprocessing используют синхронный psycopg2 (на каждое
    сохранение — новое короткоживущее подключение; это безопасно и для потоков,
    и для процессов, т.к. соединение нельзя разделять между процессами);
  - async-версия пишет в БД по-настоящему асинхронно через драйвер asyncpg
    (пул соединений, операции await), не блокируя цикл событий.
"""
import os

import asyncpg
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


# --- Асинхронный доступ к БД (для async-версии парсера, драйвер asyncpg) ------
async def create_async_pool() -> "asyncpg.Pool":
    """Создать пул асинхронных подключений к БД.

    Пул создаётся один раз на запуск; задачи берут из него соединения через
    ``async with pool.acquire()`` — это и есть неблокирующая работа с БД.
    """
    return await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10)


async def save_page_async(pool: "asyncpg.Pool", url: str, title: str, approach: str) -> None:
    """Асинхронно сохранить заголовок страницы в БД (через пул asyncpg)."""
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO parsed_page (url, title, approach) VALUES ($1, $2, $3);",
            url,
            title,
            approach,
        )
