from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.constants.category import CategoryGroup
from app.core.exceptions import NotFoundError, ValidationError
from app.models.account import Account
from app.models.category import Category
from app.models.exchange_rate import ExchangeRate
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.user_category import UserCategory


def _month_bounds(month: int, year: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start, end


def _normalize_code(code: object) -> str:
    return getattr(code, "value", str(code))


class AnalyticsService:
    @staticmethod
    async def get_dashboard_data(
        session: AsyncSession,
        user: User,
        account_id: int,
        month: int,
        year: int,
    ) -> dict[str, Any]:
        account_result = await session.execute(
            select(Account)
            .where(Account.id == account_id, Account.user_id == user.id)
            .options(joinedload(Account.currency))
        )
        account = account_result.scalars().first()
        if not account:
            raise NotFoundError("Гаманець не знайдено")

        start_of_month, start_of_next_month = _month_bounds(month, year)
        stmt = (
            select(Transaction.type, func.sum(Transaction.amount).label("total"))
            .where(Transaction.account_id == account_id)
            .where(Transaction.user_id == user.id)
            .where(Transaction.transaction_date >= start_of_month)
            .where(Transaction.transaction_date < start_of_next_month)
            .group_by(Transaction.type)
        )

        result = await session.execute(stmt)
        totals = {TransactionType(row[0]): row[1] or Decimal("0") for row in result.all()}
        income = totals.get(TransactionType.INCOME, Decimal("0"))
        expense = totals.get(TransactionType.EXPENSE, Decimal("0"))
        transfers = totals.get(TransactionType.TRANSFER, Decimal("0"))

        return {
            "account_name": account.name,
            "current_balance": account.balance,
            "currency": _normalize_code(account.currency.code) if account.currency else "",
            "monthly_summary": {
                "income": income,
                "expense": expense,
                "transfers": transfers,
                "net_change": income - expense + transfers,
            },
        }

    @staticmethod
    async def get_categories_summary(
        session: AsyncSession,
        user: User,
        account_id: int,
    ) -> list[dict[str, Any]]:
        account = await session.get(Account, account_id)
        if not account or account.user_id != user.id:
            raise NotFoundError("Гаманець не знайдено")

        stmt = (
            select(
                Category.name,
                func.sum(Transaction.amount).label("spent"),
                UserCategory.monthly_limit,
            )
            .join(Category, Transaction.category_id == Category.id)
            .outerjoin(
                UserCategory,
                (UserCategory.category_id == Category.id) & (UserCategory.user_id == user.id),
            )
            .where(Transaction.account_id == account_id)
            .where(Transaction.user_id == user.id)
            .where(Transaction.type == TransactionType.EXPENSE)
            .group_by(Category.name, UserCategory.monthly_limit)
        )

        result = await session.execute(stmt)
        summary = []
        for name, spent, limit in result.all():
            spent_abs = abs(spent or Decimal("0"))
            limit_value = limit or Decimal("0")
            summary.append(
                {
                    "category": name,
                    "spent": spent_abs,
                    "limit": limit_value,
                    "remaining": (limit_value - spent_abs) if limit else None,
                    "overspent": spent_abs > limit_value if limit else False,
                }
            )

        return summary

    @staticmethod
    async def get_budget_with_trends(
        session: AsyncSession,
        user: User,
        month: int,
        year: int,
        base_currency: str = "UAH",
    ) -> dict[str, Any]:
        current_report = await AnalyticsService.get_monthly_60_20_20_report(
            session,
            user,
            month,
            year,
            base_currency,
        )

        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year
        prev_report = await AnalyticsService.get_monthly_60_20_20_report(
            session,
            user,
            prev_month,
            prev_year,
            base_currency,
        )

        def calc_trend(curr: float, prev: float) -> str:
            if prev == 0:
                return "+100.0%" if curr > 0 else "0.0%"

            diff = ((curr - prev) / prev) * 100
            sign = "+" if diff > 0 else ""
            return f"{sign}{diff:.1f}%"

        current_report["trends"] = {
            "income_diff": calc_trend(
                current_report["total_income"],
                prev_report["total_income"],
            ),
            "essential_diff": calc_trend(
                current_report["breakdown"]["essential"]["amount"],
                prev_report["breakdown"]["essential"]["amount"],
            ),
            "wants_diff": calc_trend(
                current_report["breakdown"]["wants"]["amount"],
                prev_report["breakdown"]["wants"]["amount"],
            ),
            "savings_diff": calc_trend(
                current_report["breakdown"]["savings"]["amount"],
                prev_report["breakdown"]["savings"]["amount"],
            ),
        }
        return current_report

    @staticmethod
    async def get_monthly_60_20_20_report(
        session: AsyncSession,
        user: User,
        month: int,
        year: int,
        base_currency: str = "UAH",
    ) -> dict[str, Any]:
        base_currency = base_currency.upper()
        rates_result = await session.execute(select(ExchangeRate))
        rates = {rate.code: rate.rate_to_usd for rate in rates_result.scalars().all()}
        rates["USD"] = Decimal("1.0")

        stmt = (
            select(Transaction)
            .where(
                (Transaction.user_id == user.id)
                & (extract("month", Transaction.transaction_date) == month)
                & (extract("year", Transaction.transaction_date) == year)
            )
            .options(
                joinedload(Transaction.category),
                joinedload(Transaction.account).joinedload(Account.currency),
            )
        )
        transactions = (await session.execute(stmt)).scalars().all()

        required_codes = {
            _normalize_code(transaction.account.currency.code)
            for transaction in transactions
            if transaction.account and transaction.account.currency
        }
        required_codes.add(base_currency)
        missing_codes = {code for code in required_codes if code not in rates}
        if missing_codes:
            raise ValidationError(f"Missing exchange rates for: {', '.join(sorted(missing_codes))}")

        totals = {
            CategoryGroup.INCOME: Decimal("0"),
            CategoryGroup.ESSENTIAL: Decimal("0"),
            CategoryGroup.WANTS: Decimal("0"),
            CategoryGroup.SAVINGS: Decimal("0"),
            CategoryGroup.OTHER: Decimal("0"),
        }

        def convert_to_base(amount: Decimal, currency_code: str) -> Decimal:
            if currency_code == base_currency:
                return amount

            amount_in_usd = amount / rates[currency_code]
            amount_in_base = amount_in_usd * rates[base_currency]
            return amount_in_base.quantize(Decimal("0.01"))

        for transaction in transactions:
            if transaction.type == TransactionType.TRANSFER:
                continue

            currency_code = _normalize_code(transaction.account.currency.code)
            normalized_amount = convert_to_base(abs(transaction.amount), currency_code)
            group = (
                CategoryGroup(transaction.category.group)
                if transaction.category
                else CategoryGroup.OTHER
            )

            if transaction.type == TransactionType.INCOME:
                totals[CategoryGroup.INCOME] += normalized_amount
            elif group in totals:
                totals[group] += normalized_amount
            else:
                totals[CategoryGroup.OTHER] += normalized_amount

        income = totals[CategoryGroup.INCOME]
        total_expense = (
            totals[CategoryGroup.ESSENTIAL]
            + totals[CategoryGroup.WANTS]
            + totals[CategoryGroup.SAVINGS]
            + totals[CategoryGroup.OTHER]
        )

        def get_percent_of_income(amount: Decimal) -> float:
            if income == 0:
                return 0.0
            return float((amount / income * 100).quantize(Decimal("0.1")))

        def get_percent_of_expense(amount: Decimal) -> float:
            if total_expense == 0:
                return 0.0
            return float((amount / total_expense * 100).quantize(Decimal("0.1")))

        return {
            "period": f"{month:02d}/{year}",
            "base_currency": base_currency,
            "total_income": float(income),
            "total_expense": float(total_expense),
            "breakdown": {
                "essential": {
                    "amount": float(totals[CategoryGroup.ESSENTIAL]),
                    "percent_of_income": get_percent_of_income(totals[CategoryGroup.ESSENTIAL]),
                    "percent_of_expense": get_percent_of_expense(totals[CategoryGroup.ESSENTIAL]),
                    "target_percent": user.target_essential,
                    "status": (
                        "overbudget"
                        if get_percent_of_income(totals[CategoryGroup.ESSENTIAL])
                        > user.target_essential
                        else "ok"
                    ),
                },
                "wants": {
                    "amount": float(totals[CategoryGroup.WANTS]),
                    "percent_of_income": get_percent_of_income(totals[CategoryGroup.WANTS]),
                    "percent_of_expense": get_percent_of_expense(totals[CategoryGroup.WANTS]),
                    "target_percent": user.target_wants,
                    "status": (
                        "overbudget"
                        if get_percent_of_income(totals[CategoryGroup.WANTS]) > user.target_wants
                        else "ok"
                    ),
                },
                "savings": {
                    "amount": float(totals[CategoryGroup.SAVINGS]),
                    "percent_of_income": get_percent_of_income(totals[CategoryGroup.SAVINGS]),
                    "percent_of_expense": get_percent_of_expense(totals[CategoryGroup.SAVINGS]),
                    "target_percent": user.target_savings,
                    "status": (
                        "underfunded"
                        if get_percent_of_income(totals[CategoryGroup.SAVINGS])
                        < user.target_savings
                        else "ok"
                    ),
                },
                "other": {
                    "amount": float(totals[CategoryGroup.OTHER]),
                    "percent_of_income": get_percent_of_income(totals[CategoryGroup.OTHER]),
                    "percent_of_expense": get_percent_of_expense(totals[CategoryGroup.OTHER]),
                    "target_percent": 0.0,
                    "status": "warning" if totals[CategoryGroup.OTHER] > 0 else "ok",
                },
            },
        }
