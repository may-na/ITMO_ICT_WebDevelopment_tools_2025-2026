# Лабораторная работа 3. Docker, источники данных и очереди

**Студент:** Майстренко Анастасия, гр. К3341

Упаковка приложения из ЛР1, парсера из ЛР2, базы данных, Redis и Celery в Docker
и оркестрация через docker-compose.

- **Подзадача 1 (Docker):** Dockerfile для `web` и `parser`, оркестрация в
  docker-compose; парсер вынесен в отдельный контейнер.
- **Подзадача 2 (HTTP):** `POST /parser/parse` — `web` вызывает сервис `parser`
  по HTTP и возвращает результат.
- **Подзадача 3 (очередь):** `POST /parser/parse-async` ставит задачу в Celery
  (брокер Redis), `worker` выполняет её в фоне, `GET /parser/result/{id}`
  отдаёт статус/результат. Бонус — периодическая задача (Celery beat).

Код и инструкция запуска — в [`code/`](code/README.md):

```bash
cd code && docker compose up --build
# Swagger: http://localhost:8000/docs , парсер: http://localhost:8001/docs
```

Подробный разбор с архитектурой и проверками — в отчёте, раздел «ЛР3»:
<https://may-na.github.io/ITMO_ICT_WebDevelopment_tools_2025-2026/lab3/>
