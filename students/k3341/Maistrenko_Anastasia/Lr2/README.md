# Лабораторная работа 2. Потоки. Процессы. Асинхронность

**Студент:** Майстренко Анастасия, гр. К3341

Сравнение `threading` / `multiprocessing` / `asyncio` на двух типах нагрузки:

- **Задача 1 (CPU-bound)** — суммирование чисел от 1 до N. Победитель —
  `multiprocessing` (обходит GIL).
- **Задача 2 (I/O-bound)** — параллельный парсинг веб-страниц с сохранением
  заголовков в БД из ЛР1 (`finance_db`, таблица `parsed_page`). Победитель —
  `asyncio`.

Код и инструкция запуска — в [`code/`](code/README.md).
Подробный разбор с таблицами времени — в отчёте, раздел «ЛР2»:
<https://may-na.github.io/ITMO_ICT_WebDevelopment_tools_2025-2026/lab2/>

## Структура

```text
Lr2/code/
├── task1_sum/         # CPU-bound: threading / multiprocessing / async + benchmark
├── task2_scraping/    # I/O-bound: парсеры + db.py + urls.py + benchmark
├── requirements.txt
└── .env.example
```
