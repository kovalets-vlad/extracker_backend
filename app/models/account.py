from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.transaction import Transaction
    from app.models.user import User


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    balance: Decimal = Field(
        default=Decimal("0.0"), sa_column=Column(Numeric(precision=12, scale=2), nullable=False)
    )

    user_id: int = Field(foreign_key="users.id", index=True)
    currency_id: int = Field(foreign_key="currencies.id", index=True)
    monthly_limit: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(12, 2)))

    user: Optional["User"] = Relationship(back_populates="accounts")
    currency: Optional["Currency"] = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(
        back_populates="account", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
