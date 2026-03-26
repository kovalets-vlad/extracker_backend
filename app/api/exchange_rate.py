from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from datetime import datetime, timezone, timedelta
from app.core.db import AsyncSession, get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.exchange_rate import ExchangeRate

router = APIRouter(prefix="/exchange_rate", tags=["exchange_rate"])

@router.get("/currency_exchange")
async def currency_exchange(
    from_currency: str,
    to_currency: str,
    amount: Decimal,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(ExchangeRate).where(ExchangeRate.code.in_([from_currency.upper(), to_currency.upper()]))
    result = await session.execute(stmt)
    rates = {r.code: r for r in result.scalars().all()}

    from_rate = rates.get(from_currency.upper())
    to_rate = rates.get(to_currency.upper())

    if not from_rate or not to_rate:
        raise HTTPException(status_code=400, detail="Одну з валют не знайдено в системі")

    message = f""
    if to_rate.updated_at < datetime.now(timezone.utc) - timedelta(days=1):
        message = "⚠️ Курси застаріли, рекомендується вводити суму конвертації вручну."
    else:
        message = "✅ Курси актуальні."

    converted_amount = amount * (to_rate.rate_to_usd / from_rate.rate_to_usd)
    return {"converted_amount": converted_amount, "rate": to_rate.rate_to_usd / from_rate.rate_to_usd, "message": message, "last_updated": to_rate.updated_at}