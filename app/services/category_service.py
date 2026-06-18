import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.constants.category import CATEGORY_DATA, DefaultCategory
from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.user import User
from app.models.user_category import UserCategory
from app.repositories.categories import (
    get_user_category,
    user_category_name_exists,
)
from app.schemas.category import CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)


async def seed_default_categories(session: AsyncSession) -> None:
    logger.info("Starting default category seed")

    result = await session.execute(select(Category.name).where(Category.user_id.is_(None)))
    existing_names = set(result.scalars().all())

    categories_to_add = []
    for cat_enum in DefaultCategory:
        data = CATEGORY_DATA[cat_enum]

        if data["name"] not in existing_names:
            categories_to_add.append(
                Category(
                    name=data["name"],
                    icon=data["icon"],
                    group=data["group"],
                    user_id=None,
                )
            )

    if categories_to_add:
        session.add_all(categories_to_add)
        await session.commit()
        logger.info("Added %s default categories", len(categories_to_add))
    else:
        logger.info("Default categories already seeded")


class CategoryService:
    @staticmethod
    async def create_category(
        session: AsyncSession,
        data: CategoryCreate,
        current_user: User,
    ) -> tuple[Category, object | None]:
        if await user_category_name_exists(session, data.name, current_user.id):
            raise ConflictError("Категорія з такою назвою вже існує")

        category = Category(name=data.name, user_id=current_user.id)
        session.add(category)
        await session.flush()

        limit = None
        if data.limit is not None:
            limit = UserCategory(
                user_id=current_user.id,
                category_id=category.id,
                monthly_limit=data.limit,
            )
            session.add(limit)

        await session.commit()
        await session.refresh(category)
        return category, data.limit if limit else None

    @staticmethod
    async def update_category(
        session: AsyncSession,
        category_id: int,
        data: CategoryUpdate,
        current_user: User,
    ) -> tuple[Category, object | None]:
        category = await get_user_category(session, category_id, current_user.id)
        if not category:
            raise NotFoundError("Категорія не знайдена")

        if data.name is not None:
            if await user_category_name_exists(
                session,
                data.name,
                current_user.id,
                exclude_category_id=category_id,
            ):
                raise ConflictError("Категорія з такою назвою вже існує")
            category.name = data.name
            session.add(category)

        if data.limit is not None:
            stmt = select(UserCategory).where(
                UserCategory.category_id == category_id,
                UserCategory.user_id == current_user.id,
            )
            res = await session.execute(stmt)
            user_category = res.scalars().first()

            if not user_category:
                user_category = UserCategory(
                    user_id=current_user.id,
                    category_id=category_id,
                    monthly_limit=data.limit,
                )
            else:
                user_category.monthly_limit = data.limit

            session.add(user_category)

        await session.commit()
        await session.refresh(category)
        return category, data.limit

    @staticmethod
    async def delete_category(
        session: AsyncSession,
        category_id: int,
        current_user: User,
    ) -> None:
        category = await get_user_category(session, category_id, current_user.id)
        if not category:
            raise NotFoundError("Категорія не знайдена")

        await session.delete(category)
        await session.commit()
