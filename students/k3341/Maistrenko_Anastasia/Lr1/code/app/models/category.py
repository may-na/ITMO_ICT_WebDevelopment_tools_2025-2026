"""Модель категории доходов/расходов."""
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.links import BudgetCategoryLink

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.transaction import Transaction
    from app.models.user import User


class CategoryType(str, Enum):
    """Категория относится к доходам или к расходам."""

    income = "income"
    expense = "expense"


class CategoryBase(SQLModel):
    name: str = Field(max_length=100)
    type: CategoryType = Field(default=CategoryType.expense)
    icon: Optional[str] = Field(default=None, max_length=50)


class Category(CategoryBase, table=True):
    """Категория принадлежит пользователю.

    Связи:
      - один-ко-многим с транзакциями;
      - многие-ко-многим с бюджетами через ассоциативную таблицу
        BudgetCategoryLink (с полем planned_limit).
    """

    __tablename__ = "category"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    owner: Optional["User"] = Relationship(back_populates="categories")
    transactions: List["Transaction"] = Relationship(back_populates="category")
    budgets: List["Budget"] = Relationship(
        back_populates="categories", link_model=BudgetCategoryLink
    )
