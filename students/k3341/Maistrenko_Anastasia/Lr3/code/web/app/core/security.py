"""Безопасность: хеширование паролей и работа с JWT.

По условию ЛР логику регистрации/авторизации реализуем «вручную»,
разрешено использовать сторонние библиотеки только для хеширования пароля
(passlib + bcrypt) и для генерации JWT (python-jose).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Контекст хеширования паролей по алгоритму bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Вернуть bcrypt-хеш пароля для хранения в БД."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить, что открытый пароль соответствует сохранённому хешу."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | int, expires_delta: Optional[timedelta] = None) -> str:
    """Сгенерировать подписанный JWT access-токен.

    В поле ``sub`` кладём идентификатор пользователя, в ``exp`` — момент
    истечения срока действия.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Проверить подпись и срок действия токена, вернуть его полезную нагрузку.

    При неверной подписи или истёкшем сроке возвращает None.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
