from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exchange_rate import ExchangeRate


async def get_exchange_rates(
    session: AsyncSession,
    currency_codes: set[str] | None = None,
) -> dict[str, ExchangeRate]:
    stmt = select(ExchangeRate)
    if currency_codes:
        stmt = stmt.where(ExchangeRate.code.in_(currency_codes))

    result = await session.execute(stmt)
    return {rate.code: rate for rate in result.scalars().all()}
