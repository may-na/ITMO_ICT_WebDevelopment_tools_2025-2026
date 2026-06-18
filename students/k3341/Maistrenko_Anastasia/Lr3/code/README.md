# ЛР3 — Docker, источники данных и очереди

Упаковка приложения из ЛР1, парсера из ЛР2, базы данных, Redis и Celery в Docker
и оркестрация через docker-compose.

## Сервисы

| Сервис   | Что это                                   | Порт (хост) |
|----------|-------------------------------------------|-------------|
| `db`     | PostgreSQL (база из ЛР1)                   | 5435 → 5432 |
| `web`    | FastAPI-приложение ЛР1 + маршруты `/parser/*` | 8000        |
| `parser` | отдельный сервис-парсер (вызов по HTTP)    | 8001        |
| `redis`  | брокер/бэкенд Celery                       | —           |
| `worker` | Celery worker (фоновые задачи парсинга)    | —           |
| `beat`   | Celery beat (периодические задачи, бонус)  | —           |

`worker` и `beat` переиспользуют образ `web`, меняя лишь команду запуска.

## Запуск

```bash
cd Lr3/code
docker compose up --build
```

- Swagger UI приложения: <http://localhost:8000/docs>
- Сервис-парсер: <http://localhost:8001/docs>

Остановить и удалить контейнеры с томом БД:

```bash
docker compose down -v
```

## Что где реализовано

- **Подзадача 1 (Docker).** Dockerfile у `web` и `parser`, оркестрация в
  `docker-compose.yml`. Парсер вынесен в отдельный сервис и вызывается по HTTP.
- **Подзадача 2 (вызов парсера из FastAPI).** `POST /parser/parse?url=...` в
  приложении `web` пересылает запрос сервису `parser` (контейнер→контейнер) и
  возвращает результат.
- **Подзадача 3 (очередь).** `POST /parser/parse-async?url=...` ставит задачу в
  очередь Celery (брокер Redis); `worker` выполняет её в фоне; статус и результат
  — `GET /parser/result/{task_id}`. Бонус: периодическая задача в `beat`
  (парсит example.com каждые 2 минуты).

## Проверка (после `docker compose up`)

```bash
# Подзадача 2: синхронный вызов парсера через web -> parser
curl -X POST "http://localhost:8000/parser/parse?url=https://example.com"

# Подзадача 3: поставить задачу в очередь и узнать результат
curl -X POST "http://localhost:8000/parser/parse-async?url=https://www.python.org"
curl "http://localhost:8000/parser/result/<task_id>"

# Результаты парсинга в БД
docker compose exec db psql -U postgres -d finance_db -c "SELECT id,url,title,approach FROM parsed_page;"
```

## Эндпоинты парсера (`web`)

| Метод | Путь                      | Назначение                                |
|-------|---------------------------|-------------------------------------------|
| POST  | `/parser/parse`           | синхронно через сервис-парсер (подзадача 2) |
| POST  | `/parser/parse-async`     | поставить задачу в очередь Celery (подзадача 3) |
| GET   | `/parser/result/{task_id}`| статус и результат фоновой задачи         |

Остальные маршруты (`/auth`, `/accounts`, `/transactions`, ...) — из ЛР1.
