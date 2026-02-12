from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import select
from sqlalchemy.orm import joinedload
from app.core.db import AsyncSession, get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.currency import Currency
from app.schemas.account import AccountCreate, AccountReadWithCurrency

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("/", response_model=Account)
async def create_account(
    data: AccountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    currency_result = await session.execute(
        select(Currency).where(Currency.id == data.currency_code_id)
    )
    currency = currency_result.scalars().first()
    if not currency:
        raise HTTPException(status_code=400, detail="Невідома валюта")
    
    new_account = Account(
        name=data.name,
        currency_id=data.currency_code_id,
        user_id=current_user.id
    )
    
    session.add(new_account)
    await session.commit()
    await session.refresh(new_account)
    
    return {"status": "success", "account": new_account}

@router.get("/", response_model=List[AccountReadWithCurrency])
async def list_accounts(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Account)
        .where(Account.user_id == current_user.id)
        .options(joinedload(Account.currency))
    )
    
    result = await session.execute(stmt)
    accounts = result.scalars().all()
    
    return accounts