from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from typing import Optional
from app.core.db import AsyncSession, get_session
from app.api.deps import get_current_user
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user_category import UserCategory

router = APIRouter(prefix="/analytics", tags=["analytics"])

from sqlalchemy import func
from datetime import datetime

@router.get("/dashboard")
async def get_dashboard_data(
    account_id: int,
    month: Optional[int] = datetime.now().month,
    year: Optional[int] = datetime.now().year,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    account = await session.get(Account, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Гаманець не знайдено")

    start_of_month = datetime(year, month, 1)

    stmt = (
        select(
            Transaction.type,
            func.sum(Transaction.amount).label("total")
        )
        .where(Transaction.account_id == account_id)
        .where(Transaction.created_at >= start_of_month)
        .group_by(Transaction.type)
    )
    
    result = await session.execute(stmt)
    totals = {row[0]: row[1] for row in result.all()}

    return {
        "account_name": account.name,
        "current_balance": account.balance,
        "currency": account.currency_code,
        "monthly_summary": {
            "income": totals.get("income", 0),
            "expense": totals.get("expense", 0),
            "transfers": totals.get("transfer", 0),
            "net_change": totals.get("income", 0) + totals.get("expense", 0) 
        }
    }


@router.get("/categories-summary")
async def get_categories_summary(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    stmt = (
        select(
            Category.name,
            func.sum(Transaction.amount).label("spent"),
            UserCategory.monthly_limit
        )
        .join(Category, Transaction.category_id == Category.id)
        .outerjoin(UserCategory, 
            (UserCategory.category_id == Category.id) & 
            (UserCategory.user_id == current_user.id)
        )
        .where(Transaction.account_id == account_id)
        .where(Transaction.type == "expense")
        .group_by(Category.name, UserCategory.monthly_limit)
    )

    result = await session.execute(stmt)
    summary = []
    
    for name, spent, limit in result.all():
        spent_abs = abs(spent)
        summary.append({
            "category": name,
            "spent": spent_abs,
            "limit": limit or 0,
            "remaining": (limit - spent_abs) if limit else None,
            "overspent": spent_abs > limit if limit else False
        })

    return summary