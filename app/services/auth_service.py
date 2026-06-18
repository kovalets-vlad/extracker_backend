from datetime import timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants.currency import CurrencyCode
from app.core.exceptions import AuthenticationError, ConflictError, SystemStateError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.account import Account
from app.models.user import User
from app.repositories.currencies import get_currency_by_code
from app.repositories.users import get_user_by_email
from app.schemas.user import UserCreate


class AuthService:
    @staticmethod
    async def register_user(session: AsyncSession, user_data: UserCreate) -> User:
        existing_user = await get_user_by_email(session, user_data.email)
        if existing_user:
            raise ConflictError("Користувач вже існує")

        uah_currency = await get_currency_by_code(session, CurrencyCode.UAH)
        if not uah_currency:
            raise SystemStateError("System error: currencies are not initialized")

        new_user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            currency_id=uah_currency.id,
        )
        session.add(new_user)
        await session.flush()

        session.add(
            Account(
                name="Main Account",
                balance=Decimal("0.00"),
                user_id=new_user.id,
                currency_id=uah_currency.id,
            )
        )

        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise ConflictError("Користувач вже існує") from exc

        await session.refresh(new_user)
        return new_user

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        email: str,
        password: str,
    ) -> str:
        user = await get_user_by_email(session, email)
        if not user or not verify_password(user.password_hash, password):
            raise AuthenticationError("Неправильна пошта або пароль")

        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(data={"sub": user.email}, expires_delta=expires_delta)
