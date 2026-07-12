from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidTransaction,
    TransactionNotFound,
    UserNotFound,
)
from app.core.logger import logger
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
)


class TransactionService:
    """Business logic for transaction operations."""

    @staticmethod
    def create_transaction(
        db: Session,
        transaction: TransactionCreate,
    ) -> TransactionResponse:
        """Create a transaction after business validation checks."""
        if transaction.amount <= 0:
            logger.error(
                "Transaction creation failed | invalid amount=%s",
                transaction.amount,
            )
            raise InvalidTransaction()

        if transaction.transaction_date > date.today():
            logger.error(
                "Transaction creation failed | transaction_date=%s is in future",
                transaction.transaction_date,
            )
            raise InvalidTransaction()

        user = UserRepository.get_by_id(db, transaction.user_id)
        if user is None:
            logger.error(
                "Transaction creation failed | user_id=%s not found",
                transaction.user_id,
            )
            raise UserNotFound()

        transaction_data = transaction.model_dump()
        transaction_data["transaction_type"] = (
            transaction.transaction_type.value
        )
        created_transaction = TransactionRepository.create(
            db,
            transaction_data,
        )
        logger.info(
            "Transaction Created | transaction_id=%s user_id=%s",
            created_transaction.id,
            created_transaction.user_id,
        )
        return TransactionResponse.model_validate(created_transaction)

    @staticmethod
    def get_transactions(db: Session) -> list[TransactionResponse]:
        """Fetch transactions as response schemas."""
        transactions = TransactionRepository.get_all(db)
        logger.info("Transaction Fetch | count=%s", len(transactions))
        return [
            TransactionResponse.model_validate(transaction)
            for transaction in transactions
        ]

    @staticmethod
    def get_transaction_by_id(
        db: Session,
        transaction_id: int,
    ) -> TransactionResponse:
        """Fetch one transaction by id with domain-level not-found handling."""
        transaction = TransactionRepository.get_by_id(
            db,
            transaction_id,
        )
        if transaction is None:
            logger.error(
                "Transaction fetch failed | transaction_id=%s not found",
                transaction_id,
            )
            raise TransactionNotFound()

        logger.info("Transaction Fetch | transaction_id=%s", transaction_id)
        return TransactionResponse.model_validate(transaction)