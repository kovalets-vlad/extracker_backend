from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.user import UserSettingsResponse, UserSettingsUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings: UserSettingsUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    updated_user = await UserService.update_settings(session, settings, current_user)
    return {
        "status": "success",
        "message": "Налаштування бюджету успішно оновлено!",
        "settings": {
            "essential": updated_user.target_essential,
            "wants": updated_user.target_wants,
            "savings": updated_user.target_savings,
        },
    }
