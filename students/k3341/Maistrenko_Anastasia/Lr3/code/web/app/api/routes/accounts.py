"""CRUD-маршруты для счетов."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.schemas.nested import AccountReadDetailed

router = APIRouter(prefix="/accounts", tags=["Счета"])


def get_owned_account(account_id: int, session: Session, user: User) -> Account:
    """Получить счёт и убедиться, что он принадлежит текущему пользователю."""
    account = session.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Счёт не найден")
    return account


@router.get("", response_model=List[AccountRead])
def list_accounts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Account]:
    """Список счетов текущего пользователя."""
    return session.exec(select(Account).where(Account.user_id == current_user.id)).all()


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    """Создать новый счёт."""
    account = Account(**data.model_dump(), user_id=current_user.id)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountReadDetailed)
def get_account(
    account_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    """Получить счёт вместе со списком его транзакций (вложенно)."""
    return get_owned_account(account_id, session, current_user)


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    data: AccountUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    """Частично обновить счёт."""
    account = get_owned_account(account_id, session, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Удалить счёт вместе с его транзакциями (каскадно)."""
    account = get_owned_account(account_id, session, current_user)
    session.delete(account)
    session.commit()
