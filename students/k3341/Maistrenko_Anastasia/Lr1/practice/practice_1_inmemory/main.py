"""Практика 1. Основы FastAPI на временной (in-memory) базе данных.

Демонстрирует базовые возможности FastAPI без подключения к настоящей БД:
  - модели данных на Pydantic (BaseModel) с типизацией;
  - перечисления (Enum) для ограниченного набора значений;
  - вложенный объект (owner) и список вложенных объектов (operations);
  - CRUD-эндпоинты для основной сущности (кошелёк) и для вложенной
    сущности (операции внутри кошелька);
  - автодокументацию Swagger UI по адресу /docs.

Запуск (из этой папки):
    uvicorn main:app --reload
"""
from datetime import date
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Практика 1 — Кошельки (in-memory)")


# --- Модели данных -----------------------------------------------------------
class Currency(str, Enum):
    """Допустимые валюты (пример использования Enum)."""

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class OperationType(str, Enum):
    income = "income"
    expense = "expense"


class Owner(BaseModel):
    """Вложенный объект — владелец кошелька."""

    name: str
    email: str


class Operation(BaseModel):
    """Элемент списка вложенных объектов — операция по кошельку."""

    id: int
    amount: float = Field(gt=0)
    type: OperationType
    comment: Optional[str] = None
    op_date: date = Field(default_factory=date.today)


class Wallet(BaseModel):
    """Основная сущность: кошелёк с вложенным владельцем и списком операций."""

    id: int
    title: str
    currency: Currency = Currency.RUB
    balance: float = 0.0
    owner: Owner                       # один вложенный объект
    operations: List[Operation] = []   # список вложенных объектов


class WalletCreate(BaseModel):
    """Тело запроса на создание кошелька (без id и операций)."""

    title: str
    currency: Currency = Currency.RUB
    balance: float = 0.0
    owner: Owner


# --- Временная «база данных» -------------------------------------------------
wallets: List[Wallet] = [
    Wallet(
        id=1,
        title="Основной",
        currency=Currency.RUB,
        balance=15000,
        owner=Owner(name="Анастасия", email="nastya@example.com"),
        operations=[
            Operation(id=1, amount=5000, type=OperationType.income, comment="Стипендия"),
            Operation(id=2, amount=800, type=OperationType.expense, comment="Кофе"),
        ],
    ),
    Wallet(
        id=2,
        title="Накопления",
        currency=Currency.USD,
        balance=300,
        owner=Owner(name="Анастасия", email="nastya@example.com"),
        operations=[],
    ),
]


def find_wallet(wallet_id: int) -> Wallet:
    for wallet in wallets:
        if wallet.id == wallet_id:
            return wallet
    raise HTTPException(status_code=404, detail="Кошелёк не найден")


# --- CRUD основной сущности (кошельки) --------------------------------------
@app.get("/wallets", response_model=List[Wallet])
def list_wallets() -> List[Wallet]:
    return wallets


@app.get("/wallets/{wallet_id}", response_model=Wallet)
def get_wallet(wallet_id: int) -> Wallet:
    return find_wallet(wallet_id)


@app.post("/wallets", response_model=Wallet, status_code=201)
def create_wallet(data: WalletCreate) -> Wallet:
    new_id = max((w.id for w in wallets), default=0) + 1
    wallet = Wallet(id=new_id, **data.model_dump())
    wallets.append(wallet)
    return wallet


@app.put("/wallets/{wallet_id}", response_model=Wallet)
def update_wallet(wallet_id: int, data: WalletCreate) -> Wallet:
    wallet = find_wallet(wallet_id)
    wallet.title = data.title
    wallet.currency = data.currency
    wallet.balance = data.balance
    wallet.owner = data.owner
    return wallet


@app.delete("/wallets/{wallet_id}", status_code=204)
def delete_wallet(wallet_id: int) -> None:
    wallet = find_wallet(wallet_id)
    wallets.remove(wallet)


# --- API для вложенной сущности (операции внутри кошелька) -------------------
@app.get("/wallets/{wallet_id}/operations", response_model=List[Operation])
def list_operations(wallet_id: int) -> List[Operation]:
    return find_wallet(wallet_id).operations


@app.post("/wallets/{wallet_id}/operations", response_model=Wallet, status_code=201)
def add_operation(wallet_id: int, amount: float, type: OperationType, comment: Optional[str] = None) -> Wallet:
    """Добавить операцию в кошелёк и пересчитать баланс."""
    wallet = find_wallet(wallet_id)
    new_id = max((o.id for o in wallet.operations), default=0) + 1
    operation = Operation(id=new_id, amount=amount, type=type, comment=comment)
    wallet.operations.append(operation)
    wallet.balance += amount if type == OperationType.income else -amount
    return wallet
