from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import Column, Numeric
from sqlmodel import SQLModel, Field

class RecurringTransaction(SQLModel, table=True):
    __tablename__ = "recurring_transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    account_id: int = Field(foreign_key="accounts.id")
    category_id: int = Field(foreign_key="categories.id")
    
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    description: Optional[str] = Field(default=None)
    type: str 
    
    interval_days: int = Field(default=30) 
    start_date: date = Field(default_factory=date.today)
    last_executed_at: Optional[date] = Field(default=None)
    is_calendar_monthly: bool = Field(default=False)
    
    is_active: bool = Field(default=True)