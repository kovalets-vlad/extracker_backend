from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from app.models.currency import Currency

class AccountCreate(BaseModel):
    name: str
    currency_code_id: int

class AccountReadWithCurrency(BaseModel):
    id: int
    name: str
    balance: Decimal
    currency: Optional[Currency] = None 

    class Config:
        from_attributes = True

