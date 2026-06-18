"""Initial schema.

Revision ID: 20260618_0001
Revises:
Create Date: 2026-06-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260618_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "currencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_currencies_code", "currencies", ["code"])

    op.create_table(
        "exchange_rates",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("rate_to_usd", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("currency_id", sa.Integer(), nullable=True),
        sa.Column("target_essential", sa.Float(), nullable=False),
        sa.Column("target_wants", sa.Float(), nullable=False),
        sa.Column("target_savings", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["currency_id"], ["currencies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("group", sa.String(length=9), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("balance", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("currency_id", sa.Integer(), nullable=False),
        sa.Column("monthly_limit", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.ForeignKeyConstraint(["currency_id"], ["currencies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounts_currency_id", "accounts", ["currency_id"])
    op.create_index("ix_accounts_name", "accounts", ["name"])
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=6), nullable=False),
        sa.Column("type", sa.String(length=8), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])
    op.create_index("ix_transactions_transaction_date", "transactions", ["transaction_date"])
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

    op.create_table(
        "recurring_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("type", sa.String(length=8), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("last_executed_at", sa.Date(), nullable=True),
        sa.Column("is_calendar_monthly", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recurring_transactions_user_id", "recurring_transactions", ["user_id"])

    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("raw_ocr_output", sa.JSON(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_receipts_user_id", "receipts", ["user_id"])

    op.create_table(
        "user_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("monthly_limit", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "category_id", name="unique_user_category"),
    )
    op.create_index("ix_user_categories_category_id", "user_categories", ["category_id"])
    op.create_index("ix_user_categories_user_id", "user_categories", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_categories_user_id", table_name="user_categories")
    op.drop_index("ix_user_categories_category_id", table_name="user_categories")
    op.drop_table("user_categories")
    op.drop_index("ix_receipts_user_id", table_name="receipts")
    op.drop_table("receipts")
    op.drop_index("ix_recurring_transactions_user_id", table_name="recurring_transactions")
    op.drop_table("recurring_transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_index("ix_transactions_transaction_date", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_accounts_user_id", table_name="accounts")
    op.drop_index("ix_accounts_name", table_name="accounts")
    op.drop_index("ix_accounts_currency_id", table_name="accounts")
    op.drop_table("accounts")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("exchange_rates")
    op.drop_index("ix_currencies_code", table_name="currencies")
    op.drop_table("currencies")
