# Задача 2. I/O-bound: параллельный парсинг + запись в БД

Три программы параллельно загружают набор веб-страниц, извлекают `<title>` и
сохраняют его в базу данных. Используется **та же БД, что и в ЛР1** (PostgreSQL,
`finance_db`); для результатов парсинга заведена отдельная таблица `parsed_page`.

## База данных (`db.py`)

```python
def init_db():
    # CREATE TABLE IF NOT EXISTS parsed_page (id, url, title, approach, parsed_at)
    ...

def save_page(url, title, approach):
    conn = get_connection()          # новое подключение на каждый вызов
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO parsed_page (url, title, approach) VALUES (%s, %s, %s);",
                (url, title, approach),
            )
        conn.commit()
    finally:
        conn.close()
```

Новое короткоживущее подключение на каждое сохранение — безопасно и для потоков,
и для процессов (соединение psycopg2 нельзя разделять между процессами). Так
пишут в БД версии **threading** и **multiprocessing**.

Async-версия пишет в БД **по-настоящему асинхронно** — через драйвер `asyncpg`
(пул соединений, операции `await`), не блокируя цикл событий:

```python
async def create_async_pool():
    return await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10)

async def save_page_async(pool, url, title, approach):
    async with pool.acquire() as conn:                 # соединение из пула
        await conn.execute(
            "INSERT INTO parsed_page (url, title, approach) VALUES ($1, $2, $3);",
            url, title, approach,
        )
```

Список URL делится на равные части (`urls.split_list`), кроме async, где все
запросы и так запускаются конкурентно одним `gather`.

## threading

```python
def parse_and_save(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title else "(без заголовка)"
    save_page(url, title, "threading")
    print(f"[threading] {url} -> {title}")

def run(urls, workers):
    chunks = split_list(urls, workers)
    threads = [threading.Thread(target=lambda c=c: [parse_and_save(u) for u in c])
               for c in chunks]
    for t in threads: t.start()
    for t in threads: t.join()
```

**Особенность:** во время сетевого запроса (`requests.get`) GIL освобождается,
поэтому потоки реально ждут ответы параллельно → заметное ускорение.

## multiprocessing

```python
def process_chunk(chunk):
    for url in chunk:
        parse_and_save(url)

def run(urls, workers):
    chunks = split_list(urls, workers)
    with Pool(processes=workers) as pool:
        pool.map(process_chunk, chunks)
```

**Особенность:** процессы тоже распараллеливают ожидание, но платят за запуск
процессов и сериализацию. Для сетевых задач это избыточно и обычно медленнее
потоков/async.

## async (asyncio + aiohttp)

```python
async def parse_and_save(url):
    async with _session.get(url) as response:            # запрос — aiohttp
        html = await response.text()
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else "(без заголовка)"
    await save_page_async(_pool, url, title, "async")     # запись в БД — asyncpg (await)

async def run(urls):
    _pool = await create_async_pool()                    # пул соединений asyncpg
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        await asyncio.gather(*(parse_and_save(u) for u in urls))
```

**Особенности:**

- один поток обслуживает все запросы сразу — пока одна страница грузится, цикл
  событий переключается на другие;
- запись в БД тоже **асинхронная** — через драйвер `asyncpg` (пул соединений,
  `await`), поэтому цикл событий не блокируется ни на сети, ни на работе с БД;
- на macOS aiohttp не использует системные сертификаты, поэтому SSL-контекст
  берётся из `certifi` (иначе `CERTIFICATE_VERIFY_FAILED`).

## Результаты замеров

12 URL, воркеров = 4, перед замерами — прогрев сети (DNS/TLS). Команда:
`python benchmark.py --workers 4`.

| Подход            | Время, с | Ускорение | Строк сохранено |
|-------------------|---------:|----------:|----------------:|
| sequential        |   17.202 | 1.00×     | 12 |
| threading         |    5.686 | 3.03×     | 12 |
| multiprocessing   |    7.702 | 2.23×     | 12 |
| **async**         | **2.081** | **8.26×** | 12 |

## Анализ

- **async** — лидер (≈8×): один поток с минимальными накладными расходами держит
  все соединения одновременно. Идеален для большого числа сетевых запросов.
- **threading** — хорошее ускорение (≈3×): GIL освобождается на время сетевого
  ожидания. Ограничено числом потоков (здесь 4).
- **multiprocessing** — ускорение есть (≈2×), но меньше: накладные расходы на
  процессы и их запуск «съедают» выигрыш, для I/O это неоптимально.

**Вывод:** для I/O-bound задач лучший выбор — `asyncio` (или `threading`);
`multiprocessing` здесь избыточен.
