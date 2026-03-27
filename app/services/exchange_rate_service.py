import httpx
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exchange_rate import ExchangeRate
from app.core.constants.currency import CurrencyCode
from app.core.config import settings

MAIN_CURRENCY = "USD"

async def sync_exchange_rates(session: AsyncSession):
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

            allowed_codes = [c.value for c in CurrencyCode]

            for code, rate in rates.items():
                if code in allowed_codes:
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