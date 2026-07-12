"""FastAPI exception handlers for custom Ledgerly exceptions."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    InvalidTransaction,
    TransactionNotFound,
    UserAlreadyExists,
    UserNotFound,
)


async def user_already_exists_handler(
    request: Request,
    exc: UserAlreadyExists,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"message": "User already exists"},
    )


async def user_not_found_handler(
    request: Request,
    exc: UserNotFound,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"message": "User not found"},
    )


async def transaction_not_found_handler(
    request: Request,
    exc: TransactionNotFound,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"message": "Transaction not found"},
    )


async def invalid_transaction_handler(
    request: Request,
    exc: InvalidTransaction,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"message": "Invalid transaction"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the app instance."""
    app.add_exception_handler(
        UserAlreadyExists,
        user_already_exists_handler,
    )
    app.add_exception_handler(
        UserNotFound,
        user_not_found_handler,
    )
    app.add_exception_handler(
        TransactionNotFound,
        transaction_not_found_handler,
    )
    app.add_exception_handler(
        InvalidTransaction,
        invalid_transaction_handler,
    )
