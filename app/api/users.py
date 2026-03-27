from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserSettingsUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.put("/settings")
async def update_user_settings(
    settings: UserSettingsUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    current_user.target_essential = settings.target_essential
    current_user.target_wants = settings.target_wants
    current_user.target_savings = settings.target_savings

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return {
        "status": "success",
        "message": "Налаштування бюджету успішно оновлено!",
        "settings": {
            "essential": current_user.target_essential,
            "wants": current_user.target_wants,
            "savings": current_user.target_savings
        }
    }