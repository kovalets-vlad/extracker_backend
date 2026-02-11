from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import select
from app.models.currency import CurrencyCode, Currency 

from app.core.config import settings
from app import models 

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