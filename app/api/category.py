from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from app.core.db import AsyncSession, get_session
from app.api.deps import get_current_user
from app.models.category import Category
from app.models.user_category import UserCategory
from app.schemas.category import CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    existing_category = await session.execute(select(Category).where((Category.name == data.name) & (Category.user_id == current_user.id)))
    if existing_category.scalars().first():
        raise HTTPException(status_code=400, detail="Категорія з такою назвою вже існує")

    new_category = Category(name=data.name, user_id=current_user.id)
    new_category_limit = UserCategory(user_id=current_user.id, category_id=new_category.id, monthly_limit=data.limit)
    session.add(new_category)
    session.add(new_category_limit)
    await session.commit()
    await session.refresh(new_category)
    
    return {"status": "success", "category": new_category}

@router.put("/{category_id}", status_code=status.HTTP_200_OK)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    category = await session.get(Category, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Категорія не знайдена")

    category.name = data.name
    user_category = await session.execute(select(UserCategory).where((UserCategory.category_id == category_id) & (UserCategory.user_id == current_user.id)))
    user_category_record = user_category.scalars().first()
    
    if user_category_record:
        user_category_record.monthly_limit = data.limit
        session.add(user_category_record)

    session.add(category)
    await session.commit()
    await session.refresh(category)
    
    return {"status": "success", "category": category}