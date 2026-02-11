from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.transaction import Transaction
    from app.models.account import Account

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)
    
    currency_id: Optional[int] = Field(default=None, foreign_key="currencies.id")
    accounts: List["Account"] = Relationship(back_populates="user")
    
    currency: Optional["Currency"] = Relationship(back_populates="users")
    transactions: List["Transaction"] = Relationship(back_populates="user")
