from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .transaction import Transaction

class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: CategoryType = Field(default=CategoryType.EXPENSE, index=True)
    icon: Optional[str] = "folder" 
    
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    transactions: List["Transaction"] = Relationship(back_populates="category")