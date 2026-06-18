"""Вложенные (детализированные) схемы ответов.

Эти модели возвращают связанные объекты «вложенными» в основной ответ —
требование ЛР про CRUD с возвращением вложенных объектов для связей.
Вынесены в отдельный модуль, чтобы избежать циклических импортов между
доменными схемами.
"""
from typing import List, Optional

from sqlmodel import SQLModel

from app.schemas.account import AccountRead
from app.schemas.budget import BudgetRead
from app.schemas.category import CategoryRead
from app.schemas.tag import TagRead
from app.schemas.transaction import TransactionRead


class TransactionReadDetailed(TransactionRead):
    """Транзакция вместе со счётом, категорией и тегами."""

    account: Optional[AccountRead] = None
    category: Optional[CategoryRead] = None
    tags: List[TagRead] = []


class AccountReadDetailed(AccountRead):
    """Счёт вместе со списком его транзакций."""

    transactions: List[TransactionRead] = []


class CategoryReadDetailed(CategoryRead):
    """Категория вместе со списком её транзакций."""

    transactions: List[TransactionRead] = []


class BudgetCategoryAllocation(SQLModel):
    """Строка распределения бюджета: категория + запланированный лимит.

    planned_limit берётся из ассоциативной таблицы BudgetCategoryLink.
    """

    category: CategoryRead
    planned_limit: float


class BudgetReadDetailed(BudgetRead):
    """Бюджет вместе с распределением по категориям (с лимитами)."""

    allocations: List[BudgetCategoryAllocation] = []
