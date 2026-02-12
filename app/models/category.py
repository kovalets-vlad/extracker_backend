from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.transaction import Transaction

class DefaultCategory(str, Enum):
    FOOD = "Продукти"
    TRANSPORT = "Транспорт"
    HOUSING = "Житло/Гуртожиток"
    ENTERTAINMENT = "Розваги"
    HEALTH = "Здоров'я"
    OTHER = "Інше"
    SALARY = "Зарплата/Стипендія"
    TRANSFER = "Переказ"

CATEGORY_DATA = {
    DefaultCategory.FOOD: {"name": "Продукти", "icon": "🛒"},
    DefaultCategory.TRANSPORT: {"name": "Транспорт", "icon": "🚌"},
    DefaultCategory.HOUSING: {"name": "Гуртожиток", "icon": "🏠"},
    DefaultCategory.ENTERTAINMENT: {"name": "Розваги", "icon": "🎮"},
    DefaultCategory.HEALTH: {"name": "Здоров'я", "icon": "💊"},
    DefaultCategory.OTHER: {"name": "Інше", "icon": "📦"},
    DefaultCategory.SALARY: {"name": "Зарплата/Стипендія", "icon": "💸"},
    DefaultCategory.TRANSFER: {"name": "Переказ", "icon": "🔄"},
}

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    icon: Optional[str] = "folder" 
    
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    transactions: List["Transaction"] = Relationship(back_populates="category")

    @classmethod
    def create_default(cls, category_enum: DefaultCategory):
        """
        Фабричний метод: створює об'єкт категорії на основі Enum.
        """
        data = CATEGORY_DATA.get(category_enum)
        
        return cls(
            name=data["name"],
            icon=data["icon"]
        )