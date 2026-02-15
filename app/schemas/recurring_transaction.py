from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import date

class RecurringTransactionCreate(BaseModel):
    amount: Decimal
    description: Optional[str] = None
    type: str 
    account_id: int
    category_id: int
    interval_days: int = 30 
    last_executed_at: Optional[date] = None
    is_calendar_monthly: bool = False
