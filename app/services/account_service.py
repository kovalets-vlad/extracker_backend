from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.account import Account
from app.models.user import User
from app.repositories.accounts import get_account_for_user, list_accounts_for_user
from app.repositories.currencies import get_currency_by_id
from app.schemas.account import AccountCreate, AccountSetLimit


class AccountService:
    @staticmethod
    async def create_account(
        session: AsyncSession,
        data: AccountCreate,
        current_user: User,
    ) -> Account:
        currency = await get_currency_by_id(session, data.currency_id)
        if not currency:
            raise ValidationError("Невідома валюта")

        account = Account(
            name=data.name,
            balance=Decimal("0.00"),
            currency_id=data.currency_id,
            user_id=current_user.id,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    @staticmethod
    async def set_monthly_limit(
        session: AsyncSession,
        account_id: int,
        data: AccountSetLimit,
        current_user: User,
    ) -> Account:
        account = await get_account_for_user(session, account_id, current_user.id, lock=True)
        if not account:
            raise NotFoundError("Гаманець не знайдено")

        account.monthly_limit = data.monthly_limit
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    @staticmethod
    async def list_accounts(session: AsyncSession, current_user: User) -> list[Account]:
        return await list_accounts_for_user(session, current_user.id)
