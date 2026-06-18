from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionResponse,
)
from app.services.recurring_transaction_service import RecurringTransactionService

router = APIRouter(prefix="/recurring_transactions", tags=["recurring_transactions"])


@router.post(
    "/",
    response_model=RecurringTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recurring_template(
    data: RecurringTransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    template = await RecurringTransactionService.create_template(session, data, current_user)
    return {"status": "success", "template": template}
