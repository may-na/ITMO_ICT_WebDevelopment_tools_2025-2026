# Практика 2. База данных, SQLModel и связи

**Цель:** перейти от временного хранилища к настоящей БД (PostgreSQL),
описать таблицы через ORM **SQLModel**, реализовать связи и возврат вложенных
объектов.

Результаты практики вошли в основное приложение (`code/`).

## Подключение к PostgreSQL

Создаётся «движок» SQLAlchemy и зависимость-сессия (`code/app/core/database.py`):

```python
from sqlmodel import Session, SQLModel, create_engine
from app.core.config import settings

engine = create_engine(settings.database_url, echo=settings.db_echo)

def get_session():
    with Session(engine) as session:
        yield session
```

Сессия внедряется в обработчики через `Depends(get_session)`.

## Модели и связи

Базовый класс без таблицы (`...Base`) описывает поля, табличный класс
(`table=True`) добавляет первичный ключ и связи. Пример с тремя видами связей:

```python
class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")          # 1:M
    account_id: int = Field(foreign_key="account.id")    # 1:M
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")

    account: Optional["Account"] = Relationship(back_populates="transactions")
    category: Optional["Category"] = Relationship(back_populates="transactions")
    tags: List["Tag"] = Relationship(                     # M:M
        back_populates="transactions", link_model=TransactionTagLink
    )
```

Связь **многие-ко-многим** объявляется через `link_model` и связующую таблицу:

```python
class TransactionTagLink(SQLModel, table=True):
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)
```

Полное описание всех моделей — на странице [Модели и сущности](models.md).

## Возврат вложенных объектов

Чтобы в ответе API связанные объекты приходили «вложенными», заведены отдельные
схемы ответа (`code/app/schemas/nested.py`):

```python
class TransactionReadDetailed(TransactionRead):
    account: Optional[AccountRead] = None
    category: Optional[CategoryRead] = None
    tags: List[TagRead] = []
```

В обработчике достаточно указать `response_model=TransactionReadDetailed` —
FastAPI сам сериализует связанные ORM-объекты во вложенные структуры:

```python
@router.get("/{transaction_id}", response_model=TransactionReadDetailed)
def get_transaction(transaction_id: int, ...) -> Transaction:
    return get_owned_transaction(transaction_id, session, current_user)
```

Пример ответа — см. [Эндпоинты API](endpoints.md).

## Задание практики

> Установить подключение к БД, описать модели по своей предметной области,
> реализовать связь многие-ко-многим с вложенным представлением в ответе.

Выполнено: подключение к PostgreSQL, 8 таблиц SQLModel, связи 1:M и M:M,
вложенные ответы.
