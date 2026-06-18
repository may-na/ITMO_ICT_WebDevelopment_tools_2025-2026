"""Задача 1 — подход THREADING.

Сумма чисел от 1 до N считается несколькими потоками (модуль threading).
Диапазон делится на части, каждый поток суммирует свою часть. Поскольку
вычисление CPU-bound, а потоки в CPython делят один GIL, реального ускорения
относительно последовательного варианта не будет (потоки выполняются по
очереди, а не одновременно).

Запуск:
    python threading_sum.py --n 100000000 --workers 8
"""
import argparse
import threading
import time

from common import DEFAULT_N, expected_sum, split_ranges


def calculate_sum(start: int, end: int, results: list | None = None,
                  index: int | None = None) -> int:
    """Просуммировать целые числа в диапазоне [start, end] (включительно).

    Если переданы results/index — записать частичную сумму по индексу
    (так поток возвращает результат в общий список).
    """
    total = 0
    for value in range(start, end + 1):
        total += value
    if results is not None and index is not None:
        results[index] = total
    return total


def run(n: int, workers: int) -> tuple[int, float]:
    """Запустить подсчёт в `workers` потоках. Вернуть (сумма, время в секундах)."""
    ranges = split_ranges(n, workers)
    results = [0] * len(ranges)
    threads: list[threading.Thread] = []

    start_time = time.perf_counter()
    for index, (start, end) in enumerate(ranges):
        thread = threading.Thread(target=calculate_sum, args=(start, end, results, index))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    total = sum(results)
    elapsed = time.perf_counter() - start_time
    return total, elapsed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сумма 1..N через threading")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    total, elapsed = run(args.n, args.workers)
    check = expected_sum(args.n)
    print(f"[threading] N={args.n}, потоков={args.workers}")
    print(f"  сумма       = {total}")
    print(f"  контроль    = {check} ({'OK' if total == check else 'ОШИБКА'})")
    print(f"  время       = {elapsed:.3f} с")
