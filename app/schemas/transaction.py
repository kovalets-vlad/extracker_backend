from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.transaction import SourceType, TransactionType


class TransactionCreate(BaseModel):
    amount: Decimal = Field(gt=Decimal("0"))
    description: Optional[str] = Field(default=None, max_length=500)
    category_id: int
    account_id: int
    type: TransactionType = TransactionType.EXPENSE
    source: SourceType = SourceType.MANUAL
    transaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def reject_transfer_endpoint_misuse(self) -> "TransactionCreate":
        if self.type == TransactionType.TRANSFER:
            raise ValueError("Use /transactions/transfer for transfers")
        return self


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(gt=Decimal("0"))
    target_amount: Optional[Decimal] = Field(default=None, gt=Decimal("0"))
    description: Optional[str] = Field(default="Внутрішній переказ", max_length=500)
    transaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def require_distinct_accounts(self) -> "TransferCreate":
        if self.from_account_id == self.to_account_id:
            raise ValueError("Transfer accounts must be different")
        return self


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: Optional[str] = None
    created_at: datetime
    transaction_date: datetime
    source: SourceType
    type: TransactionType
    user_id: int
    category_id: int
    account_id: int


class TransactionMutationResponse(BaseModel):
    status: str = "success"
    transaction: TransactionRead


class TransferResponse(BaseModel):
    status: str = "success"
    received: Decimal


class TransactionListResponse(BaseModel):
    transactions: list[TransactionRead]
    next_offset: Optional[int]
