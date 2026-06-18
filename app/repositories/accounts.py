from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.account import Account


async def get_account_for_user(
    session: AsyncSession,
    account_id: int,
    user_id: int,
    *,
    lock: bool = False,
) -> Account | None:
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id)
    if lock:
        stmt = stmt.with_for_update()

    result = await session.execute(stmt)
    return result.scalars().first()


async def get_accounts_for_user(
    session: AsyncSession,
    account_ids: Sequence[int],
    user_id: int,
    *,
    lock: bool = False,
) -> list[Account]:
    stmt = (
        select(Account)
        .where(Account.id.in_(account_ids), Account.user_id == user_id)
        .order_by(Account.id)
    )
    if lock:
        stmt = stmt.with_for_update()

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_accounts_for_user(session: AsyncSession, user_id: int) -> list[Account]:
    stmt = (
        select(Account)
        .where(Account.user_id == user_id)
        .options(joinedload(Account.currency))
        .order_by(Account.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
