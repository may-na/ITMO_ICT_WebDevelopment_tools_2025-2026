"""CRUD-маршруты для категорий доходов/расходов."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.nested import CategoryReadDetailed

router = APIRouter(prefix="/categories", tags=["Категории"])


def get_owned_category(category_id: int, session: Session, user: User) -> Category:
    category = session.get(Category, category_id)
    if category is None or category.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Категория не найдена")
    return category


@router.get("", response_model=List[CategoryRead])
def list_categories(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Category]:
    return session.exec(select(Category).where(Category.user_id == current_user.id)).all()


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = Category(**data.model_dump(), user_id=current_user.id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryReadDetailed)
def get_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Category:
    """Категория вместе с её транзакциями (вложенно)."""
    return get_owned_category(category_id, session, current_user)


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = get_owned_category(category_id, session, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    category = get_owned_category(category_id, session, current_user)
    session.delete(category)
    session.commit()
