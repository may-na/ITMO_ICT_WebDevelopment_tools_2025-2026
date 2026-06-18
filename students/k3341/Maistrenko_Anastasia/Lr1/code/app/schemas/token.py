"""Схемы для JWT-токенов."""
from typing import Optional

from sqlmodel import SQLModel


class Token(SQLModel):
    """Ответ на успешную авторизацию."""

    access_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    """Полезная нагрузка, извлечённая из токена."""

    user_id: Optional[int] = None
