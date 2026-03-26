from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy import extract
from sqlalchemy.orm import joinedload
from typing import Optional
from datetime import datetime, timezone
from app.core.db import AsyncSession, get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransferCreate

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/transfer")
async def create_transfer(
    data: TransferCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    from_acc = await session.get(Account, data.from_account_id)
    to_acc = await session.get(Account, data.to_account_id)

    if not from_acc or from_acc.user_id != current_user.id or \
       not to_acc or to_acc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Один з гаманців не знайдено")
    
    received_amount = data.target_amount or data.amount

    swt = select(Category).where(Category.name == "Переказ")
    result = await session.execute(swt)
    transfer_category = result.scalars().first()

    t_date = data.transaction_date or datetime.now(timezone.utc)

    out_transaction = Transaction(
        amount=-data.amount, 
        description=data.description,
        account_id=data.from_account_id,
        user_id=current_user.id,
        type=TransactionType.TRANSFER,
        category_id=transfer_category.id,
        transaction_date=t_date 
    )

    in_transaction = Transaction(
        amount=received_amount, 
        description=data.description,
        account_id=data.to_account_id,
        user_id=current_user.id,
        type=TransactionType.TRANSFER,
        category_id=transfer_category.id,
        transaction_date=t_date 
    )

    from_acc.balance -= data.amount
    to_acc.balance += received_amount 

    session.add_all([out_transaction, in_transaction, from_acc, to_acc])
    await session.commit()
    return {"status": "success", "received": received_amount}

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    account = await session.get(Account, data.account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Гаманець не знайдено")

    category_stmt = select(Category).where(
        Category.id == data.category_id,
        (Category.user_id == current_user.id) | (Category.user_id == None)
    )
    category_res = await session.execute(category_stmt)
    if not category_res.scalars().first():
        raise HTTPException(status_code=400, detail="Категорія не знайдена")

    new_transaction = Transaction(
        **data.model_dump(),
        user_id=current_user.id
    )

    if new_transaction.type == TransactionType.EXPENSE:
        account.balance -= data.amount
    elif new_transaction.type == TransactionType.INCOME:
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
    category_id: Optional[int] = None,
    type: Optional[TransactionType] = None,
    offset: int = 0, 
    limit: int = 20, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    target_month = month or now.month
    target_year = year or now.year

    stmt = (
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .options(joinedload(Transaction.category)) 
        .order_by(Transaction.transaction_date.desc())
    )

    stmt = stmt.where(
        (extract('month', Transaction.transaction_date) == target_month) & 
        (extract('year', Transaction.transaction_date) == target_year)
    )

    if category_id: stmt = stmt.where(Transaction.category_id == category_id)
    if type: stmt = stmt.where(Transaction.type == type)

    stmt = stmt.offset(offset).limit(limit)
    
    result = await session.execute(stmt)
    transactions = result.scalars().all()

    result = await session.execute(stmt.offset(offset).limit(limit))
    transactions = result.scalars().all()
    
    return {
        "transactions": transactions,
        "next_offset": offset + limit if len(transactions) == limit else None
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
    transaction = await session.get(Transaction, transaction_id)
    if not transaction or transaction.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Транзакцію не знайдено")

    account = await session.get(Account, transaction.account_id)
    if account:
        if transaction.type == "expense":
            account.balance += transaction.amount
        else:
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
    transaction = await session.get(Transaction, transaction_id)
    if not transaction or transaction.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Транзакцію не знайдено")

    old_account = await session.get(Account, transaction.account_id)
    if old_account:
        if transaction.type == "expense":
            old_account.balance += transaction.amount
        else:
            old_account.balance -= transaction.amount
        session.add(old_account)

    new_account = await session.get(Account, data.account_id)
    if not new_account or new_account.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Цільовий гаманець не знайдено")

    if data.type == "expense":
        new_account.balance -= data.amount
    else:
        new_account.balance += data.amount
    session.add(new_account)

    for key, value in data.model_dump().items():
        setattr(transaction, key, value)

    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)

    return {"status": "success", "transaction": transaction}