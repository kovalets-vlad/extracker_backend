from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserSettingsUpdate


class UserService:
    @staticmethod
    async def update_settings(
        session: AsyncSession,
        settings: UserSettingsUpdate,
        current_user: User,
    ) -> User:
        current_user.target_essential = settings.target_essential
        current_user.target_wants = settings.target_wants
        current_user.target_savings = settings.target_savings

        session.add(current_user)
        await session.commit()
        await session.refresh(current_user)
        return current_user
