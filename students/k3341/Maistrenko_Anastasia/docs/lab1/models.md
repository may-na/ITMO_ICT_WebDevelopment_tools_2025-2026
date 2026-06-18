# Модели и сущности

Все модели описаны через ORM **SQLModel** в пакете `code/app/models/`.
Для каждой предметной сущности применён приём «базовый класс без таблицы
(`...Base`) → табличный класс (`table=True`)»: в базовом классе хранятся общие
поля, в табличном добавляются первичный ключ и связи. Базовые классы затем
переиспользуются в схемах запросов/ответов.

## Перечень таблиц

| Таблица                 | Назначение                              | Связи |
|-------------------------|-----------------------------------------|-------|
| `user`                  | пользователь (аутентификация)           | 1:M со всеми сущностями ниже |
| `account`               | счёт/кошелёк                            | 1:M → `transaction` |
| `category`              | категория дохода/расхода                | 1:M → `transaction`; M:M ↔ `budget` |
| `transaction`           | финансовая операция                     | M:1 → `account`, `category`; M:M ↔ `tag` |
| `budget`                | бюджет (план расходов)                  | M:M ↔ `category` |
| `tag`                   | метка для транзакций                    | M:M ↔ `transaction` |
| `transaction_tag_link`  | связь транзакция↔тег                    | ассоциативная (M:M) |
| `budget_category_link`  | связь бюджет↔категория + `planned_limit`| **ассоциативная с полем связи** |

## Пользователь (`user`)

```python
class UserBase(SQLModel):
    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)


class User(UserBase, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    accounts: List["Account"] = Relationship(back_populates="owner", ...)
    categories: List["Category"] = Relationship(back_populates="owner", ...)
    transactions: List["Transaction"] = Relationship(back_populates="owner", ...)
    budgets: List["Budget"] = Relationship(back_populates="owner", ...)
    tags: List["Tag"] = Relationship(back_populates="owner", ...)
```

Пароль в открытом виде не хранится — только bcrypt-хеш (`hashed_password`).

## Счёт (`account`) — связь 1:M с транзакциями

```python
class AccountType(str, Enum):
    cash = "cash"; card = "card"; deposit = "deposit"; savings = "savings"


class Account(AccountBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    owner: Optional["User"] = Relationship(back_populates="accounts")
    transactions: List["Transaction"] = Relationship(
        back_populates="account", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

## Категория (`category`) — 1:M и M:M

```python
class Category(CategoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    owner: Optional["User"] = Relationship(back_populates="categories")
    transactions: List["Transaction"] = Relationship(back_populates="category")
    budgets: List["Budget"] = Relationship(
        back_populates="categories", link_model=BudgetCategoryLink
    )
```

## Транзакция (`transaction`) — центр модели

```python
class TransactionType(str, Enum):
    income = "income"; expense = "expense"; transfer = "transfer"


class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)

    owner: Optional["User"] = Relationship(back_populates="transactions")
    account: Optional["Account"] = Relationship(back_populates="transactions")
    category: Optional["Category"] = Relationship(back_populates="transactions")
    tags: List["Tag"] = Relationship(back_populates="transactions", link_model=TransactionTagLink)
```

## Бюджет (`budget`) и тег (`tag`)

```python
class Budget(BudgetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    owner: Optional["User"] = Relationship(back_populates="budgets")
    categories: List["Category"] = Relationship(
        back_populates="budgets", link_model=BudgetCategoryLink
    )


class Tag(TagBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    owner: Optional["User"] = Relationship(back_populates="tags")
    transactions: List["Transaction"] = Relationship(
        back_populates="tags", link_model=TransactionTagLink
    )
```

## Ассоциативные сущности

Обе таблицы-связки реализуют **многие-ко-многим**. Ключевая по условию ЛР —
`BudgetCategoryLink`: помимо двух внешних ключей у неё есть **собственное поле
`planned_limit`**, которое характеризует связь (сколько средств бюджета
запланировано на конкретную категорию).

```python
class TransactionTagLink(SQLModel, table=True):
    __tablename__ = "transaction_tag_link"
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class BudgetCategoryLink(SQLModel, table=True):
    __tablename__ = "budget_category_link"
    budget_id: Optional[int] = Field(default=None, foreign_key="budget.id", primary_key=True)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", primary_key=True)
    planned_limit: float = Field(default=0.0)   # поле, характеризующее связь
```

Работа с этим полем вынесена в отдельные эндпоинты бюджета
(`POST/PATCH/DELETE /budgets/{id}/categories`), а в детальном ответе бюджета
лимиты приходят вложенным списком — см. [Эндпоинты API](endpoints.md).
