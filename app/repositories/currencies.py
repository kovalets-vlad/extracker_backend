from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants.currency import CurrencyCode
from app.models.currency import Currency


async def get_currency_by_id(session: AsyncSession, currency_id: int) -> Currency | None:
    result = await session.execute(select(Currency).where(Currency.id == currency_id))
    return result.scalars().first()


async def get_currency_by_code(
    session: AsyncSession,
    currency_code: CurrencyCode,
) -> Currency | None:
    result = await session.execute(select(Currency).where(Currency.code == currency_code))
    return result.scalars().first()
