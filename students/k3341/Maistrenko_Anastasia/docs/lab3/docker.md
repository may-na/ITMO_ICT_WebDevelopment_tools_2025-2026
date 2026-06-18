# Подзадачи 1–2. Docker и вызов парсера по HTTP

## Сервис-парсер (отдельное приложение)

Парсер вынесен в отдельный контейнер `parser` — это FastAPI-приложение с
эндпоинтом `POST /parse`, который загружает страницу, извлекает `<title>` и
сохраняет его в общую БД (таблица `parsed_page`).

```python
@app.post("/parse")
def parse(url: str = Query(...)):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "(без заголовка)"
        save_page(url, title)
        return {"message": "Parsing completed", "url": url, "title": title}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Dockerfile приложения (`web`)

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x entrypoint.sh
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
```

`entrypoint.sh` сначала применяет миграции, потом запускает сервер:

```sh
#!/bin/sh
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

У `parser` — аналогичный, более простой Dockerfile (запускает `uvicorn main:app`
на порту 8001).

## docker-compose.yml

Оркестрирует все сервисы; `web` поднимается только после того, как БД пройдёт
healthcheck (`depends_on … condition: service_healthy`):

```yaml
services:
  db:
    image: postgres:16
    environment: { POSTGRES_USER: postgres, POSTGRES_PASSWORD: postgres, POSTGRES_DB: finance_db }
    ports: ["5435:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d finance_db"]
      interval: 5s
      retries: 10
  web:
    build: ./web
    image: lab3-web:latest
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/finance_db
      PARSER_URL: http://parser:8001
      CELERY_BROKER_URL: redis://redis:6379/0
    ports: ["8000:8000"]
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
  parser:
    build: ./parser
    environment: { DATABASE_URL: postgresql://postgres:postgres@db:5432/finance_db }
    ports: ["8001:8001"]
    depends_on:
      db: { condition: service_healthy }
  # redis, worker, beat — см. раздел «Очередь Celery»
```

Внутри docker-сети сервисы обращаются друг к другу по имени: `db`, `redis`,
`parser`.

## Подзадача 2. Вызов парсера из FastAPI по HTTP

В приложении `web` есть маршрут, который пересылает URL сервису-парсеру
(контейнер → контейнер) и возвращает его ответ клиенту:

```python
PARSER_SERVICE_URL = os.getenv("PARSER_URL", "http://parser:8001")

@router.post("/parse")
def parse_via_service(url: str = Query(...)):
    try:
        response = requests.post(f"{PARSER_SERVICE_URL}/parse",
                                 params={"url": url}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Сервис-парсер недоступен: {exc}")
```

## Проверка

```text
$ docker compose up --build
...
web-1  | INFO  [alembic] Running upgrade -> 81aa61fb58d7, initial schema
web-1  | INFO:     Application startup complete.

$ curl -X POST "http://localhost:8000/parser/parse?url=https://example.com"
{"message":"Parsing completed","url":"https://example.com","title":"Example Domain"}
```

Результат сохраняется в БД (поле `approach = parser-service`):

```text
 id |        url          |     title      |    approach
----+---------------------+----------------+----------------
  1 | https://example.com | Example Domain | parser-service
```
