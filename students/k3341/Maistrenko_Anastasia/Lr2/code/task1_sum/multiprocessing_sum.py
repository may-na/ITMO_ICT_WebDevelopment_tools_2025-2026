"""Задача 1 — подход MULTIPROCESSING.

Сумма чисел от 1 до N считается несколькими процессами (модуль multiprocessing).
Каждый процесс — отдельный интерпретатор Python со своим GIL, поэтому вычисления
идут по-настоящему параллельно на разных ядрах CPU. Для CPU-bound задачи это
даёт реальное ускорение.

Запуск:
    python multiprocessing_sum.py --n 100000000 --workers 8
"""
import argparse
import time
from multiprocessing import Pool

from common import DEFAULT_N, expected_sum, split_ranges


def calculate_sum(start: int, end: int) -> int:
    """Просуммировать целые числа в диапазоне [start, end] (включительно)."""
    total = 0
    for value in range(start, end + 1):
        total += value
    return total


def run(n: int, workers: int) -> tuple[int, float]:
    """Запустить подсчёт в `workers` процессах. Вернуть (сумма, время)."""
    ranges = split_ranges(n, workers)

    start_time = time.perf_counter()
    # Пул процессов; starmap передаёт каждому процессу пару (start, end)
    with Pool(processes=workers) as pool:
        partials = pool.starmap(calculate_sum, ranges)
    total = sum(partials)
    elapsed = time.perf_counter() - start_time
    return total, elapsed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сумма 1..N через multiprocessing")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    total, elapsed = run(args.n, args.workers)
    check = expected_sum(args.n)
    print(f"[multiprocessing] N={args.n}, процессов={args.workers}")
    print(f"  сумма       = {total}")
    print(f"  контроль    = {check} ({'OK' if total == check else 'ОШИБКА'})")
    print(f"  время       = {elapsed:.3f} с")
