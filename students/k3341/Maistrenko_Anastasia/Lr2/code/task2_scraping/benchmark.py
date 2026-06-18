"""Сравнительный замер трёх подходов для Задачи 2 (парсинг + запись в БД).

Перед каждым подходом таблица parsed_page очищается, затем измеряется время
парсинга всех URL. В конце печатается таблица времени и ускорения относительно
последовательного варианта.

Запуск:
    python benchmark.py --workers 4
"""
import argparse
import asyncio
import time

import requests
from bs4 import BeautifulSoup

import async_scraper
import multiprocessing_scraper
import threading_scraper
from db import clear_pages, count_pages, init_db, save_page
from urls import URLS

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Lab2Scraper/1.0)"}


def warmup(urls: list[str]) -> None:
    """Прогрев: один незамеряемый проход, чтобы «разогреть» DNS/TLS/кеши.

    Без него первый замеряемый подход штрафуется за холодный старт сети и
    сравнение получается нечестным.
    """
    for url in urls:
        try:
            requests.get(url, headers=HEADERS, timeout=15)
        except Exception:
            pass


def run_sequential(urls: list[str]) -> float:
    """Последовательный парсинг (базовая линия)."""
    start_time = time.perf_counter()
    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else "(без заголовка)"
            )
            save_page(url, title, "sequential")
        except Exception as exc:
            print(f"[sequential] ОШИБКА {url}: {exc}")
    return time.perf_counter() - start_time


def main() -> None:
    parser = argparse.ArgumentParser(description="Бенчмарк Задачи 2")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    workers = args.workers

    init_db()
    print(f"URL-адресов: {len(URLS)}, воркеров: {workers}")
    print("прогрев сети (DNS/TLS)...")
    warmup(URLS)
    print()

    results = []
    for name, func in (
        ("sequential", lambda: run_sequential(URLS)),
        ("threading", lambda: threading_scraper.run(URLS, workers)),
        ("multiprocessing", lambda: multiprocessing_scraper.run(URLS, workers)),
        ("async", lambda: asyncio.run(async_scraper.run(URLS))),
    ):
        clear_pages()
        elapsed = func()
        results.append((name, elapsed, count_pages()))

    base = results[0][1]
    print(f"\n{'подход':<18}{'время, с':>12}{'ускорение':>12}{'строк в БД':>12}")
    print("-" * 56)
    for name, elapsed, rows in results:
        speedup = base / elapsed if elapsed else 0
        print(f"{name:<18}{elapsed:>12.3f}{speedup:>11.2f}x{rows:>12}")


if __name__ == "__main__":
    main()
