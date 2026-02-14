from pydantic import BaseModel
from decimal import Decimal
from typing import Optional

class CategoryCreate(BaseModel):
    name: str
    limit: Optional[Decimal] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    limit: Optional[Decimal] = None

