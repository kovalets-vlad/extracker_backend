from collections.abc import Mapping
from http import HTTPStatus


class AppError(Exception):
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, detail: str, headers: Mapping[str, str] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.headers = dict(headers or {})


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND


class ConflictError(AppError):
    status_code = HTTPStatus.BAD_REQUEST


class ValidationError(AppError):
    status_code = HTTPStatus.BAD_REQUEST


class AuthenticationError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED

    def __init__(self, detail: str) -> None:
        super().__init__(detail, headers={"WWW-Authenticate": "Bearer"})


class SystemStateError(AppError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
