"""Ассоциативные (связующие) таблицы для связей многие-ко-многим.

BudgetCategoryLink — пример ассоциативной сущности, которая помимо внешних
ключей содержит собственное поле ``planned_limit``, характеризующее связь:
сколько средств в рамках конкретного бюджета запланировано на конкретную
категорию.
"""
from typing import Optional

from sqlmodel import Field, SQLModel


class TransactionTagLink(SQLModel, table=True):
    """Связь многие-ко-многим между транзакциями и тегами."""

    __tablename__ = "transaction_tag_link"

    transaction_id: Optional[int] = Field(
        default=None, foreign_key="transaction.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tag.id", primary_key=True
    )


class BudgetCategoryLink(SQLModel, table=True):
    """Связь многие-ко-многим между бюджетами и категориями.

    Поле ``planned_limit`` характеризует связь — это запланированный лимит
    расходов по данной категории внутри данного бюджета.
    """

    __tablename__ = "budget_category_link"

    budget_id: Optional[int] = Field(
        default=None, foreign_key="budget.id", primary_key=True
    )
    category_id: Optional[int] = Field(
        default=None, foreign_key="category.id", primary_key=True
    )
    # Поле, характеризующее связь:
    planned_limit: float = Field(default=0.0)
