from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Numeric, UniqueConstraint
from sqlmodel import Field, SQLModel


class UserCategory(SQLModel, table=True):
    __tablename__ = "user_categories"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id", index=True)
    category_id: int = Field(foreign_key="categories.id", index=True)

    monthly_limit: Optional[Decimal] = Field(
        default=None, sa_column=Column(Numeric(precision=12, scale=2))
    )

    __table_args__ = (UniqueConstraint("user_id", "category_id", name="unique_user_category"),)
