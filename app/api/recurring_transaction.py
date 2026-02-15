from fastapi import APIRouter, Depends, HTTPException
from app.core.db import AsyncSession, get_session
from app.api.deps import get_current_user
from app.models.account import Account
from app.models.recurring_transaction import RecurringTransaction
from app.schemas.recurring_transaction import RecurringCreate

router = APIRouter(prefix="/recurring_transactions", tags=["recurring_transactions"])

@router.post("/")
async def create_recurring_template(
    data: RecurringCreate, 
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user)
):
    account = await session.get(Account, data.account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Гаманець не знайдено")

    new_template = RecurringTransaction(
        **data.model_dump(),
        user_id=current_user.id
    )
    
    session.add(new_template)
    await session.commit()
    await session.refresh(new_template)
    
    return {"status": "success", "template": new_template}