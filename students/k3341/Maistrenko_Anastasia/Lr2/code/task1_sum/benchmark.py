"""Сравнительный замер трёх подходов для Задачи 1.

Запускает последовательный вариант (базовая линия) и три параллельных
(threading, multiprocessing, async) на одном и том же N, печатает таблицу
времени и ускорения относительно последовательного варианта.

Запуск:
    python benchmark.py --n 100000000 --workers 8
"""
import argparse
import time

from common import DEFAULT_N, expected_sum
from threading_sum import calculate_sum  # тот же цикл, что и в остальных
from threading_sum import run as run_threading
from multiprocessing_sum import run as run_multiprocessing
from async_sum import run as run_async


def run_sequential(n: int) -> tuple[int, float]:
    """Однопоточный/однопроцессный базовый замер тем же циклом."""
    start_time = time.perf_counter()
    total = calculate_sum(1, n)
    return total, time.perf_counter() - start_time


def main() -> None:
    parser = argparse.ArgumentParser(description="Бенчмарк Задачи 1")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    n, workers = args.n, args.workers
    check = expected_sum(n)
    print(f"N = {n}, воркеров = {workers}, контроль = {check}\n")

    results = []
    for name, func in (
        ("sequential", lambda: run_sequential(n)),
        ("threading", lambda: run_threading(n, workers)),
        ("multiprocessing", lambda: run_multiprocessing(n, workers)),
        ("async", lambda: run_async_sync(n, workers)),
    ):
        total, elapsed = func()
        ok = "OK" if total == check else "ОШИБКА"
        results.append((name, elapsed, ok))

    base = results[0][1]
    print(f"{'подход':<18}{'время, с':>12}{'ускорение':>12}{'':>8}")
    print("-" * 50)
    for name, elapsed, ok in results:
        speedup = base / elapsed if elapsed else 0
        print(f"{name:<18}{elapsed:>12.3f}{speedup:>11.2f}x   {ok}")


def run_async_sync(n: int, workers: int) -> tuple[int, float]:
    """Обёртка, чтобы запускать async-вариант из синхронного кода."""
    import asyncio
    return asyncio.run(run_async(n, workers))


if __name__ == "__main__":
    main()
