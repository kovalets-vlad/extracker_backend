from datetime import datetime, timezone 
from decimal import Decimal
from enum import Enum 
from sqlalchemy import Column, Numeric, DateTime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category
    from app.models.account import Account 

class SourceType(str, Enum):
    BANK = "bank"
    MANUAL = "manual"
    ML = "ml"

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    amount: Decimal = Field(sa_column=Column(Numeric(precision=12, scale=2), nullable=False))
    description: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True), 
        index=True
    )
    
    source: SourceType = Field(default=SourceType.MANUAL)
    type: TransactionType = Field(default=TransactionType.EXPENSE)

    user_id: int = Field(foreign_key="users.id", index=True)
    category_id: int = Field(foreign_key="categories.id", index=True)
    account_id: int = Field(foreign_key="accounts.id", index=True) 

    user: Optional["User"] = Relationship(back_populates="transactions")
    category: Optional["Category"] = Relationship(back_populates="transactions")
    account: Optional["Account"] = Relationship(back_populates="transactions")