from datetime import date, datetime, timedelta
from calendar import monthrange

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
    def get_todays_transactions_for_telegram_user(
        db: Session,
        telegram_id: str,
    ) -> list[TransactionResponse]:
        """Fetch today's transactions for a Telegram user."""
        user = UserRepository.get_by_telegram_id(db, telegram_id)
        if user is None:
            logger.info(
                "Today's transaction fetch | telegram_id=%s user not found",
                telegram_id,
            )
            return []

        transactions = TransactionRepository.get_by_user_and_date(
            db,
            user.id,
            date.today(),
        )
        logger.info(
            "Today's transaction fetch | telegram_id=%s user_id=%s count=%s",
            telegram_id,
            user.id,
            len(transactions),
        )
        return [
            TransactionResponse.model_validate(transaction)
            for transaction in transactions
        ]

    @staticmethod
    def get_todays_transactions_for_user(
        db: Session,
        user_id: int,
    ) -> list[TransactionResponse]:
        transactions = TransactionRepository.get_by_user_and_date(
            db,
            user_id,
            date.today(),
        )
        return [
            TransactionResponse.model_validate(transaction)
            for transaction in transactions
        ]

    @staticmethod
    def get_transactions_for_last_7_days(
        db: Session,
        telegram_id: str,
    ) -> list[TransactionResponse]:
        user = UserRepository.get_by_telegram_id(db, telegram_id)
        if user is None:
            logger.info(
                "Weekly transaction fetch | telegram_id=%s user not found",
                telegram_id,
            )
            return []

        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        transactions = TransactionRepository.get_by_user_and_date_range(
            db,
            user.id,
            start_date,
            end_date,
        )
        logger.info(
            "Weekly transaction fetch | telegram_id=%s user_id=%s count=%s",
            telegram_id,
            user.id,
            len(transactions),
        )
        return [
            TransactionResponse.model_validate(transaction)
            for transaction in transactions
        ]

    @staticmethod
    def get_transactions_for_current_month(
        db: Session,
        telegram_id: str,
    ) -> list[TransactionResponse]:
        user = UserRepository.get_by_telegram_id(db, telegram_id)
        if user is None:
            logger.info(
                "Monthly transaction fetch | telegram_id=%s user not found",
                telegram_id,
            )
            return []

        today = date.today()
        start_date = today.replace(day=1)
        end_date = today.replace(day=monthrange(today.year, today.month)[1])
        transactions = TransactionRepository.get_by_user_and_date_range(
            db,
            user.id,
            start_date,
            end_date,
        )
        logger.info(
            "Monthly transaction fetch | telegram_id=%s user_id=%s count=%s",
            telegram_id,
            user.id,
            len(transactions),
        )
        return [
            TransactionResponse.model_validate(transaction)
            for transaction in transactions
        ]

    @staticmethod
    def get_all_transactions_for_telegram_user(
        db: Session,
        telegram_id: str,
    ) -> list[TransactionResponse]:
        user = UserRepository.get_by_telegram_id(db, telegram_id)
        if user is None:
            logger.info(
                "Overall transaction fetch | telegram_id=%s user not found",
                telegram_id,
            )
            return []

        transactions = TransactionRepository.get_by_user(db, user.id)
        logger.info(
            "Overall transaction fetch | telegram_id=%s user_id=%s count=%s",
            telegram_id,
            user.id,
            len(transactions),
        )
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