from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.db import init_db, get_session_context
from app.services.category_service import seed_default_categories
from app.services.currency_service import seed_currencies
from app.services.exchange_rate_service import auto_update_exchange_rates
from app.api.auth import router as auth_router
from app.api.transactions import router as transaction_router
from app.api.accounts import router as accounts_router
from app.api.exchange_rate import router as exchange_rate_router
from app.api.analytics import router as analytics_router
from app.api.category import router as category_router
from app.api.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db() 
    
    async with get_session_context() as session:
        await seed_currencies(session)
        await auto_update_exchange_rates(session)
        await seed_default_categories(session)
        
    print("🚀 Бекенд готовий до роботи, валюти та категорії ініціалізовані!")
    yield

app = FastAPI(lifespan=lifespan)


app.include_router(auth_router)
app.include_router(transaction_router)
app.include_router(accounts_router)
app.include_router(exchange_rate_router)
app.include_router(analytics_router)
app.include_router(category_router)
app.include_router(users_router)