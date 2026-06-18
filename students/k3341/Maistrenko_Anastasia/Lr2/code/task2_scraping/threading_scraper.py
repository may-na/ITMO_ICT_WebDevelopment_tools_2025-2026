"""Задача 2 — подход THREADING.

Параллельный парсинг страниц потоками. Список URL делится на равные части, по
потоку на часть. Парсинг — это I/O-bound работа (ожидание ответа сети), а на
время операций ввода-вывода Python освобождает GIL, поэтому потоки дают
реальное ускорение относительно последовательного варианта.

Запуск:
    python threading_scraper.py --workers 4
"""
import argparse
import threading
import time

import requests
from bs4 import BeautifulSoup

from db import count_pages, init_db, save_page
from urls import URLS, split_list

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Lab2Scraper/1.0)"}
APPROACH = "threading"


def parse_and_save(url: str) -> str | None:
    """Загрузить страницу, извлечь <title>, сохранить в БД и вывести результат."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = (
            soup.title.string.strip()
            if soup.title and soup.title.string
            else "(без заголовка)"
        )
        save_page(url, title, APPROACH)
        print(f"[{APPROACH}] {url} -> {title}")
        return title
    except Exception as exc:
        print(f"[{APPROACH}] ОШИБКА {url}: {exc}")
        return None


def _worker(chunk: list[str]) -> None:
    for url in chunk:
        parse_and_save(url)


def run(urls: list[str], workers: int) -> float:
    """Запустить парсинг в `workers` потоках. Вернуть время выполнения (с)."""
    chunks = split_list(urls, workers)
    threads = [threading.Thread(target=_worker, args=(chunk,)) for chunk in chunks]

    start_time = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return time.perf_counter() - start_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Парсинг через threading")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    init_db()
    elapsed = run(URLS, args.workers)
    print(f"\n[threading] страниц={len(URLS)}, потоков={args.workers}, время={elapsed:.3f} с")
    print(f"строк в parsed_page: {count_pages()}")
