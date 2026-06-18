# Практика 1. Основы FastAPI

**Цель:** познакомиться с FastAPI, научиться описывать модели на Pydantic и
строить CRUD-эндпоинты на временной (in-memory) базе данных.

Код практики: `practice/practice_1_inmemory/main.py`.

## Что реализовано

В качестве основной сущности взят **кошелёк** (`Wallet`). У него есть:

- **вложенный объект** `owner` (владелец);
- **список вложенных объектов** `operations` (операции по кошельку).

Для значений с ограниченным набором используются перечисления `Enum`
(`Currency`, `OperationType`). «Базой данных» служит обычный список Python.

### Модели

```python
class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class Owner(BaseModel):            # вложенный объект
    name: str
    email: str


class Operation(BaseModel):        # элемент списка вложенных объектов
    id: int
    amount: float = Field(gt=0)
    type: OperationType
    comment: Optional[str] = None
    op_date: date = Field(default_factory=date.today)


class Wallet(BaseModel):
    id: int
    title: str
    currency: Currency = Currency.RUB
    balance: float = 0.0
    owner: Owner                       # один вложенный объект
    operations: List[Operation] = []   # список вложенных объектов
```

### Эндпоинты

CRUD основной сущности и отдельный API для вложенной сущности (операции):

```python
@app.get("/wallets", response_model=List[Wallet])
def list_wallets() -> List[Wallet]:
    return wallets


@app.post("/wallets/{wallet_id}/operations", response_model=Wallet, status_code=201)
def add_operation(wallet_id: int, amount: float, type: OperationType,
                  comment: Optional[str] = None) -> Wallet:
    wallet = find_wallet(wallet_id)
    new_id = max((o.id for o in wallet.operations), default=0) + 1
    operation = Operation(id=new_id, amount=amount, type=type, comment=comment)
    wallet.operations.append(operation)
    wallet.balance += amount if type == OperationType.income else -amount
    return wallet
```

| Метод  | Путь                          | Назначение                          |
|--------|-------------------------------|-------------------------------------|
| GET    | `/wallets`                    | список кошельков                    |
| GET    | `/wallets/{id}`               | кошелёк с владельцем и операциями   |
| POST   | `/wallets`                    | создать кошелёк                     |
| PUT    | `/wallets/{id}`               | обновить кошелёк                    |
| DELETE | `/wallets/{id}`               | удалить кошелёк                     |
| GET    | `/wallets/{id}/operations`    | операции кошелька (вложенная сущн.) |
| POST   | `/wallets/{id}/operations`    | добавить операцию                   |

## Задание практики

> Реализовать временную базу данных для основной таблицы (2–3 записи) с одним
> вложенным объектом и списком объектов; разработать модели и API для вложенного
> объекта.

Выполнено: основная таблица `wallets` содержит 2 записи, вложенный объект
`owner`, список объектов `operations`; для операций реализован отдельный API.

## Запуск

```bash
cd practice/practice_1_inmemory
uvicorn main:app --reload
# Swagger UI: http://127.0.0.1:8000/docs
```
