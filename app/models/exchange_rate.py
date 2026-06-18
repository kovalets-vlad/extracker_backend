from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric
from sqlmodel import Field, SQLModel


class ExchangeRate(SQLModel, table=True):
    __tablename__ = "exchange_rates"

    code: str = Field(primary_key=True)
    rate_to_usd: Decimal = Field(sa_column=Column(Numeric(precision=12, scale=6), nullable=False))

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_type=DateTime(timezone=True)
    )
