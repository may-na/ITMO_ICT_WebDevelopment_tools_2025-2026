"""Схемы бюджета и привязки категорий к бюджету."""
from datetime import date
from typing import Optional

from sqlmodel import SQLModel

from app.models.budget import BudgetBase, BudgetPeriod


class BudgetCreate(BudgetBase):
    """Создание бюджета."""


class BudgetUpdate(SQLModel):
    """Частичное обновление бюджета."""

    name: Optional[str] = None
    limit_amount: Optional[float] = None
    period: Optional[BudgetPeriod] = None
    start_date: Optional[date] = None


class BudgetRead(BudgetBase):
    id: int
    user_id: int


class BudgetCategoryAdd(SQLModel):
    """Привязать категорию к бюджету с запланированным лимитом.

    Здесь planned_limit — то самое поле ассоциативной сущности
    BudgetCategoryLink, характеризующее связь.
    """

    category_id: int
    planned_limit: float = 0.0


class BudgetCategoryUpdate(SQLModel):
    """Изменить запланированный лимит у уже привязанной категории."""

    planned_limit: float
