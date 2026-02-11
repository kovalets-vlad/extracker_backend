from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User

class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    UAH = "UAH"
    GBP = "GBP"

CURRENCY_DATA = {
    CurrencyCode.USD: {"name": "US Dollar", "symbol": "$"},
    CurrencyCode.EUR: {"name": "Euro", "symbol": "€"},
    CurrencyCode.UAH: {"name": "Ukrainian Hryvnia", "symbol": "₴"},
    CurrencyCode.GBP: {"name": "British Pound", "symbol": "£"},
}

class Currency(SQLModel, table=True):
    __tablename__ = "currencies"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: CurrencyCode = Field(unique=True, index=True)
    name: str 
    symbol: str
    
    users: List["User"] = Relationship(back_populates="currency")

    @classmethod
    def create_default(cls, code: CurrencyCode):
        data = CURRENCY_DATA.get(code)
        return cls(code=code, name=data["name"], symbol=data["symbol"])
    