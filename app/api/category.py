from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryMutationResponse,
    CategoryUpdate,
    MessageResponse,
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryMutationResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    category, limit = await CategoryService.create_category(session, data, current_user)
    return {"status": "success", "category": category, "limit": limit}


@router.patch("/{category_id}", response_model=CategoryMutationResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    category, limit = await CategoryService.update_category(
        session,
        category_id,
        data,
        current_user,
    )
    return {"status": "success", "category": category, "limit": limit}


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await CategoryService.delete_category(session, category_id, current_user)
    return {"status": "success", "message": "Категорія видалена"}
