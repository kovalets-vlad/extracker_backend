from decimal import Decimal
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.core.constants.currency import CurrencyCode


class CurrencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: CurrencyCode
    name: str
    symbol: str


class AccountCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    currency_id: int = Field(validation_alias=AliasChoices("currency_id", "currency_code_id"))


class AccountUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    currency_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("currency_id", "currency_code_id"),
    )


class AccountSetLimit(BaseModel):
    monthly_limit: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    balance: Decimal
    currency_id: int
    monthly_limit: Optional[Decimal] = None


class AccountReadWithCurrency(AccountRead):
    currency: Optional[CurrencyRead] = None


class AccountMutationResponse(BaseModel):
    status: str = "success"
    account: AccountRead
