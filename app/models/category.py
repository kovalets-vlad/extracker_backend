from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.core.constants.category import CategoryGroup
from app.models.transaction import Transaction


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    icon: Optional[str] = "folder"
    group: CategoryGroup = Field(default=CategoryGroup.OTHER)

    transactions: list["Transaction"] = Relationship(back_populates="category")

    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
