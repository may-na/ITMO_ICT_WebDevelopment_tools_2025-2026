"""Задача 1 — подход ASYNC (asyncio).

Сумма чисел от 1 до N оформлена как набор корутин, запущенных через
asyncio.gather. Важно понимать: asyncio — это кооперативная многозадачность в
ОДНОМ потоке. Для CPU-bound кода без операций ввода-вывода точек переключения
(await) нет, поэтому корутины фактически выполняются последовательно, и
ускорения относительно последовательного варианта не будет. Это наглядно
показывает, что async предназначен для I/O-bound, а не CPU-bound задач.

Запуск:
    python async_sum.py --n 100000000 --workers 8
"""
import argparse
import asyncio
import time

from common import DEFAULT_N, expected_sum, split_ranges


async def calculate_sum(start: int, end: int) -> int:
    """Корутина: просуммировать целые числа в диапазоне [start, end]."""
    total = 0
    for value in range(start, end + 1):
        total += value
    return total


async def run(n: int, workers: int) -> tuple[int, float]:
    """Запустить корутины подсчёта через gather. Вернуть (сумма, время)."""
    ranges = split_ranges(n, workers)

    start_time = time.perf_counter()
    partials = await asyncio.gather(*(calculate_sum(start, end) for start, end in ranges))
    total = sum(partials)
    elapsed = time.perf_counter() - start_time
    return total, elapsed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сумма 1..N через asyncio")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    total, elapsed = asyncio.run(run(args.n, args.workers))
    check = expected_sum(args.n)
    print(f"[async] N={args.n}, корутин={args.workers}")
    print(f"  сумма       = {total}")
    print(f"  контроль    = {check} ({'OK' if total == check else 'ОШИБКА'})")
    print(f"  время       = {elapsed:.3f} с")
