from sqlmodel import select
from app.core.constants.category import DefaultCategory, CATEGORY_DATA
from app.core.db import AsyncSession
from app.models.category import Category

async def seed_default_categories(session: AsyncSession):
    print("🌱 Початок ініціалізації дефолтних категорій...")
    
    result = await session.execute(select(Category.name).where(Category.user_id == None))
    existing_names = set(result.scalars().all())

    categories_to_add = []
    for cat_enum in DefaultCategory:
        data = CATEGORY_DATA[cat_enum]
        
        if data["name"] not in existing_names:
            new_cat = Category(
                name=data["name"],
                icon=data["icon"],
                group=data["group"],
                user_id=None 
            )
            categories_to_add.append(new_cat)

    if categories_to_add:
        session.add_all(categories_to_add)
        await session.commit()
        print(f"✅ Додано нових категорій: {len(categories_to_add)}")
    else:
        print("ℹ️ Всі системні категорії вже існують.")