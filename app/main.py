from fastapi import FastAPI
import asyncio
from app.core.db import init_db, seed_currencies, seed_categories, auto_update_exchange_rates, async_session_maker
from app.api.auth import router as auth_router
from app.api.transactions import router as transaction_router
from app.api.accounts import router as accounts_router
from app.api.exchange_rate import router as exchange_rate_router
from app.api.analytics import router as analytics_router
from app.api.category import router as category_router

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await init_db()
    async with async_session_maker() as session:
        await seed_currencies(session)
        await seed_categories(session)
    asyncio.create_task(run_startup_tasks(session))

async def run_startup_tasks(session):
    try:
        await auto_update_exchange_rates(session)
    except Exception as e:
        print(f"⚠️ Не вдалося оновити курси при старті: {e}")

app.include_router(auth_router)
app.include_router(transaction_router)
app.include_router(accounts_router)
app.include_router(exchange_rate_router)
app.include_router(analytics_router)
app.include_router(category_router)
