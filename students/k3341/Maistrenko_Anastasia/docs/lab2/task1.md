# Задача 1. CPU-bound: сумма чисел

Три программы считают сумму чисел от 1 до N тремя подходами. Диапазон делится на
части (по числу воркеров), каждая часть суммируется отдельно, затем частичные
суммы складываются. Корректность проверяется по формуле Гаусса
`N·(N+1)/2`.

!!! warning "О значении N"
    По условию N = 10¹³. Просуммировать столько чисел обычным циклом в Python
    физически невозможно за разумное время (≈десятки часов), поэтому замеры
    делаются на практическом **N = 10⁸**. Целевое значение хранится в
    `common.py` как `TARGET_N`, рабочее задаётся аргументом `--n`. На выводы это
    не влияет: соотношение подходов от N не меняется.

Общая функция разбиения (`common.py`):

```python
def split_ranges(n: int, parts: int) -> list[tuple[int, int]]:
    parts = max(1, parts)
    chunk = n // parts
    ranges, start = [], 1
    for i in range(parts):
        end = n if i == parts - 1 else start + chunk - 1
        ranges.append((start, end))
        start = end + 1
    return ranges
```

## threading

Каждый поток суммирует свой отрезок и кладёт результат в общий список.

```python
def calculate_sum(start, end, results=None, index=None):
    total = 0
    for value in range(start, end + 1):
        total += value
    if results is not None and index is not None:
        results[index] = total
    return total

def run(n, workers):
    ranges = split_ranges(n, workers)
    results = [0] * len(ranges)
    threads = [threading.Thread(target=calculate_sum, args=(s, e, results, i))
               for i, (s, e) in enumerate(ranges)]
    for t in threads: t.start()
    for t in threads: t.join()
    return sum(results)
```

**Особенность:** из-за GIL потоки выполняют байткод по очереди, поэтому для
чистых вычислений ускорения нет (а с учётом накладных расходов на потоки время
даже чуть больше последовательного).

## multiprocessing

Пул процессов; `starmap` раздаёт каждому процессу пару `(start, end)`.

```python
def calculate_sum(start, end):
    total = 0
    for value in range(start, end + 1):
        total += value
    return total

def run(n, workers):
    ranges = split_ranges(n, workers)
    with Pool(processes=workers) as pool:
        partials = pool.starmap(calculate_sum, ranges)
    return sum(partials)
```

**Особенность:** каждый процесс — отдельный интерпретатор со своим GIL, поэтому
вычисления идут параллельно на разных ядрах. Для CPU-bound — единственный из трёх
подходов, дающий реальное ускорение. Есть накладные расходы на запуск процессов и
передачу данных (на macOS используется метод `spawn`, поэтому обязателен
`if __name__ == "__main__"`).

## async (asyncio)

Корутины запускаются через `asyncio.gather`.

```python
async def calculate_sum(start, end):
    total = 0
    for value in range(start, end + 1):
        total += value
    return total

async def run(n, workers):
    ranges = split_ranges(n, workers)
    partials = await asyncio.gather(*(calculate_sum(s, e) for s, e in ranges))
    return sum(partials)
```

**Особенность:** `asyncio` — это один поток и кооперативное переключение по
`await`. Внутри цикла суммирования точек `await` нет, переключаться не на чем,
поэтому корутины выполняются последовательно. Ускорения для CPU-bound нет — это
ровно та ситуация, для которой async **не** предназначен.

## Результаты замеров

`N = 10⁸`, воркеров = 8 (по числу ядер). Команда: `python benchmark.py --n 100000000 --workers 8`.

| Подход            | Время, с | Ускорение к последовательному |
|-------------------|---------:|------------------------------:|
| sequential        |    2.491 | 1.00× |
| threading         |    2.577 | 0.97× |
| **multiprocessing** | **0.598** | **4.17×** |
| async             |    2.507 | 0.99× |

## Анализ

- **multiprocessing** даёт ускорение ≈4× — вычисления реально распараллелились по
  ядрам в обход GIL. (Ускорение не ровно ×8 из-за накладных расходов на запуск
  процессов и сериализацию результатов.)
- **threading** не ускоряет и даже чуть медленнее последовательного варианта:
  GIL не даёт потокам считать одновременно, а переключение между ними добавляет
  накладные расходы.
- **async** практически равен последовательному: всё выполняется в одном потоке
  без точек переключения.

**Вывод:** для CPU-bound задач нужен `multiprocessing`; `threading` и `asyncio`
здесь бесполезны.
