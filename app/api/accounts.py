from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.account import (
    AccountCreate,
    AccountMutationResponse,
    AccountReadWithCurrency,
    AccountSetLimit,
)
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountMutationResponse)
async def create_account(
    data: AccountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    account = await AccountService.create_account(session, data, current_user)
    return {"status": "success", "account": account}


@router.post("/{account_id}/set_limit", response_model=AccountMutationResponse)
async def set_monthly_limit(
    account_id: int,
    data: AccountSetLimit,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    account = await AccountService.set_monthly_limit(session, account_id, data, current_user)
    return {"status": "success", "account": account}


@router.get("/", response_model=list[AccountReadWithCurrency])
async def list_accounts(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await AccountService.list_accounts(session, current_user)
