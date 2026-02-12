from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy import extract
from sqlalchemy.orm import joinedload
from typing import Optional
from app.core.db import AsyncSession, get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.account import Account
from app.schemas.transaction import TransactionCreate

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    account_stmt = select(Account).where(
        Account.id == data.account_id, 
        Account.user_id == current_user.id
    )
    result = await session.execute(account_stmt)
    account = result.scalars().first()

    if not account:
        raise HTTPException(status_code=404, detail="Гаманець не знайдено або він вам не належить")

    new_transaction = Transaction(
        **data.model_dump(),
        user_id=current_user.id
    )

    if new_transaction.type == "expense":
        account.balance -= data.amount
    else:
        account.balance += data.amount

    session.add(new_transaction)
    session.add(account) 
    
    await session.commit()
    await session.refresh(new_transaction)
    
    return {"status": "success", "transaction": new_transaction}


@router.get("/")
async def list_transactions(
    month: Optional[int] = None, 
    year: Optional[int] = None,
    offset: int = 0, 
    limit: int = 20, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .options(joinedload(Transaction.category)) 
        .order_by(Transaction.created_at.desc())
    )

    if month is not None:
        stmt = stmt.where(extract('month', Transaction.created_at) == month)
    
    if year is not None:
        stmt = stmt.where(extract('year', Transaction.created_at) == year)

    stmt = stmt.offset(offset).limit(limit)
    
    result = await session.execute(stmt)
    transactions = result.scalars().all()

    if len(transactions) < limit:
        next_offset = None
    else:
        next_offset = offset + limit
    
    return {
        "transactions": transactions,
        "next_offset": next_offset
    }

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Transaction).where(
        Transaction.id == transaction_id, 
        Transaction.user_id == current_user.id
    )
    result = await session.execute(stmt)
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакція не знайдена або вона вам не належить")

    return {"status": "success", "transaction": transaction}

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Transaction).where(
        Transaction.id == transaction_id, 
        Transaction.user_id == current_user.id
    )
    result = await session.execute(stmt)
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакцію не знайдено")

    account = await session.get(Account, transaction.account_id)
    if account:
        account.balance -= transaction.amount 
        session.add(account)

    await session.delete(transaction)
    await session.commit() 
    
@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Transaction).where(
        Transaction.id == transaction_id, 
        Transaction.user_id == current_user.id
    )
    result = await session.execute(stmt)
    transaction = result.scalars().first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакцію не знайдено")

    old_account = await session.get(Account, transaction.account_id)
    
    if transaction.account_id != data.account_id:
        new_account = await session.get(Account, data.account_id)
        if not new_account or new_account.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Новий гаманець не знайдено")
        
        old_account.balance -= transaction.amount
        new_account.balance += data.amount
        
        session.add(old_account)
        session.add(new_account)
    else:
        old_account.balance = old_account.balance - transaction.amount + data.amount
        session.add(old_account)

    for key, value in data.model_dump().items():
        setattr(transaction, key, value)

    session.add(transaction)
    await session.commit() 
    await session.refresh(transaction)

    return {"status": "success", "transaction": transaction}