from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.currency import Currency
    from app.models.transaction import Transaction


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)

    currency_id: Optional[int] = Field(default=None, foreign_key="currencies.id")
    target_essential: float = Field(default=60.0)
    target_wants: float = Field(default=20.0)
    target_savings: float = Field(default=20.0)
    accounts: list["Account"] = Relationship(back_populates="user")

    currency: Optional["Currency"] = Relationship(back_populates="users")
    transactions: list["Transaction"] = Relationship(back_populates="user")
