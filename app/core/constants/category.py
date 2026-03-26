from enum import Enum

class CategoryGroup(str, Enum):
    ESSENTIAL = "essential" 
    WANTS = "wants"         
    SAVINGS = "savings"     
    OTHER = "other"

class DefaultCategory(str, Enum):
    FOOD = "Продукти"
    TRANSPORT = "Транспорт"
    HOUSING = "Житло"
    ENTERTAINMENT = "Розваги"
    HEALTH = "Здоров'я"
    OTHER = "Інше"
    SALARY = "Зарплата/Стипендія"
    TRANSFER = "Переказ"
    UTILITIES = "Комуналка"
    COMMUNICATION = "Зв'язок та інтернет"
    CAR_MAINTENANCE = "Авто"
    CAFES = "Кафе та ресторани"
    SHOPPING = "Покупки"
    SUBSCRIPTIONS = "Підписки"
    EDUCATION = "Курси/Книги"
    INVESTMENTS = "Інвестиції"
    SAVINGS_FILL = "Поповнення подушки"

CATEGORY_DATA = {
    DefaultCategory.FOOD: {"name": "Продукти", "icon": "🛒", "group": CategoryGroup.ESSENTIAL},
    DefaultCategory.TRANSPORT: {"name": "Транспорт", "icon": "🚌", "group": CategoryGroup.ESSENTIAL},
    DefaultCategory.HOUSING: {"name": "Житло", "icon": "🏠", "group": CategoryGroup.ESSENTIAL},
    DefaultCategory.HEALTH: {"name": "Здоров'я", "icon": "💊", "group": CategoryGroup.ESSENTIAL},
    DefaultCategory.UTILITIES: {"name": "Комуналка", "icon": "⚡", "group": CategoryGroup.ESSENTIAL},
    DefaultCategory.COMMUNICATION: {"name": "Зв'язок та інтернет", "icon": "📱", "group": CategoryGroup.ESSENTIAL},
    DefaultCategory.CAR_MAINTENANCE: {"name": "Авто", "icon": "🚗", "group": CategoryGroup.ESSENTIAL}, 

    DefaultCategory.ENTERTAINMENT: {"name": "Розваги", "icon": "🎮", "group": CategoryGroup.WANTS}, 
    DefaultCategory.CAFES: {"name": "Кафе та ресторани", "icon": "☕", "group": CategoryGroup.WANTS},
    DefaultCategory.SHOPPING: {"name": "Покупки", "icon": "🛍️", "group": CategoryGroup.WANTS}, 
    DefaultCategory.SUBSCRIPTIONS: {"name": "Підписки", "icon": "📺", "group": CategoryGroup.WANTS},
    DefaultCategory.EDUCATION: {"name": "Курси/Книги", "icon": "📚", "group": CategoryGroup.WANTS}, 

    DefaultCategory.INVESTMENTS: {"name": "Інвестиції", "icon": "📈", "group": CategoryGroup.SAVINGS},
    DefaultCategory.SAVINGS_FILL: {"name": "Поповнення подушки", "icon": "🛡️", "group": CategoryGroup.SAVINGS},
    
    DefaultCategory.SALARY: {"name": "Зарплата/Стипендія", "icon": "💰", "group": CategoryGroup.OTHER},
    DefaultCategory.TRANSFER: {"name": "Переказ", "icon": "🔄", "group": CategoryGroup.OTHER},
    DefaultCategory.OTHER: {"name": "Інше", "icon": "📦", "group": CategoryGroup.OTHER},
}