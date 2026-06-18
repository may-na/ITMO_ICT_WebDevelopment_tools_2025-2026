# Подзадача 3. Вызов парсера через очередь (Celery + Redis)

Долгие операции (парсинг) логично выполнять в фоне, чтобы не блокировать
HTTP-ответ. Для этого используется **Celery** (очередь задач) с **Redis** в роли
брокера и хранилища результатов.

## Настройка Celery (`app/core/celery_app.py`)

```python
celery_app = Celery(
    "lab3",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)
celery_app.conf.update(task_track_started=True)

@celery_app.task(name="parse_url")
def parse_url_task(url: str) -> dict:
    _ensure_table()
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title else "(без заголовка)"
    _save(url, title, "celery")
    return {"url": url, "title": title}
```

## Эндпоинты (`web`)

```python
@router.post("/parse-async")
def parse_async(url: str = Query(...)):
    task = parse_url_task.delay(url)          # кладём задачу в очередь
    return {"task_id": task.id, "status": "queued", "url": url}

@router.get("/result/{task_id}")
def get_result(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": result.status,
            "result": result.result if result.successful() else None}
```

## Сервисы в docker-compose

```yaml
  redis:
    image: redis:7-alpine

  worker:
    image: lab3-web:latest
    command: celery -A app.core.celery_app:celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/finance_db
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }

  beat:
    image: lab3-web:latest
    command: celery -A app.core.celery_app:celery_app beat --loglevel=info
    depends_on:
      redis: { condition: service_started }
```

## Проверка

```text
$ curl -X POST "http://localhost:8000/parser/parse-async?url=https://www.python.org"
{"task_id":"08bd8661-a722-4784-b5ca-c4c563ad2acb","status":"queued","url":"https://www.python.org"}

$ curl "http://localhost:8000/parser/result/08bd8661-a722-4784-b5ca-c4c563ad2acb"
{"task_id":"08bd...","status":"SUCCESS","result":{"url":"https://www.python.org","title":"Welcome to Python.org"}}
```

Лог worker:

```text
worker-1 | celery@... ready.
worker-1 | Task parse_url[08bd8661-...] received
worker-1 | Task parse_url[08bd8661-...] succeeded in 1.62s: {'url': 'https://www.python.org', 'title': 'Welcome to Python.org'}
```

Запись в БД (поле `approach = celery`):

```text
 id |          url           |         title         | approach
----+------------------------+-----------------------+----------
  2 | https://www.python.org | Welcome to Python.org | celery
```

## Бонус. Периодические задачи (Celery beat)

Расписание задаётся в конфигурации Celery — каждые 2 минуты автоматически
парсится `example.com`:

```python
celery_app.conf.beat_schedule = {
    "parse-example-every-2-minutes": {
        "task": "parse_url",
        "schedule": 120.0,
        "args": ("https://example.com",),
    }
}
```

Сервис `beat` (`celery ... beat`) читает это расписание и периодически кладёт
задачу в ту же очередь, которую разбирает `worker`.

## Вывод

Синхронный путь (подзадача 2) возвращает результат сразу, но клиент ждёт весь
парсинг. Асинхронный путь (подзадача 3) мгновенно отвечает `task_id`, а парсинг
выполняется в фоне отдельным worker'ом — приложение остаётся отзывчивым. Такой
подход — основа фоновой обработки в реальных сервисах.
