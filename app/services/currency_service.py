import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.constants.currency import CURRENCY_DATA, CurrencyCode
from app.models.currency import Currency

logger = logging.getLogger(__name__)


async def seed_currencies(session: AsyncSession) -> None:
    logger.info("Starting currency seed")

    result = await session.execute(select(Currency.code))
    existing_codes = set(result.scalars().all())

    currencies_to_add = []
    for code in CurrencyCode:
        if code not in existing_codes:
            data = CURRENCY_DATA[code]
            currencies_to_add.append(
                Currency(
                    code=code,
                    name=data["name"],
                    symbol=data["symbol"],
                )
            )

    if currencies_to_add:
        session.add_all(currencies_to_add)
        await session.commit()
        logger.info("Added %s currencies", len(currencies_to_add))
    else:
        logger.info("Currencies already seeded")
