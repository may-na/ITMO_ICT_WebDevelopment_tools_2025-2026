"""Схемы тега."""
from typing import Optional

from sqlmodel import SQLModel

from app.models.tag import TagBase


class TagCreate(TagBase):
    """Создание тега."""


class TagUpdate(SQLModel):
    """Частичное обновление тега."""

    name: Optional[str] = None
    color: Optional[str] = None


class TagRead(TagBase):
    id: int
    user_id: int
