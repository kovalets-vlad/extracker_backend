from pydantic import BaseModel, EmailStr, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class UserSettingsUpdate(BaseModel):
    target_essential: float
    target_wants: float
    target_savings: float

    @model_validator(mode='after')
    def check_sum_equals_100(self) -> 'UserSettingsUpdate':
        total = self.target_essential + self.target_wants + self.target_savings
        if total != 100.0:
            raise ValueError(f"Сума відсотків має дорівнювати 100. Зараз: {total}")
        return self