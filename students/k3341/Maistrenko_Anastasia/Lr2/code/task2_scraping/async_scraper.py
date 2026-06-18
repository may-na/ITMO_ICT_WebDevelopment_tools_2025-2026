"""Задача 2 — подход ASYNC (asyncio + aiohttp).

Параллельный парсинг страниц асинхронными запросами. Все запросы запускаются
одной корутиной-планировщиком через asyncio.gather; пока один запрос ждёт ответа
сети, цикл событий переключается на другие. Для I/O-bound задач это самый
эффективный и «лёгкий» по ресурсам подход — один поток обслуживает десятки
соединений.

Запись в БД синхронная (psycopg2), поэтому выполняется в отдельном потоке через
asyncio.to_thread(), чтобы не блокировать цикл событий.

Запуск:
    python async_scraper.py
"""
import asyncio
import ssl
import time

import aiohttp
import certifi
from bs4 import BeautifulSoup

from db import count_pages, init_db, save_page
from urls import URLS

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Lab2Scraper/1.0)"}
APPROACH = "async"

# Общая HTTP-сессия для всех запросов (создаётся внутри event loop в run()).
_session: aiohttp.ClientSession | None = None


async def parse_and_save(url: str) -> str | None:
    """Асинхронно загрузить страницу, извлечь <title> и сохранить в БД."""
    try:
        async with _session.get(url) as response:
            response.raise_for_status()
            html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        title = (
            soup.title.string.strip()
            if soup.title and soup.title.string
            else "(без заголовка)"
        )
        # Синхронную запись в БД выполняем в отдельном потоке, чтобы не
        # блокировать цикл событий.
        await asyncio.to_thread(save_page, url, title, APPROACH)
        print(f"[{APPROACH}] {url} -> {title}")
        return title
    except Exception as exc:
        print(f"[{APPROACH}] ОШИБКА {url}: {exc}")
        return None


async def run(urls: list[str]) -> float:
    """Запустить асинхронный парсинг всех URL. Вернуть время выполнения (с)."""
    global _session
    timeout = aiohttp.ClientTimeout(total=15)
    # aiohttp на macOS не использует системные сертификаты — берём CA из certifi,
    # иначе HTTPS-запросы падают с CERTIFICATE_VERIFY_FAILED.
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(
        headers=HEADERS, timeout=timeout, connector=connector
    ) as session:
        _session = session
        start_time = time.perf_counter()
        await asyncio.gather(*(parse_and_save(url) for url in urls))
        elapsed = time.perf_counter() - start_time
    _session = None
    return elapsed


if __name__ == "__main__":
    init_db()
    total_elapsed = asyncio.run(run(URLS))
    print(f"\n[async] страниц={len(URLS)}, время={total_elapsed:.3f} с")
    print(f"строк в parsed_page: {count_pages()}")
