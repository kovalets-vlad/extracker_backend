from sqlmodel import select
from app.models.currency import Currency
from app.core.constants.currency import CurrencyCode, CURRENCY_DATA
from app.core.db import AsyncSession

async def seed_currencies(session: AsyncSession):
    print("🪙 Початок ініціалізації валют...")
    
    result = await session.execute(select(Currency.code))
    existing_codes = set(result.scalars().all())

    currencies_to_add = []
    for code in CurrencyCode:
        if code not in existing_codes:
            data = CURRENCY_DATA[code]
            new_currency = Currency(
                code=code,
                name=data["name"],
                symbol=data["symbol"]
            )
            currencies_to_add.append(new_currency)

    if currencies_to_add:
        session.add_all(currencies_to_add)
        await session.commit()
        print(f"✅ Додано нових валют: {len(currencies_to_add)}")
    else:
        print("ℹ️ Всі валюти вже існують.")