from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import TransactionType


class RecurringTransactionCreate(BaseModel):
    amount: Decimal = Field(gt=Decimal("0"))
    description: Optional[str] = Field(default=None, max_length=500)
    type: TransactionType
    account_id: int
    category_id: int
    interval_days: int = Field(default=30, gt=0)
    start_date: date = Field(default_factory=date.today)
    last_executed_at: Optional[date] = None
    is_calendar_monthly: bool = False


class RecurringTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    category_id: int
    amount: Decimal
    description: Optional[str] = None
    type: TransactionType
    interval_days: int
    start_date: date
    last_executed_at: Optional[date] = None
    is_calendar_monthly: bool
    is_active: bool


class RecurringTransactionResponse(BaseModel):
    status: str = "success"
    template: RecurringTransactionRead
