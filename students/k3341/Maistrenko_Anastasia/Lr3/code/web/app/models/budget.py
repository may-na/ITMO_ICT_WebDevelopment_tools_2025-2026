"""Модель бюджета (плана расходов)."""
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.links import BudgetCategoryLink

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class BudgetPeriod(str, Enum):
    week = "week"
    month = "month"
    year = "year"


class BudgetBase(SQLModel):
    name: str = Field(max_length=100)
    limit_amount: float = Field(gt=0, description="Общий лимит бюджета")
    period: BudgetPeriod = Field(default=BudgetPeriod.month)
    start_date: date = Field(default_factory=date.today)


class Budget(BudgetBase, table=True):
    """Бюджет принадлежит пользователю и охватывает набор категорий.

    Многие-ко-многим с категориями через ассоциативную таблицу
    BudgetCategoryLink, где хранится запланированный лимит по каждой категории.
    """

    __tablename__ = "budget"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    owner: Optional["User"] = Relationship(back_populates="budgets")
    categories: List["Category"] = Relationship(
        back_populates="budgets", link_model=BudgetCategoryLink
    )
