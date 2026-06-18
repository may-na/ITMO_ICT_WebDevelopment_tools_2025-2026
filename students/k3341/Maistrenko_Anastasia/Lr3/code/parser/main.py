"""Сервис-парсер (подзадача 1, п.4).

Отдельное FastAPI-приложение, которое умеет по HTTP принять URL, загрузить
страницу, извлечь её заголовок и сохранить в общую БД (таблица parsed_page).
Запускается в отдельном контейнере; основное приложение обращается к нему по
адресу http://parser:8001 внутри docker-сети.
"""
import os

import psycopg2
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Parser Service", version="1.0.0")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@db:5432/finance_db"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Lab3Parser/1.0)"}


def ensure_table() -> None:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS parsed_page (
                    id         SERIAL PRIMARY KEY,
                    url        TEXT NOT NULL,
                    title      TEXT,
                    approach   TEXT,
                    parsed_at  TIMESTAMP DEFAULT now()
                );
                """
            )
        conn.commit()
    finally:
        conn.close()


def save_page(url: str, title: str) -> None:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO parsed_page (url, title, approach) VALUES (%s, %s, %s);",
                (url, title, "parser-service"),
            )
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def on_startup() -> None:
    ensure_table()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/parse")
def parse(url: str = Query(..., description="URL для парсинга")) -> dict:
    """Загрузить страницу, извлечь <title>, сохранить в БД и вернуть результат."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = (
            soup.title.string.strip()
            if soup.title and soup.title.string
            else "(без заголовка)"
        )
        save_page(url, title)
        return {"message": "Parsing completed", "url": url, "title": title}
    except requests.RequestException as exc:
        raise HTTPException(status_code=500, detail=str(exc))
