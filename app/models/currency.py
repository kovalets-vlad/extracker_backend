from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from app.core.constants.currency import CurrencyCode 
from app.models.user import User
from app.models.account import Account

class Currency(SQLModel, table=True):
    __tablename__ = "currencies"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: CurrencyCode = Field(index=True, unique=True) 
    name: str 
    symbol: str
    
    users: List["User"] = Relationship(back_populates="currency")
    accounts: List["Account"] = Relationship(back_populates="currency")