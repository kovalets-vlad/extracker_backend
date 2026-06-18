from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.core.constants.currency import CurrencyCode

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.user import User


class Currency(SQLModel, table=True):
    __tablename__ = "currencies"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: CurrencyCode = Field(index=True, unique=True)
    name: str
    symbol: str

    users: list["User"] = Relationship(back_populates="currency")
    accounts: list["Account"] = Relationship(back_populates="currency")
