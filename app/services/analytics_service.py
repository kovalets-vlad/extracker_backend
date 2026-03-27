from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, extract
from sqlalchemy.orm import joinedload
from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.models.user import User
from app.models.exchange_rate import ExchangeRate
from app.core.constants.category import CategoryGroup

class AnalyticsService:
    @staticmethod
    async def get_budget_with_trends(
        session: AsyncSession, 
        user: User, 
        month: int, 
        year: int,
        base_currency: str = "UAH"
    ) -> Dict[str, Any]:
        
        current_report = await AnalyticsService.get_monthly_60_20_20_report(
            session, user, month, year, base_currency
        )
        
        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year
        
        prev_report = await AnalyticsService.get_monthly_60_20_20_report(
            session, user, prev_month, prev_year, base_currency
        )
        
        def calc_trend(curr: float, prev: float) -> str:
            if prev == 0:
                return "+100.0%" if curr > 0 else "0.0%"
            
            diff = ((curr - prev) / prev) * 100
            sign = "+" if diff > 0 else ""
            return f"{sign}{diff:.1f}%"
            
        trends = {
            "income_diff": calc_trend(
                current_report["total_income"], 
                prev_report["total_income"]
            ),
            "essential_diff": calc_trend(
                current_report["breakdown"]["essential"]["amount"], 
                prev_report["breakdown"]["essential"]["amount"]
            ),
            "wants_diff": calc_trend(
                current_report["breakdown"]["wants"]["amount"], 
                prev_report["breakdown"]["wants"]["amount"]
            ),
            "savings_diff": calc_trend(
                current_report["breakdown"]["savings"]["amount"], 
                prev_report["breakdown"]["savings"]["amount"]
            )
        }
        
        current_report["trends"] = trends
        
        return current_report
    
    @staticmethod
    async def get_monthly_60_20_20_report(
        session: AsyncSession, 
        user: User, 
        month: int, 
        year: int,
        base_currency: str = "UAH" 
    ) -> Dict[str, Any]:
        
        rates_result = await session.execute(select(ExchangeRate))
        rates = {r.code: r.rate_to_usd for r in rates_result.scalars().all()}
        rates["USD"] = Decimal("1.0")

        stmt = (
            select(Transaction)
            .where(
                (Transaction.user_id == user.id) &
                (extract('month', Transaction.transaction_date) == month) &
                (extract('year', Transaction.transaction_date) == year)
            )
            .options(
                joinedload(Transaction.category),
                joinedload(Transaction.account).joinedload(Account.currency)
            )
        )
        
        transactions = (await session.execute(stmt)).scalars().all()

        totals = {
            CategoryGroup.INCOME: Decimal("0"),
            CategoryGroup.ESSENTIAL: Decimal("0"),
            CategoryGroup.WANTS: Decimal("0"),
            CategoryGroup.SAVINGS: Decimal("0"),
            CategoryGroup.OTHER: Decimal("0")
        }

        def convert_to_base(amount: Decimal, currency_code: str) -> Decimal:
            if currency_code == base_currency:
                return amount
            
            amount_in_usd = amount / rates.get(currency_code, Decimal("1.0"))
            amount_in_base = amount_in_usd * rates.get(base_currency, Decimal("1.0"))
            return amount_in_base.quantize(Decimal("0.01"))

        for t in transactions:
            if t.type == TransactionType.TRANSFER:
                continue
                
            currency_code = t.account.currency.code
            normalized_amount = convert_to_base(abs(t.amount), currency_code)
            
            group = t.category.group if t.category else CategoryGroup.OTHER
            
            if t.type == TransactionType.INCOME:
                totals[CategoryGroup.INCOME] += normalized_amount
            else:
                if group in totals:
                    totals[group] += normalized_amount
                else:
                    totals[CategoryGroup.OTHER] += normalized_amount

        income = totals[CategoryGroup.INCOME]
        def get_percent(amount: Decimal) -> float:
            return float((amount / income * 100).quantize(Decimal("0.1"))) if income > 0 else 0.0

        return {
            "period": f"{month:02d}/{year}",
            "base_currency": base_currency,
            "total_income": float(income),
            "breakdown": {
                "essential": {
                    "amount": float(totals[CategoryGroup.ESSENTIAL]),
                    "percent": get_percent(totals[CategoryGroup.ESSENTIAL]),
                    "target_percent": user.target_essential, 
                    "status": "overbudget" if get_percent(totals[CategoryGroup.ESSENTIAL]) > user.target_essential else "ok"
                },
                "wants": {
                    "amount": float(totals[CategoryGroup.WANTS]),
                    "percent": get_percent(totals[CategoryGroup.WANTS]),
                    "target_percent": user.target_wants, 
                    "status": "overbudget" if get_percent(totals[CategoryGroup.WANTS]) > user.target_wants else "ok"
                },
                "savings": {
                    "amount": float(totals[CategoryGroup.SAVINGS]),
                    "percent": get_percent(totals[CategoryGroup.SAVINGS]),
                    "target_percent": user.target_savings, 
                    "status": "underfunded" if get_percent(totals[CategoryGroup.SAVINGS]) < user.target_savings else "ok"
                },
                "other": {
                    "amount": float(totals[CategoryGroup.OTHER]),
                    "percent": get_percent(totals[CategoryGroup.OTHER]),
                    "target_percent": 0.0, 
                    "status": "warning" if totals[CategoryGroup.OTHER] > 0 else "ok"
                }
            }
        }