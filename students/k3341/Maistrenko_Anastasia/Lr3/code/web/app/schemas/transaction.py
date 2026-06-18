"""Схемы транзакции."""
from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel

from app.models.transaction import TransactionBase, TransactionType


class TransactionCreate(TransactionBase):
    """Создание транзакции.

    account_id обязателен, category_id и список тегов — опциональны.
    """

    account_id: int
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None


class TransactionUpdate(SQLModel):
    """Частичное обновление транзакции."""

    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None


class TransactionRead(TransactionBase):
    id: int
    user_id: int
    account_id: int
    category_id: Optional[int] = None
