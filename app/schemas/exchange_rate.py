from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CurrencyExchangeResponse(BaseModel):
    converted_amount: Decimal
    rate: Decimal
    message: str
    last_updated: datetime
