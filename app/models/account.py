from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Column, Numeric
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.currency import Currency
    from app.models.transaction import Transaction

class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    balance: Decimal = Field(
        default=Decimal("0.0"), 
        sa_column=Column(Numeric(precision=12, scale=2), nullable=False)
    )

    user_id: int = Field(foreign_key="users.id", index=True)
    currency_id: int = Field(foreign_key="currencies.id", index=True)

    user: Optional["User"] = Relationship(back_populates="accounts")
    currency: Optional["Currency"] = Relationship(back_populates="accounts")
    transactions: List["Transaction"] = Relationship(
        back_populates="account", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"} 
    )