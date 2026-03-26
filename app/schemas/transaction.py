from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone
from app.models.transaction import SourceType, TransactionType

class TransactionCreate(BaseModel):
    amount: Decimal
    description: Optional[str] = None
    category_id: int
    account_id: int
    type: TransactionType = TransactionType.EXPENSE
    source: SourceType = SourceType.MANUAL
    transaction_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal 
    target_amount: Optional[Decimal] = None
    description: Optional[str] = "Внутрішній переказ"
    transaction_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )