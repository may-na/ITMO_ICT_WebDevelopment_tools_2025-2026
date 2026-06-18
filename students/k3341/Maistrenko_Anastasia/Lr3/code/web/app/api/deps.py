"""Общие зависимости (Dependencies) для обработчиков FastAPI.

Главная зависимость — get_current_user: извлекает JWT из заголовка
Authorization, проверяет его и возвращает текущего пользователя. Так
реализуется аутентификация по токену.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User

# tokenUrl указывает Swagger UI, куда отправлять логин/пароль для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Вернуть пользователя по предъявленному JWT либо отдать 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    subject = payload.get("sub")
    if subject is None:
        raise credentials_exception

    user = session.get(User, int(subject))
    if user is None or not user.is_active:
        raise credentials_exception
    return user
