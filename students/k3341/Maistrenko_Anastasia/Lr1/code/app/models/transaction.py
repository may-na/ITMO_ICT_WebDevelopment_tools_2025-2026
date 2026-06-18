"""Модель финансовой операции (транзакции)."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.links import TransactionTagLink

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.category import Category
    from app.models.tag import Tag
    from app.models.user import User


class TransactionType(str, Enum):
    income = "income"        # доход
    expense = "expense"      # расход
    transfer = "transfer"    # перевод


class TransactionBase(SQLModel):
    amount: float = Field(gt=0, description="Сумма операции, должна быть > 0")
    type: TransactionType
    description: Optional[str] = Field(default=None, max_length=255)
    date: datetime = Field(default_factory=datetime.utcnow)


class Transaction(TransactionBase, table=True):
    """Операция привязана к счёту и (необязательно) к категории.

    Многие-ко-многим с тегами через TransactionTagLink.
    """

    __tablename__ = "transaction"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)

    owner: Optional["User"] = Relationship(back_populates="transactions")
    account: Optional["Account"] = Relationship(back_populates="transactions")
    category: Optional["Category"] = Relationship(back_populates="transactions")
    tags: List["Tag"] = Relationship(
        back_populates="transactions", link_model=TransactionTagLink
    )
