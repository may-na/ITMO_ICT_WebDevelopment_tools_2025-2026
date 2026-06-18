"""Схемы счёта."""
from typing import Optional

from sqlmodel import SQLModel

from app.models.account import AccountBase, AccountType


class AccountCreate(AccountBase):
    """Создание счёта (user_id берётся из текущего пользователя)."""


class AccountUpdate(SQLModel):
    """Частичное обновление счёта."""

    name: Optional[str] = None
    type: Optional[AccountType] = None
    currency: Optional[str] = None
    balance: Optional[float] = None


class AccountRead(AccountBase):
    id: int
    user_id: int
