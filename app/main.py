from fastapi import FastAPI
from app.core.db import init_db, seed_currencies, seed_categories, auto_update_exchange_rates, async_session_maker
from app.api.auth import router as auth_router
from app.api.transactions import router as transaction_router
from app.api.accounts import router as accounts_router
from app.api.exchange_rate import router as exchange_rate_router

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await init_db()
    async with async_session_maker() as session:
        await seed_currencies(session)
        await seed_categories(session)
        await auto_update_exchange_rates(session)

app.include_router(auth_router)
app.include_router(transaction_router)
app.include_router(accounts_router)
app.include_router(exchange_rate_router)
