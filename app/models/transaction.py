from datetime import datetime, timezone 
from decimal import Decimal
from enum import Enum 
from sqlalchemy import Column, Numeric
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category

class SourceType(str, Enum):
    BANK = "bank"
    MANUAL = "manual"
    ML = "ml"

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    amount: Decimal = Field(sa_column=Column(Numeric(precision=12, scale=2), nullable=False))
    description: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        index=True
    )
    
    source: SourceType = Field(default=SourceType.MANUAL, index=True)
    
    user_id: int = Field(foreign_key="users.id", index=True)
    category_id: int = Field(foreign_key="categories.id", index=True)
    
    user: Optional["User"] = Relationship(back_populates="transactions")
    category: Optional["Category"] = Relationship(back_populates="transactions")