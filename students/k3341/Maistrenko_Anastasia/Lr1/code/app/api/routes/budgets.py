"""CRUD-маршруты для бюджетов и управления их связью с категориями.

Связь бюджет↔категория — многие-ко-многим через ассоциативную сущность
BudgetCategoryLink, у которой есть собственное поле planned_limit
(запланированный лимит расходов по категории внутри бюджета).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.budget import Budget
from app.models.category import Category
from app.models.links import BudgetCategoryLink
from app.models.user import User
from app.schemas.budget import (
    BudgetCategoryAdd,
    BudgetCategoryUpdate,
    BudgetCreate,
    BudgetRead,
    BudgetUpdate,
)
from app.schemas.nested import BudgetCategoryAllocation, BudgetReadDetailed

router = APIRouter(prefix="/budgets", tags=["Бюджеты"])


def get_owned_budget(budget_id: int, session: Session, user: User) -> Budget:
    budget = session.get(Budget, budget_id)
    if budget is None or budget.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Бюджет не найден")
    return budget


def build_detailed(budget: Budget, session: Session) -> BudgetReadDetailed:
    """Собрать детальное представление бюджета с лимитами по категориям."""
    links = session.exec(
        select(BudgetCategoryLink).where(BudgetCategoryLink.budget_id == budget.id)
    ).all()
    allocations: List[BudgetCategoryAllocation] = []
    for link in links:
        category = session.get(Category, link.category_id)
        if category is not None:
            allocations.append(
                BudgetCategoryAllocation(category=category, planned_limit=link.planned_limit)
            )
    return BudgetReadDetailed(**budget.model_dump(), allocations=allocations)


@router.get("", response_model=List[BudgetRead])
def list_budgets(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Budget]:
    return session.exec(select(Budget).where(Budget.user_id == current_user.id)).all()


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Budget:
    budget = Budget(**data.model_dump(), user_id=current_user.id)
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


@router.get("/{budget_id}", response_model=BudgetReadDetailed)
def get_budget(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BudgetReadDetailed:
    """Бюджет вместе с распределением по категориям (с лимитами)."""
    budget = get_owned_budget(budget_id, session, current_user)
    return build_detailed(budget, session)


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Budget:
    budget = get_owned_budget(budget_id, session, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(budget, field, value)
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    budget = get_owned_budget(budget_id, session, current_user)
    # Сначала удаляем связи с категориями, затем сам бюджет
    links = session.exec(
        select(BudgetCategoryLink).where(BudgetCategoryLink.budget_id == budget.id)
    ).all()
    for link in links:
        session.delete(link)
    session.delete(budget)
    session.commit()


@router.post("/{budget_id}/categories", response_model=BudgetReadDetailed,
             status_code=status.HTTP_201_CREATED)
def add_category_to_budget(
    budget_id: int,
    data: BudgetCategoryAdd,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BudgetReadDetailed:
    """Привязать категорию к бюджету с запланированным лимитом."""
    budget = get_owned_budget(budget_id, session, current_user)

    category = session.get(Category, data.category_id)
    if category is None or category.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Категория не найдена")

    existing = session.get(BudgetCategoryLink, (budget_id, data.category_id))
    if existing is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Категория уже привязана к этому бюджету"
        )

    link = BudgetCategoryLink(
        budget_id=budget_id,
        category_id=data.category_id,
        planned_limit=data.planned_limit,
    )
    session.add(link)
    session.commit()
    return build_detailed(budget, session)


@router.patch("/{budget_id}/categories/{category_id}", response_model=BudgetReadDetailed)
def update_budget_category(
    budget_id: int,
    category_id: int,
    data: BudgetCategoryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BudgetReadDetailed:
    """Изменить запланированный лимит у привязанной категории."""
    budget = get_owned_budget(budget_id, session, current_user)
    link = session.get(BudgetCategoryLink, (budget_id, category_id))
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Связь бюджет–категория не найдена")
    link.planned_limit = data.planned_limit
    session.add(link)
    session.commit()
    return build_detailed(budget, session)


@router.delete("/{budget_id}/categories/{category_id}", response_model=BudgetReadDetailed)
def remove_category_from_budget(
    budget_id: int,
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BudgetReadDetailed:
    """Отвязать категорию от бюджета."""
    budget = get_owned_budget(budget_id, session, current_user)
    link = session.get(BudgetCategoryLink, (budget_id, category_id))
    if link is not None:
        session.delete(link)
        session.commit()
    return build_detailed(budget, session)
