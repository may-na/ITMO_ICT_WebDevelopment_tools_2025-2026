"""CRUD-маршруты для тегов."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagRead, TagUpdate

router = APIRouter(prefix="/tags", tags=["Теги"])


def get_owned_tag(tag_id: int, session: Session, user: User) -> Tag:
    tag = session.get(Tag, tag_id)
    if tag is None or tag.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Тег не найден")
    return tag


@router.get("", response_model=List[TagRead])
def list_tags(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Tag]:
    return session.exec(select(Tag).where(Tag.user_id == current_user.id)).all()


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    data: TagCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Tag:
    tag = Tag(**data.model_dump(), user_id=current_user.id)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: int,
    data: TagUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Tag:
    tag = get_owned_tag(tag_id, session, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    tag = get_owned_tag(tag_id, session, current_user)
    session.delete(tag)
    session.commit()
