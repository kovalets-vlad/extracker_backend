import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.accounts import router as accounts_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.category import router as category_router
from app.api.exception_handlers import app_error_handler
from app.api.exchange_rate import router as exchange_rate_router
from app.api.recurring_transaction import router as recurring_transaction_router
from app.api.transactions import router as transaction_router
from app.api.users import router as users_router
from app.core.config import settings
from app.core.db import get_session_context
from app.core.exceptions import AppError
from app.services.category_service import seed_default_categories
from app.services.currency_service import seed_currencies
from app.services.exchange_rate_service import auto_update_exchange_rates

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.LOG_LEVEL.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def create_lifespan(run_startup_tasks: bool):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()

        if run_startup_tasks and settings.RUN_STARTUP_SEEDS:
            async with get_session_context() as session:
                await seed_currencies(session)
                await auto_update_exchange_rates(session)
                await seed_default_categories(session)

        logger.info("Backend application is ready")
        yield

    return lifespan


def create_app(run_startup_tasks: bool = True) -> FastAPI:
    app = FastAPI(lifespan=create_lifespan(run_startup_tasks))

    app.add_exception_handler(AppError, app_error_handler)

    app.include_router(auth_router)
    app.include_router(transaction_router)
    app.include_router(accounts_router)
    app.include_router(exchange_rate_router)
    app.include_router(recurring_transaction_router)
    app.include_router(analytics_router)
    app.include_router(category_router)
    app.include_router(users_router)

    return app


app = create_app()
