from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from app.models.transaction import Transaction
from app.core.constants.category import CategoryGroup

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    icon: Optional[str] = "folder"
    group: CategoryGroup = Field(default=CategoryGroup.OTHER) 

    transactions: List["Transaction"] = Relationship(back_populates="category")
    
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")