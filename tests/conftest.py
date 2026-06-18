from collections.abc import AsyncGenerator, Callable
from datetime import datetime, timezone
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app import models  # noqa: F401
from app.core.db import get_session
from app.main import create_app
from app.models.exchange_rate import ExchangeRate
from app.services.category_service import seed_default_categories
from app.services.currency_service import seed_currencies

SessionFactory = Callable[[], AsyncSession]


@pytest_asyncio.fixture
async def session_factory() -> AsyncGenerator[SessionFactory, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    testing_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with testing_session_factory() as session:
        await seed_currencies(session)
        await seed_default_categories(session)
        session.add_all(
            [
                ExchangeRate(
                    code="USD",
                    rate_to_usd=Decimal("1.0"),
                    updated_at=datetime.now(timezone.utc),
                ),
                ExchangeRate(
                    code="UAH",
                    rate_to_usd=Decimal("40.0"),
                    updated_at=datetime.now(timezone.utc),
                ),
                ExchangeRate(
                    code="EUR",
                    rate_to_usd=Decimal("0.9"),
                    updated_at=datetime.now(timezone.utc),
                ),
            ]
        )
        await session.commit()

    yield testing_session_factory

    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory: SessionFactory) -> AsyncGenerator[AsyncClient, None]:
    app = create_app(run_startup_tasks=False)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
