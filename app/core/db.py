from decimal import Decimal
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import select, func
import httpx
from datetime import datetime, timezone, timedelta
from app.models.currency import CurrencyCode, Currency 
from app.models.category import DefaultCategory, Category, CATEGORY_DATA
from app.models.exchange_rate import ExchangeRate

from app.core.config import settings
from app import models 

MAIN_CURRENCY = "USD"

engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def seed_currencies(session: AsyncSession):
    result = await session.execute(select(Currency.code))
    existing_codes = set(result.scalars().all())

    to_create = []
    for code in CurrencyCode:
        if code not in existing_codes:
            new_currency = Currency.create_default(code)
            to_create.append(new_currency)
    if to_create:
        session.add_all(to_create) 
        await session.commit()
        print(f"✅ Додано нових валют: {len(to_create)}")
    else:
        print("ℹ️ Всі валюти вже є в базі.")

async def seed_categories(session: AsyncSession):
    result = await session.execute(select(Category).where(Category.user_id == None))
    db_categories = {c.name: c for c in result.scalars().all()} 

    to_create = []
    updated_count = 0

    for cat_enum in DefaultCategory:
        data = CATEGORY_DATA[cat_enum]
        name = data["name"]
        icon = data["icon"]

        if name not in db_categories:
            to_create.append(Category(name=name, icon=icon))
        else:
            category_in_db = db_categories[name]
            if category_in_db.icon != icon:
                category_in_db.icon = icon
                updated_count += 1

    if to_create:
        session.add_all(to_create)
    
    if to_create or updated_count > 0:
        await session.commit()
        print(f"✅ Додано: {len(to_create)}, Оновлено: {updated_count}")


async def sync_exchange_rates(session: AsyncSession):
    """Головна функція для оновлення курсів (використовується і для seed, і для auto)"""

    try:
        api_url = f"{settings.EXCHANGE_RATE_API_URL}{MAIN_CURRENCY}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url, timeout=10.0)
                response.raise_for_status()
            except httpx.HTTPError:
                print("❌ Помилка зв'язку з API курсів")
                return

            data = response.json()
            if data.get("result") != "success":
                return

            rates = data.get("conversion_rates", {})
            
            result = await session.execute(select(ExchangeRate))
            existing_rates = {r.code: r for r in result.scalars().all()}

            for code, rate in rates.items():
                if code in CurrencyCode: 
                    rate_dec = Decimal(str(rate))
                    
                    if code in existing_rates:
                        existing_rates[code].rate_to_usd = rate_dec
                        existing_rates[code].updated_at = datetime.now(timezone.utc)
                    else:
                        new_rate = ExchangeRate(
                            code=code, 
                            rate_to_usd=rate_dec,
                            updated_at=datetime.now(timezone.utc) 
                        )
                        session.add(new_rate)

            await session.commit()
            print(f"✅ Курси оновлені: {datetime.now(timezone.utc)}")

    except Exception as e:
        await session.rollback()
        print(f"❌ Критична помилка при синхронізації: {e}")
        return

async def auto_update_exchange_rates(session: AsyncSession):
    stmt = select(func.max(ExchangeRate.updated_at))
    result = await session.execute(stmt)
    last_update = result.scalar()

    if not last_update or last_update < datetime.now(timezone.utc) - timedelta(days=1):
        print("🔄 Курси застаріли, запускаю оновлення...")
        await sync_exchange_rates(session)

    stmt = select(ExchangeRate)
    result = await session.execute(stmt)
    rates = result.scalars().all()

    for rate in CurrencyCode:
        if rate.value not in [r.code for r in rates]:
            print(f"⚠️ Відсутній курс для {rate.value}, запускаю оновлення...")
            await sync_exchange_rates(session)
            break