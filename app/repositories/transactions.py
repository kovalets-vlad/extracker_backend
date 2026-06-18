from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction


async def get_transaction_for_user(
    session: AsyncSession,
    transaction_id: int,
    user_id: int,
    *,
    lock: bool = False,
) -> Transaction | None:
    stmt = select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id,
    )
    if lock:
        stmt = stmt.with_for_update()

    result = await session.execute(stmt)
    return result.scalars().first()
