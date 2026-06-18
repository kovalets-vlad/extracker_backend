from math import isclose

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSettingsUpdate(BaseModel):
    target_essential: float = Field(ge=0, le=100)
    target_wants: float = Field(ge=0, le=100)
    target_savings: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def check_sum_equals_100(self) -> "UserSettingsUpdate":
        total = self.target_essential + self.target_wants + self.target_savings
        if not isclose(total, 100.0, abs_tol=0.01):
            raise ValueError(f"Budget percentages must sum to 100. Current total: {total}")
        return self


class UserSettingsResponse(BaseModel):
    status: str = "success"
    message: str
    settings: dict[str, float]
