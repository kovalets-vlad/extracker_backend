from decimal import Decimal
from typing import Optional

from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.constants.category import DefaultCategory
from app.core.exceptions import NotFoundError, SystemStateError, ValidationError
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.repositories.accounts import get_account_for_user, get_accounts_for_user
from app.repositories.categories import get_accessible_category, get_system_category_by_name
from app.repositories.transactions import get_transaction_for_user
from app.schemas.transaction import TransactionCreate, TransferCreate


def _apply_balance_effect(
    account: Account,
    transaction_type: TransactionType,
    amount: Decimal,
    *,
    reverse: bool = False,
) -> None:
    if transaction_type == TransactionType.INCOME:
        delta = amount
    elif transaction_type == TransactionType.EXPENSE:
        delta = -amount
    else:
        delta = amount

    if reverse:
        delta = -delta

    account.balance += delta


class TransactionService:
    @staticmethod
    async def create_transfer(
        session: AsyncSession,
        data: TransferCreate,
        current_user: User,
    ) -> dict[str, Decimal]:
        accounts = await get_accounts_for_user(
            session,
            [data.from_account_id, data.to_account_id],
            current_user.id,
            lock=True,
        )
        account_by_id = {account.id: account for account in accounts}
        from_account = account_by_id.get(data.from_account_id)
        to_account = account_by_id.get(data.to_account_id)
        if not from_account or not to_account:
            raise NotFoundError("Один з гаманців не знайдено")

        transfer_category = await get_system_category_by_name(
            session,
            DefaultCategory.TRANSFER.value,
        )
        if not transfer_category:
            raise SystemStateError("System transfer category is missing")

        received_amount = data.target_amount or data.amount
        out_transaction = Transaction(
            amount=-data.amount,
            description=data.description,
            account_id=data.from_account_id,
            user_id=current_user.id,
            type=TransactionType.TRANSFER,
            category_id=transfer_category.id,
            transaction_date=data.transaction_date,
        )
        in_transaction = Transaction(
            amount=received_amount,
            description=data.description,
            account_id=data.to_account_id,
            user_id=current_user.id,
            type=TransactionType.TRANSFER,
            category_id=transfer_category.id,
            transaction_date=data.transaction_date,
        )

        _apply_balance_effect(from_account, TransactionType.TRANSFER, out_transaction.amount)
        _apply_balance_effect(to_account, TransactionType.TRANSFER, in_transaction.amount)

        session.add_all([out_transaction, in_transaction, from_account, to_account])
        await session.commit()
        return {"received": received_amount}

    @staticmethod
    async def create_transaction(
        session: AsyncSession,
        data: TransactionCreate,
        current_user: User,
    ) -> Transaction:
        account = await get_account_for_user(session, data.account_id, current_user.id, lock=True)
        if not account:
            raise NotFoundError("Гаманець не знайдено")

        category = await get_accessible_category(session, data.category_id, current_user.id)
        if not category:
            raise ValidationError("Категорія не знайдена")

        transaction = Transaction(**data.model_dump(), user_id=current_user.id)
        _apply_balance_effect(account, transaction.type, transaction.amount)

        session.add_all([transaction, account])
        await session.commit()
        await session.refresh(transaction)
        return transaction

    @staticmethod
    async def list_transactions(
        session: AsyncSession,
        current_user: User,
        *,
        month: int,
        year: int,
        category_id: Optional[int],
        transaction_type: Optional[TransactionType],
        offset: int,
        limit: int,
    ) -> dict[str, object]:
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == current_user.id)
            .options(joinedload(Transaction.category))
            .where(extract("month", Transaction.transaction_date) == month)
            .where(extract("year", Transaction.transaction_date) == year)
            .order_by(Transaction.transaction_date.desc())
        )

        if category_id is not None:
            stmt = stmt.where(Transaction.category_id == category_id)
        if transaction_type is not None:
            stmt = stmt.where(Transaction.type == transaction_type)

        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        return {
            "transactions": transactions,
            "next_offset": offset + limit if len(transactions) == limit else None,
        }

    @staticmethod
    async def get_transaction(
        session: AsyncSession,
        transaction_id: int,
        current_user: User,
    ) -> Transaction:
        transaction = await get_transaction_for_user(session, transaction_id, current_user.id)
        if not transaction:
            raise NotFoundError("Транзакція не знайдена або вона вам не належить")
        return transaction

    @staticmethod
    async def delete_transaction(
        session: AsyncSession,
        transaction_id: int,
        current_user: User,
    ) -> None:
        transaction = await get_transaction_for_user(
            session,
            transaction_id,
            current_user.id,
            lock=True,
        )
        if not transaction:
            raise NotFoundError("Транзакцію не знайдено")

        account = await get_account_for_user(
            session,
            transaction.account_id,
            current_user.id,
            lock=True,
        )
        if account:
            _apply_balance_effect(account, transaction.type, transaction.amount, reverse=True)
            session.add(account)

        await session.delete(transaction)
        await session.commit()

    @staticmethod
    async def update_transaction(
        session: AsyncSession,
        transaction_id: int,
        data: TransactionCreate,
        current_user: User,
    ) -> Transaction:
        transaction = await get_transaction_for_user(
            session,
            transaction_id,
            current_user.id,
            lock=True,
        )
        if not transaction:
            raise NotFoundError("Транзакцію не знайдено")

        category = await get_accessible_category(session, data.category_id, current_user.id)
        if not category:
            raise ValidationError("Категорія не знайдена")

        old_account = await get_account_for_user(
            session,
            transaction.account_id,
            current_user.id,
            lock=True,
        )
        new_account = await get_account_for_user(
            session, data.account_id, current_user.id, lock=True
        )
        if not new_account:
            raise ValidationError("Цільовий гаманець не знайдено")

        if old_account:
            _apply_balance_effect(old_account, transaction.type, transaction.amount, reverse=True)
            session.add(old_account)

        _apply_balance_effect(new_account, data.type, data.amount)
        session.add(new_account)

        for key, value in data.model_dump().items():
            setattr(transaction, key, value)

        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)
        return transaction
