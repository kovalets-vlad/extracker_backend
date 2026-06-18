from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.recurring_transaction import RecurringTransaction
from app.models.user import User
from app.repositories.accounts import get_account_for_user
from app.repositories.categories import get_accessible_category
from app.schemas.recurring_transaction import RecurringTransactionCreate


class RecurringTransactionService:
    @staticmethod
    async def create_template(
        session: AsyncSession,
        data: RecurringTransactionCreate,
        current_user: User,
    ) -> RecurringTransaction:
        account = await get_account_for_user(session, data.account_id, current_user.id)
        if not account:
            raise NotFoundError("Гаманець не знайдено")

        category = await get_accessible_category(session, data.category_id, current_user.id)
        if not category:
            raise ValidationError("Категорія не знайдена")

        template = RecurringTransaction(**data.model_dump(), user_id=current_user.id)
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template
