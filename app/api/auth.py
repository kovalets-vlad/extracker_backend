from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from decimal import Decimal
from app.models.user import User
from app.models.currency import Currency, CurrencyCode
from app.models.account import Account
from app.schemas.user import UserCreate, UserOut
from app.core.security import hash_password, verify_password, create_access_token
from app.core.db import AsyncSession, get_session

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Користувач вже існує")

    hashed_password = hash_password(user_data.password)
    new_user = User(email=user_data.email, password_hash=hashed_password)
    session.add(new_user)
    
    await session.flush()

    currency_result = await session.execute(
        select(Currency).where(Currency.code == CurrencyCode.UAH)
    )
    uah_currency = currency_result.scalars().first()

    if not uah_currency:
        raise HTTPException(status_code=500, detail="Системна помилка: валюти не ініціалізовані")

    default_account = Account(
        name="Main Account",
        balance=Decimal("0.0"),
        user_id=new_user.id,
        currency_id=uah_currency.id
    )
    session.add(default_account)

    await session.commit()
    await session.refresh(new_user)
    
    return new_user

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: AsyncSession = Depends(get_session)
):
    statement = select(User).where(User.email == form_data.username)
    result = await session.execute(statement)
    user = result.scalars().first()

    if not user or not verify_password(user.password_hash, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильна пошта або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}