"""Схемы пользователя для регистрации, чтения и смены пароля."""
from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel

from app.models.user import UserBase


class UserCreate(UserBase):
    """Данные для регистрации нового пользователя."""

    email: EmailStr
    password: str


class UserRead(UserBase):
    """Публичное представление пользователя (без пароля)."""

    id: int
    is_active: bool
    created_at: datetime


class UserUpdate(SQLModel):
    """Частичное обновление профиля."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class PasswordChange(SQLModel):
    """Смена пароля: нужно подтвердить старый пароль."""

    old_password: str
    new_password: str
