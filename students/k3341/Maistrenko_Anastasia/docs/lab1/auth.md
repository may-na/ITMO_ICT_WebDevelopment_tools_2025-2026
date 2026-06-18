# Аутентификация (JWT)

Дополнительное задание (15 баллов). Регистрация и авторизация реализованы
вручную; сторонние библиотеки используются только для хеширования пароля
(bcrypt) и генерации JWT (python-jose).

## Хеширование и токены (`app/core/security.py`)

```python
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | int, expires_delta=None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(
        minutes=settings.access_token_expire_minutes))
    return jwt.encode({"sub": str(subject), "exp": expire},
                      settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
```

## Проверка токена (`app/api/deps.py`)

Зависимость `get_current_user` извлекает токен из заголовка `Authorization:
Bearer ...`, проверяет подпись и срок действия, находит пользователя в БД.
Если что-то не так — `401 Unauthorized`.

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme),
                     session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=401, detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"})
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user = session.get(User, int(payload.get("sub")))
    if user is None or not user.is_active:
        raise credentials_exception
    return user
```

Любой защищённый маршрут добавляет `current_user: User = Depends(get_current_user)`,
и все данные фильтруются по `current_user.id`.

## Эндпоинты аутентификации

| Метод | Путь                 | Назначение                              | Токен |
|-------|----------------------|-----------------------------------------|:-----:|
| POST  | `/auth/register`     | регистрация (пароль → bcrypt-хеш)       |  нет  |
| POST  | `/auth/token`        | вход, выдача JWT                        |  нет  |
| GET   | `/auth/me`           | информация о текущем пользователе       |  да   |
| GET   | `/auth/users`        | список всех пользователей               |  да   |
| PATCH | `/auth/me/password`  | смена пароля (с проверкой старого)      |  да   |

## Сценарий

1. **Регистрация** — `POST /auth/register`:

   ```json
   {"username": "anastasia", "email": "a@ex.com", "password": "secret123"}
   ```

2. **Вход** — `POST /auth/token` (form-data `username`/`password`) → токен:

   ```json
   {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
   ```

3. **Запрос с токеном** — заголовок `Authorization: Bearer <access_token>`.
   Без него защищённые эндпоинты отвечают `401`.

4. **Смена пароля** — `PATCH /auth/me/password`:

   ```json
   {"old_password": "secret123", "new_password": "newsecret456"}
   ```
