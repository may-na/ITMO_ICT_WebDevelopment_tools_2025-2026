"""Модель счёта (кошелька)."""
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User


class AccountType(str, Enum):
    """Тип счёта."""

    cash = "cash"          # наличные
    card = "card"          # банковская карта
    deposit = "deposit"    # вклад
    savings = "savings"    # накопительный счёт


class AccountBase(SQLModel):
    name: str = Field(max_length=100)
    type: AccountType = Field(default=AccountType.card)
    currency: str = Field(default="RUB", max_length=3)
    balance: float = Field(default=0.0)


class Account(AccountBase, table=True):
    """Счёт принадлежит одному пользователю и содержит много транзакций."""

    __tablename__ = "account"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    owner: Optional["User"] = Relationship(back_populates="accounts")
    transactions: List["Transaction"] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
