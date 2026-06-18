"""Пакет моделей.

Импортируем все модели в одном месте, чтобы:
  - метаданные SQLModel «знали» обо всех таблицах (нужно для Alembic и
    create_all);
  - разрешались строковые ссылки в Relationship(back_populates=...).
"""
from app.models.account import Account, AccountBase, AccountType
from app.models.budget import Budget, BudgetBase, BudgetPeriod
from app.models.category import Category, CategoryBase, CategoryType
from app.models.links import BudgetCategoryLink, TransactionTagLink
from app.models.tag import Tag, TagBase
from app.models.transaction import Transaction, TransactionBase, TransactionType
from app.models.user import User, UserBase

__all__ = [
    "User",
    "UserBase",
    "Account",
    "AccountBase",
    "AccountType",
    "Category",
    "CategoryBase",
    "CategoryType",
    "Transaction",
    "TransactionBase",
    "TransactionType",
    "Budget",
    "BudgetBase",
    "BudgetPeriod",
    "Tag",
    "TagBase",
    "TransactionTagLink",
    "BudgetCategoryLink",
]
