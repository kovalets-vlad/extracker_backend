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
    stmt = select(Category).where(
        (Category.name == data.name) & 
        (Category.user_id == current_user.id)
    )
    existing_category = await session.execute(stmt)
    if existing_category.scalars().first():
        raise HTTPException(status_code=400, detail="Категорія з такою назвою вже існує")


    new_category = Category(name=data.name, user_id=current_user.id)
    session.add(new_category)
    
    await session.flush()   

    if data.limit is not None:
        new_category_limit = UserCategory(
            user_id=current_user.id, 
            category_id=new_category.id, 
            monthly_limit=data.limit
        )
        session.add(new_category_limit)

    await session.commit()
    await session.refresh(new_category)
    
    return {"status": "success", "category": new_category}

@router.patch("/{category_id}", status_code=status.HTTP_200_OK)
async def update_category_all_in_one(
    category_id: int,
    data: CategoryUpdate, 
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):

    category = await session.get(Category, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Категорія не знайдена")

    if data.name is not None:
        category.name = data.name
        session.add(category)

    if data.limit is not None:
        stmt = select(UserCategory).where(
            (UserCategory.category_id == category_id) & 
            (UserCategory.user_id == current_user.id)
        )
        res = await session.execute(stmt)
        user_category_record = res.scalars().first()

        if not user_category_record:
            user_category_record = UserCategory(
                user_id=current_user.id, 
                category_id=category_id, 
                monthly_limit=data.limit
            )
        else:
            user_category_record.monthly_limit = data.limit
        
        session.add(user_category_record)

    await session.commit()
    await session.refresh(category)
    
    return {
        "status": "success", 
        "category_name": category.name,
        "limit": data.limit if data.limit is not None else "не змінено"
    }

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    category = await session.get(Category, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Категорія не знайдена")

    await session.delete(category)
    await session.commit()
    
    return {"status": "success", "message": "Категорія видалена"}
