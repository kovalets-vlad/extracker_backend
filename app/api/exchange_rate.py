from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.exchange_rate import CurrencyExchangeResponse
from app.services.exchange_rate_service import ExchangeRateService

router = APIRouter(prefix="/exchange_rate", tags=["exchange_rate"])


@router.get("/currency_exchange", response_model=CurrencyExchangeResponse)
async def currency_exchange(
    from_currency: str = Query(min_length=3, max_length=3),
    to_currency: str = Query(min_length=3, max_length=3),
    amount: Decimal = Query(gt=Decimal("0")),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await ExchangeRateService.convert_currency(
        session,
        from_currency,
        to_currency,
        amount,
    )
