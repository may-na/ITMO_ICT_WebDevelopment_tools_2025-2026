"""Модель тега (метки) для транзакций."""
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.links import TransactionTagLink

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User


class TagBase(SQLModel):
    name: str = Field(max_length=50)
    color: Optional[str] = Field(default=None, max_length=20)


class Tag(TagBase, table=True):
    """Тег принадлежит пользователю; связь многие-ко-многим с транзакциями."""

    __tablename__ = "tag"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    owner: Optional["User"] = Relationship(back_populates="tags")
    transactions: List["Transaction"] = Relationship(
        back_populates="tags", link_model=TransactionTagLink
    )
