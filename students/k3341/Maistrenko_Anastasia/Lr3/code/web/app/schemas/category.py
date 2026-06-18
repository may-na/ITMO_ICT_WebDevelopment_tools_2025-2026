"""Схемы категории."""
from typing import Optional

from sqlmodel import SQLModel

from app.models.category import CategoryBase, CategoryType


class CategoryCreate(CategoryBase):
    """Создание категории."""


class CategoryUpdate(SQLModel):
    """Частичное обновление категории."""

    name: Optional[str] = None
    type: Optional[CategoryType] = None
    icon: Optional[str] = None


class CategoryRead(CategoryBase):
    id: int
    user_id: int
