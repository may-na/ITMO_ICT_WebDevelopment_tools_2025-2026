# Образ основного приложения FastAPI (а также Celery worker/beat — они
# переиспользуют этот же образ, меняя только команду запуска).
FROM python:3.11-slim

# Без .pyc и с небуферизованным выводом — удобнее логи в контейнере
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Сначала зависимости — лучше кешируется слой
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Затем исходный код приложения
COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

# По умолчанию запускаем веб-приложение (worker/beat переопределяют command в compose)
CMD ["sh", "entrypoint.sh"]
