from fastapi import FastAPI
from app.core.db import init_db 

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await init_db()

