from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy import extract
from sqlalchemy.orm import joinedload
from typing import Optional
from datetime import datetime
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
    
    received_amount = data.target_amount

    if received_amount is None:
        raise HTTPException(status_code=400, detail="target_amount обов'язковий для переказів без вказаної суми отримання")
    
    swt = select(Category).where(Category.name == "Переказ")
    result = await session.execute(swt)
    transfer_category = result.scalars().first()

    if not transfer_category:
        raise HTTPException(status_code=500, detail="Категорія 'Переказ' не знайдена. Зверніться до адміністратора.")

    out_transaction = Transaction(
        amount=-data.amount, 
        description=data.description,
        account_id=data.from_account_id,
        user_id=current_user.id,
        type=TransactionType.TRANSFER,
        category_id=transfer_category.id
    )

    in_transaction = Transaction(
        amount=data.amount, 
        description=data.description,
        account_id=data.to_account_id,
        user_id=current_user.id,
        type=TransactionType.TRANSFER,
        category_id=transfer_category.id
    )

    from_acc.balance -= data.amount
    to_acc.balance += data.amount

    session.add_all([out_transaction, in_transaction, from_acc, to_acc])
    await session.commit()

    return {"status": "success", "message": "Переказ виконано"}

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
    month: Optional[int] = datetime.now().month, 
    year: Optional[int] = datetime.now().year,
    category_id: Optional[int] = None,
    type: Optional[TransactionType] = None,
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

    if category_id is not None:
        stmt = stmt.where(Transaction.category_id == category_id)

    if type is not None:
        stmt = stmt.where(Transaction.type == type)

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