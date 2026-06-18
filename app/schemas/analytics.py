from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel


class BudgetResponse(BaseModel):
    status: str = "success"
    data: dict[str, Any]


class DashboardMonthlySummary(BaseModel):
    income: Decimal
    expense: Decimal
    transfers: Decimal
    net_change: Decimal


class DashboardResponse(BaseModel):
    account_name: str
    current_balance: Decimal
    currency: str
    monthly_summary: DashboardMonthlySummary


class CategorySummaryItem(BaseModel):
    category: str
    spent: Decimal
    limit: Decimal
    remaining: Optional[Decimal]
    overspent: bool
