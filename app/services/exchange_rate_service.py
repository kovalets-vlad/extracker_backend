import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.config import settings
from app.core.constants.currency import CurrencyCode
from app.core.exceptions import ValidationError
from app.models.exchange_rate import ExchangeRate
from app.repositories.exchange_rates import get_exchange_rates

logger = logging.getLogger(__name__)

MAIN_CURRENCY = "USD"


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def sync_exchange_rates(session: AsyncSession) -> bool:
    api_url = f"{settings.EXCHANGE_RATE_API_URL}{MAIN_CURRENCY}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, timeout=10.0)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Exchange rate API request failed: %s", exc)
        return False

    data = response.json()
    if data.get("result") != "success":
        logger.warning("Exchange rate API returned non-success result")
        return False

    rates = data.get("conversion_rates", {})
    result = await session.execute(select(ExchangeRate))
    existing_rates = {rate.code: rate for rate in result.scalars().all()}
    allowed_codes = {code.value for code in CurrencyCode}
    now = datetime.now(timezone.utc)

    for code, rate in rates.items():
        if code not in allowed_codes:
            continue

        rate_dec = Decimal(str(rate))
        if code in existing_rates:
            existing_rates[code].rate_to_usd = rate_dec
            existing_rates[code].updated_at = now
        else:
            session.add(ExchangeRate(code=code, rate_to_usd=rate_dec, updated_at=now))

    await session.commit()
    logger.info("Exchange rates synchronized at %s", now.isoformat())
    return True


async def auto_update_exchange_rates(session: AsyncSession) -> None:
    result = await session.execute(select(func.max(ExchangeRate.updated_at)))
    last_update = result.scalar()
    stale_after = datetime.now(timezone.utc) - timedelta(days=1)

    if not last_update or _ensure_aware(last_update) < stale_after:
        logger.info("Exchange rates are stale; starting synchronization")
        await sync_exchange_rates(session)

    result = await session.execute(select(ExchangeRate.code))
    existing_codes = set(result.scalars().all())
    missing_codes = {rate.value for rate in CurrencyCode} - existing_codes
    if missing_codes:
        logger.info(
            "Exchange rates missing for %s; starting synchronization", sorted(missing_codes)
        )
        await sync_exchange_rates(session)


class ExchangeRateService:
    @staticmethod
    async def convert_currency(
        session: AsyncSession,
        from_currency: str,
        to_currency: str,
        amount: Decimal,
    ) -> dict[str, object]:
        from_code = from_currency.upper()
        to_code = to_currency.upper()
        rates = await get_exchange_rates(session, {from_code, to_code})

        from_rate = rates.get(from_code)
        to_rate = rates.get(to_code)
        if not from_rate or not to_rate:
            raise ValidationError("Одну з валют не знайдено в системі")

        stale_after = datetime.now(timezone.utc) - timedelta(days=1)
        updated_at = _ensure_aware(to_rate.updated_at)
        message = (
            "⚠️ Курси застарілі, рекомендується перевірити суму конвертації вручну."
            if updated_at < stale_after
            else "✅ Курси актуальні."
        )

        rate = to_rate.rate_to_usd / from_rate.rate_to_usd
        return {
            "converted_amount": amount * rate,
            "rate": rate,
            "message": message,
            "last_updated": to_rate.updated_at,
        }
