"""Маршруты вызова парсера (подзадачи 2 и 3).

- POST /parser/parse        — синхронно дёргает отдельный сервис-парсер по HTTP
                              (демонстрация межконтейнерного взаимодействия);
- POST /parser/parse-async  — ставит задачу парсинга в очередь Celery;
- GET  /parser/result/{id}  — узнать статус/результат фоновой задачи.

Эндпоинты сделаны публичными (без JWT) для удобства проверки.
"""
import os

import requests
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Query

from app.core.celery_app import celery_app, parse_url_task

router = APIRouter(prefix="/parser", tags=["Парсер"])

# Адрес сервиса-парсера внутри docker-сети (имя сервиса из docker-compose)
PARSER_SERVICE_URL = os.getenv("PARSER_URL", "http://parser:8001")


@router.post("/parse")
def parse_via_service(url: str = Query(..., description="URL для парсинга")) -> dict:
    """Синхронный вызов: переслать URL сервису-парсеру и вернуть его ответ."""
    try:
        response = requests.post(
            f"{PARSER_SERVICE_URL}/parse", params={"url": url}, timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Сервис-парсер недоступен: {exc}")


@router.post("/parse-async")
def parse_async(url: str = Query(..., description="URL для парсинга")) -> dict:
    """Асинхронный вызов: поставить задачу парсинга в очередь Celery."""
    task = parse_url_task.delay(url)
    return {"task_id": task.id, "status": "queued", "url": url}


@router.get("/result/{task_id}")
def get_result(task_id: str) -> dict:
    """Получить статус и результат фоновой задачи по её идентификатору."""
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
    }
