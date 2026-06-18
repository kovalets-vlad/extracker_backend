from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.analytics import BudgetResponse, CategorySummaryItem, DashboardResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(
    account_id: int,
    month: Optional[int] = Query(default=None, ge=1, le=12),
    year: Optional[int] = Query(default=None, ge=1970, le=9999),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    return await AnalyticsService.get_dashboard_data(
        session,
        current_user,
        account_id,
        month or now.month,
        year or now.year,
    )


@router.get("/categories-summary", response_model=list[CategorySummaryItem])
async def get_categories_summary(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await AnalyticsService.get_categories_summary(session, current_user, account_id)


@router.get("/budget", response_model=BudgetResponse)
async def get_budget_analytics(
    month: Optional[int] = Query(default=None, ge=1, le=12),
    year: Optional[int] = Query(default=None, ge=1970, le=9999),
    base_currency: str = Query(default="UAH", min_length=3, max_length=3),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    report = await AnalyticsService.get_budget_with_trends(
        session=session,
        user=current_user,
        month=month or now.month,
        year=year or now.year,
        base_currency=base_currency.upper(),
    )
    return {"status": "success", "data": report}
