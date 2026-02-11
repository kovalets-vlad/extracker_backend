from fastapi import FastAPI
from app.core.db import init_db, seed_currencies 
from app.api.auth import router as auth_router
from app.core.db import async_session_maker, seed_currencies


app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await init_db()
    async with async_session_maker() as session:
        await seed_currencies(session)

app.include_router(auth_router)