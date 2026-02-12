from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from app.models.transaction import SourceType, TransactionType

class TransactionCreate(BaseModel):
    amount: Decimal
    description: Optional[str] = None
    category_id: int
    account_id: int
    type: TransactionType = TransactionType.EXPENSE
    source: SourceType = SourceType.MANUAL

