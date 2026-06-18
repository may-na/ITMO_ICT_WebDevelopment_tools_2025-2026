"""Модель пользователя."""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:  # только для подсказок типов, чтобы избежать циклических импортов
    from app.models.account import Account
    from app.models.budget import Budget
    from app.models.category import Category
    from app.models.tag import Tag
    from app.models.transaction import Transaction


class UserBase(SQLModel):
    """Общие поля пользователя (без секретов и идентификатора)."""

    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)


class User(UserBase, table=True):
    """Пользователь системы. Владеет счетами, категориями, бюджетами и т.д."""

    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Связи один-ко-многим: у пользователя много счетов/категорий/...
    accounts: List["Account"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    categories: List["Category"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    transactions: List["Transaction"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    budgets: List["Budget"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    tags: List["Tag"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
