from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.category import MessageResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionMutationResponse,
    TransferCreate,
    TransferResponse,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/transfer", response_model=TransferResponse)
async def create_transfer(
    data: TransferCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await TransactionService.create_transfer(session, data, current_user)
    return {"status": "success", **result}


@router.post(
    "/",
    response_model=TransactionMutationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    transaction = await TransactionService.create_transaction(session, data, current_user)
    return {"status": "success", "transaction": transaction}


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    month: Optional[int] = Query(default=None, ge=1, le=12),
    year: Optional[int] = Query(default=None, ge=1970, le=9999),
    category_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = Query(default=None, alias="type"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    result = await TransactionService.list_transactions(
        session,
        current_user,
        month=month or now.month,
        year=year or now.year,
        category_id=category_id,
        transaction_type=transaction_type,
        offset=offset,
        limit=limit,
    )
    return result


@router.get("/{transaction_id}", response_model=TransactionMutationResponse)
async def get_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    transaction = await TransactionService.get_transaction(session, transaction_id, current_user)
    return {"status": "success", "transaction": transaction}


@router.delete("/{transaction_id}", response_model=MessageResponse)
async def delete_transaction(
    transaction_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await TransactionService.delete_transaction(session, transaction_id, current_user)
    return {"status": "success", "message": "Транзакція видалена"}


@router.put("/{transaction_id}", response_model=TransactionMutationResponse)
async def update_transaction(
    transaction_id: int,
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    transaction = await TransactionService.update_transaction(
        session,
        transaction_id,
        data,
        current_user,
    )
    return {"status": "success", "transaction": transaction}
