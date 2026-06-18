# ЛР2 — Потоки, процессы, асинхронность

Код двух задач: сравнение threading / multiprocessing / async на CPU-bound
(сумма чисел) и I/O-bound (парсинг веб-страниц) нагрузках.

## Установка

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Для Задачи 2 нужна БД из ЛР1 (PostgreSQL). Скопируйте `.env.example` в `.env` и
укажите свой `DATABASE_URL` — скрипты сами создадут таблицу `parsed_page`.

## Задача 1 — сумма чисел (CPU-bound)

```bash
cd task1_sum
python threading_sum.py        --n 100000000 --workers 8
python multiprocessing_sum.py  --n 100000000 --workers 8
python async_sum.py            --n 100000000 --workers 8
python benchmark.py            --n 100000000 --workers 8   # сравнительная таблица
```

> Целевое по условию N = 10¹³ задано в `common.py` как `TARGET_N`. Суммировать
> столько чисел циклом на Python нереально (≈десятки часов), поэтому замеры
> делаются на практическом N (по умолчанию 10⁸); выводы от этого не меняются.

## Задача 2 — парсинг (I/O-bound)

```bash
cd task2_scraping
python threading_scraper.py        --workers 4
python multiprocessing_scraper.py  --workers 4
python async_scraper.py
python benchmark.py                --workers 4              # сравнительная таблица
```

Результаты складываются в таблицу `parsed_page` (поля `url`, `title`,
`approach`, `parsed_at`).

## Краткие выводы

| Нагрузка             | Победитель        | Почему                                  |
|----------------------|-------------------|-----------------------------------------|
| CPU-bound (Задача 1) | multiprocessing   | обходит GIL, реально грузит все ядра    |
| I/O-bound (Задача 2) | async / threading | GIL освобождается на время ожидания сети |

Подробный разбор и таблицы времени — в отчёте (раздел «ЛР2»).
