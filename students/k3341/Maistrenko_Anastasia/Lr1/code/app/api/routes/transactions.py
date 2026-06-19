"""CRUD-маршруты для транзакций.

Дополнительно: при создании/изменении/удалении транзакции пересчитывается
баланс соответствующего счёта, а также поддерживается связь многие-ко-многим
с тегами.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.account import Account
from app.models.category import Category
from app.models.tag import Tag
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.nested import TransactionReadDetailed
from app.schemas.transaction import TransactionCreate, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["Транзакции"])


def signed_amount(t_type: TransactionType, amount: float) -> float:
    """Знаковое влияние операции на баланс счёта.

    Доход увеличивает баланс, расход и перевод — уменьшают.
    """
    return amount if t_type == TransactionType.income else -amount


def get_owned_transaction(transaction_id: int, session: Session, user: User) -> Transaction:
    transaction = session.get(Transaction, transaction_id)
    if transaction is None or transaction.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Транзакция не найдена")
    return transaction


def _validate_account(account_id: int, session: Session, user: User) -> Account:
    account = session.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Счёт не найден")
    return account


def _validate_category(category_id: int, session: Session, user: User) -> Category:
    category = session.get(Category, category_id)
    if category is None or category.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Категория не найдена")
    return category


def _check_sufficient_funds(account: Account, t_type: TransactionType, amount: float) -> None:
    """Проверить, что на счёте достаточно средств для расхода/перевода.

    Для дохода проверка не нужна. Если денег не хватает — отдаём 400.
    """
    if t_type in (TransactionType.expense, TransactionType.transfer) and amount > account.balance:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Недостаточно средств на счёте «{account.name}»: "
            f"баланс {account.balance}, требуется {amount}",
        )


@router.get("", response_model=List[TransactionReadDetailed])
def list_transactions(
    account_id: Optional[int] = Query(default=None, description="Фильтр по счёту"),
    category_id: Optional[int] = Query(default=None, description="Фильтр по категории"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Transaction]:
    """Список транзакций пользователя с необязательными фильтрами."""
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)
    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)
    return session.exec(query.order_by(Transaction.date.desc())).all()


@router.post("", response_model=TransactionReadDetailed, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    """Создать транзакцию, привязать теги и обновить баланс счёта."""
    account = _validate_account(data.account_id, session, current_user)
    if data.category_id is not None:
        _validate_category(data.category_id, session, current_user)

    # Базовая валидация: нельзя потратить больше, чем есть на счёте
    _check_sufficient_funds(account, data.type, data.amount)

    transaction = Transaction(
        amount=data.amount,
        type=data.type,
        description=data.description,
        date=data.date,
        account_id=data.account_id,
        category_id=data.category_id,
        user_id=current_user.id,
    )

    if data.tag_ids:
        tags = session.exec(
            select(Tag).where(Tag.id.in_(data.tag_ids), Tag.user_id == current_user.id)
        ).all()
        transaction.tags = list(tags)

    account.balance += signed_amount(transaction.type, transaction.amount)

    session.add(transaction)
    session.add(account)
    session.commit()
    session.refresh(transaction)
    return transaction


@router.get("/{transaction_id}", response_model=TransactionReadDetailed)
def get_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    """Транзакция со счётом, категорией и тегами (вложенно)."""
    return get_owned_transaction(transaction_id, session, current_user)


@router.patch("/{transaction_id}", response_model=TransactionReadDetailed)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    """Обновить транзакцию и корректно пересчитать баланс затронутых счетов."""
    transaction = get_owned_transaction(transaction_id, session, current_user)
    updates = data.model_dump(exclude_unset=True)

    # Проверяем права на новые счёт/категорию, если они меняются
    if "account_id" in updates and updates["account_id"] is not None:
        _validate_account(updates["account_id"], session, current_user)
    if "category_id" in updates and updates["category_id"] is not None:
        _validate_category(updates["category_id"], session, current_user)

    # Откатываем влияние старой версии транзакции на её счёт
    old_account = session.get(Account, transaction.account_id)
    if old_account is not None:
        old_account.balance -= signed_amount(transaction.type, transaction.amount)

    # Применяем изменения
    for field, value in updates.items():
        setattr(transaction, field, value)

    # Применяем влияние новой версии (счёт мог измениться)
    new_account = session.get(Account, transaction.account_id)
    if new_account is not None:
        new_account.balance += signed_amount(transaction.type, transaction.amount)
        # Базовая валидация: после изменения баланс не должен уйти в минус.
        # commit ещё не было — при ошибке сессия закроется без сохранения.
        if new_account.balance < 0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Недостаточно средств на счёте «{new_account.name}» "
                f"для изменённой операции (итоговый баланс был бы {new_account.balance})",
            )

    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Удалить транзакцию и вернуть её влияние на баланс счёта."""
    transaction = get_owned_transaction(transaction_id, session, current_user)
    account = session.get(Account, transaction.account_id)
    if account is not None:
        account.balance -= signed_amount(transaction.type, transaction.amount)
    session.delete(transaction)
    session.commit()


@router.post("/{transaction_id}/tags/{tag_id}", response_model=TransactionReadDetailed)
def attach_tag(
    transaction_id: int,
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    """Добавить тег к транзакции (связь многие-ко-многим)."""
    transaction = get_owned_transaction(transaction_id, session, current_user)
    tag = session.get(Tag, tag_id)
    if tag is None or tag.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Тег не найден")
    if tag not in transaction.tags:
        transaction.tags.append(tag)
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}/tags/{tag_id}", response_model=TransactionReadDetailed)
def detach_tag(
    transaction_id: int,
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    """Открепить тег от транзакции."""
    transaction = get_owned_transaction(transaction_id, session, current_user)
    tag = session.get(Tag, tag_id)
    if tag is not None and tag in transaction.tags:
        transaction.tags.remove(tag)
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
    return transaction
