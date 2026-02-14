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
    currency_exchange = await session.execute(
        select(ExchangeRate).where(ExchangeRate.code == from_currency.upper())
    )
    from_rate = currency_exchange.scalars().first()
    if not from_rate:
        raise HTTPException(status_code=400, detail="Невідома вихідна валюта")

    currency_exchange = await session.execute(
        select(ExchangeRate).where(ExchangeRate.code == to_currency.upper())
    )

    message = f""
    if currency_exchange.updated_at == datetime.now(timezone.utc) - timedelta(days=1):
        message = "⚠️ Курси застаріли, рекомендується оновити їх для точного конвертування."
    else:
        message = "✅ Курси актуальні."

    to_rate = currency_exchange.scalars().first()
    if not to_rate:
        raise HTTPException(status_code=400, detail="Невідома цільова валюта")

    converted_amount = amount * (to_rate.rate_to_usd / from_rate.rate_to_usd)
    return {"converted_amount": converted_amount, "rate": to_rate.rate_to_usd / from_rate.rate_to_usd, "message": message}