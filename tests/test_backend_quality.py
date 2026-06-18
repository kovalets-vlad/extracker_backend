from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.constants.category import DefaultCategory
from app.core.constants.currency import CurrencyCode
from app.models.category import Category
from app.models.currency import Currency
from app.services.category_service import seed_default_categories
from app.services.currency_service import seed_currencies


async def _currency_id(session_factory, code: CurrencyCode) -> int:
    async with session_factory() as session:
        result = await session.execute(select(Currency.id).where(Currency.code == code))
        return result.scalar_one()


async def _category_id(session_factory, name: str) -> int:
    async with session_factory() as session:
        result = await session.execute(select(Category.id).where(Category.name == name))
        return result.scalar_one()


async def _default_account_id(client: AsyncClient, headers: dict[str, str]) -> int:
    response = await client.get("/accounts/", headers=headers)
    assert response.status_code == 200
    return response.json()[0]["id"]


async def _account_balance(
    client: AsyncClient, headers: dict[str, str], account_id: int
) -> Decimal:
    response = await client.get("/accounts/", headers=headers)
    assert response.status_code == 200
    accounts = {account["id"]: Decimal(str(account["balance"])) for account in response.json()}
    return accounts[account_id]


async def test_auth_register_duplicate_login_and_invalid_token(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={"email": "auth@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "auth@example.com"
    assert "password" not in response.json()

    duplicate = await client.post(
        "/auth/register",
        json={"email": "auth@example.com", "password": "password123"},
    )
    assert duplicate.status_code == 400

    login = await client.post(
        "/auth/login",
        data={"username": "auth@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["access_token"]

    invalid_auth = await client.get(
        "/accounts/",
        headers={"Authorization": "Bearer definitely-invalid"},
    )
    assert invalid_auth.status_code == 401


async def test_accounts_accept_legacy_currency_alias_and_list_only_owner(
    client: AsyncClient,
    auth_headers: dict[str, str],
    session_factory,
):
    eur_id = await _currency_id(session_factory, CurrencyCode.EUR)
    response = await client.post(
        "/accounts/",
        json={"name": "Euro Wallet", "currency_code_id": eur_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["account"]["currency_id"] == eur_id

    await client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "password123"},
    )
    other_login = await client.post(
        "/auth/login",
        data={"username": "other@example.com", "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    owner_accounts = await client.get("/accounts/", headers=auth_headers)
    other_accounts = await client.get("/accounts/", headers=other_headers)

    assert len(owner_accounts.json()) == 2
    assert len(other_accounts.json()) == 1


async def test_transaction_create_update_delete_reverses_balances(
    client: AsyncClient,
    auth_headers: dict[str, str],
    session_factory,
):
    account_id = await _default_account_id(client, auth_headers)
    salary_id = await _category_id(session_factory, DefaultCategory.SALARY.value)
    food_id = await _category_id(session_factory, DefaultCategory.FOOD.value)

    income = await client.post(
        "/transactions/",
        json={
            "amount": "1000.00",
            "category_id": salary_id,
            "account_id": account_id,
            "type": "income",
        },
        headers=auth_headers,
    )
    assert income.status_code == 201
    assert await _account_balance(client, auth_headers, account_id) == Decimal("1000.00")

    expense = await client.post(
        "/transactions/",
        json={
            "amount": "100.00",
            "category_id": food_id,
            "account_id": account_id,
            "type": "expense",
        },
        headers=auth_headers,
    )
    assert expense.status_code == 201
    expense_id = expense.json()["transaction"]["id"]
    assert await _account_balance(client, auth_headers, account_id) == Decimal("900.00")

    updated = await client.put(
        f"/transactions/{expense_id}",
        json={
            "amount": "150.00",
            "category_id": food_id,
            "account_id": account_id,
            "type": "expense",
        },
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert await _account_balance(client, auth_headers, account_id) == Decimal("850.00")

    deleted = await client.delete(f"/transactions/{expense_id}", headers=auth_headers)
    assert deleted.status_code == 200
    assert await _account_balance(client, auth_headers, account_id) == Decimal("1000.00")


async def test_transfer_validates_accounts_and_updates_balances(
    client: AsyncClient,
    auth_headers: dict[str, str],
    session_factory,
):
    uah_id = await _currency_id(session_factory, CurrencyCode.UAH)
    from_account_id = await _default_account_id(client, auth_headers)
    created = await client.post(
        "/accounts/",
        json={"name": "Savings", "currency_id": uah_id},
        headers=auth_headers,
    )
    to_account_id = created.json()["account"]["id"]

    invalid = await client.post(
        "/transactions/transfer",
        json={
            "from_account_id": from_account_id,
            "to_account_id": from_account_id,
            "amount": "10.00",
        },
        headers=auth_headers,
    )
    assert invalid.status_code == 422

    transfer = await client.post(
        "/transactions/transfer",
        json={
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": "40.00",
        },
        headers=auth_headers,
    )
    assert transfer.status_code == 200
    assert await _account_balance(client, auth_headers, from_account_id) == Decimal("-40.00")
    assert await _account_balance(client, auth_headers, to_account_id) == Decimal("40.00")


async def test_analytics_budget_and_category_summary_enforce_ownership(
    client: AsyncClient,
    auth_headers: dict[str, str],
    session_factory,
):
    account_id = await _default_account_id(client, auth_headers)
    salary_id = await _category_id(session_factory, DefaultCategory.SALARY.value)
    food_id = await _category_id(session_factory, DefaultCategory.FOOD.value)

    await client.post(
        "/transactions/",
        json={
            "amount": "500.00",
            "category_id": salary_id,
            "account_id": account_id,
            "type": "income",
        },
        headers=auth_headers,
    )
    await client.post(
        "/transactions/",
        json={
            "amount": "50.00",
            "category_id": food_id,
            "account_id": account_id,
            "type": "expense",
        },
        headers=auth_headers,
    )

    budget = await client.get("/analytics/budget?base_currency=UAH", headers=auth_headers)
    assert budget.status_code == 200
    assert budget.json()["status"] == "success"
    assert budget.json()["data"]["total_income"] == 500.0

    summary = await client.get(
        f"/analytics/categories-summary?account_id={account_id}",
        headers=auth_headers,
    )
    assert summary.status_code == 200
    assert summary.json()[0]["spent"] == "50.00"

    await client.post(
        "/auth/register",
        json={"email": "analytics-other@example.com", "password": "password123"},
    )
    other_login = await client.post(
        "/auth/login",
        data={"username": "analytics-other@example.com", "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    forbidden_summary = await client.get(
        f"/analytics/categories-summary?account_id={account_id}",
        headers=other_headers,
    )
    assert forbidden_summary.status_code == 404


async def test_seed_services_are_idempotent(session_factory):
    async with session_factory() as session:
        before_currencies = await session.scalar(select(func.count(Currency.id)))
        before_categories = await session.scalar(select(func.count(Category.id)))

        await seed_currencies(session)
        await seed_default_categories(session)

        after_currencies = await session.scalar(select(func.count(Currency.id)))
        after_categories = await session.scalar(select(func.count(Category.id)))

    assert before_currencies == after_currencies
    assert before_categories == after_categories
