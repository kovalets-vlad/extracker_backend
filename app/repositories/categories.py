from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


async def get_accessible_category(
    session: AsyncSession,
    category_id: int,
    user_id: int,
) -> Category | None:
    stmt = select(Category).where(
        Category.id == category_id,
        (Category.user_id == user_id) | (Category.user_id.is_(None)),
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_user_category(
    session: AsyncSession,
    category_id: int,
    user_id: int,
) -> Category | None:
    stmt = select(Category).where(Category.id == category_id, Category.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_system_category_by_name(session: AsyncSession, name: str) -> Category | None:
    stmt = select(Category).where(Category.name == name, Category.user_id.is_(None))
    result = await session.execute(stmt)
    return result.scalars().first()


async def user_category_name_exists(
    session: AsyncSession,
    name: str,
    user_id: int,
    *,
    exclude_category_id: int | None = None,
) -> bool:
    stmt = select(Category.id).where(Category.name == name, Category.user_id == user_id)
    if exclude_category_id is not None:
        stmt = stmt.where(Category.id != exclude_category_id)

    result = await session.execute(stmt)
    return result.scalars().first() is not None
