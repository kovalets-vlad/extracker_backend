from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSession, get_session
from app.api.deps import get_current_user
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user_category import UserCategory
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

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

@router.get("/budget")
async def get_budget_analytics(
    month: Optional[int] = Query(None, description="Місяць (1-12)"),
    year: Optional[int] = Query(None, description="Рік (наприклад, 2026)"),
    base_currency: str = Query("UAH", description="Валюта для зведення звіту"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    target_month = month or now.month
    target_year = year or now.year

    report = await AnalyticsService.get_budget_with_trends(
        session=session,
        user=current_user,
        month=target_month,
        year=target_year,
        base_currency=base_currency.upper()
    )

    return {"status": "success", "data": report}