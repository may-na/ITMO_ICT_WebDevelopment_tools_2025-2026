"""Список URL-адресов для парсинга и утилита разбиения на равные части."""

URLS = [
    "https://example.com",
    "https://www.python.org",
    "https://docs.python.org/3/",
    "https://www.wikipedia.org",
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "https://en.wikipedia.org/wiki/Concurrency_(computer_science)",
    "https://en.wikipedia.org/wiki/Thread_(computing)",
    "https://en.wikipedia.org/wiki/Asynchronous_I/O",
    "https://fastapi.tiangolo.com",
    "https://www.sqlalchemy.org",
    "https://www.djangoproject.com",
    "https://pypi.org",
]


def split_list(items: list, parts: int) -> list[list]:
    """Разбить список на `parts` примерно равных частей."""
    parts = max(1, min(parts, len(items)))
    size = len(items) // parts
    remainder = len(items) % parts
    chunks: list[list] = []
    start = 0
    for i in range(parts):
        # первые `remainder` частей получают на один элемент больше
        end = start + size + (1 if i < remainder else 0)
        chunks.append(items[start:end])
        start = end
    return chunks
