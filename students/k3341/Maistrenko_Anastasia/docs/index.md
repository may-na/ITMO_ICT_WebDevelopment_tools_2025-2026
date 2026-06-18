# Лабораторные работы по Web-программированию

**Студент:** Майстренко Анастасия
**Группа:** К3341
**Курс:** «Средства Web-программирования», ИТМО, 2025–2026

Сайт-отчёт по лабораторным работам. Код каждой работы лежит в репозитории в
папках `Lr1/` и `Lr2/`.

## Работы

<div class="grid cards" markdown>

- **[ЛР1 — Серверное приложение на FastAPI](lab1/index.md)**

    Сервис учёта личных финансов: FastAPI + SQLModel + PostgreSQL + Alembic,
    аутентификация по JWT. 8 таблиц, связи 1:M и M:M, ассоциативная сущность,
    CRUD с вложенными объектами.

- **[ЛР2 — Потоки, процессы, асинхронность](lab2/index.md)**

    Сравнение `threading` / `multiprocessing` / `asyncio` на CPU-bound (сумма
    чисел) и I/O-bound (парсинг веб-страниц) нагрузках с замерами времени.

- **[ЛР3 — Docker, источники данных и очереди](lab3/index.md)**

    Упаковка приложения, БД и парсера в Docker (docker-compose), вызов парсера
    по HTTP и через очередь задач Celery + Redis (с фоновым worker и периодикой).

</div>

## Репозиторий

<https://github.com/may-na/ITMO_ICT_WebDevelopment_tools_2025-2026>

- ЛР1: `students/k3341/Maistrenko_Anastasia/Lr1`
- ЛР2: `students/k3341/Maistrenko_Anastasia/Lr2`
