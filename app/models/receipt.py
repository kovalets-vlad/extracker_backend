from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON

class Receipt(SQLModel, table=True):
    __tablename__ = "receipts"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    user_id: int = Field(foreign_key="users.id", index=True)
    transaction_id: Optional[int] = Field(default=None, foreign_key="transactions.id")
    
    image_url: Optional[str] = Field(default=None)
    raw_ocr_output: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    is_verified: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)