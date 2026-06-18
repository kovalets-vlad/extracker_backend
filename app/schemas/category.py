from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants.category import CategoryGroup


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    limit: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    limit: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: Optional[str] = None
    group: CategoryGroup
    user_id: Optional[int] = None


class CategoryMutationResponse(BaseModel):
    status: str = "success"
    category: CategoryRead
    limit: Optional[Decimal] = None


class MessageResponse(BaseModel):
    status: str = "success"
    message: str
