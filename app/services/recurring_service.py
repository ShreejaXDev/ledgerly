from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.repositories.recurring_repository import RecurringRepository
from app.repositories.user_repository import UserRepository
from app.schemas.bot import TelegramMessage
from app.schemas.recurring import RecurringCreate, RecurringResponse
from app.schemas.transaction import TransactionCreate, TransactionType
from app.schemas.user import UserCreate
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService


class RecurringService:
    @staticmethod
    def _get_or_create_user(db: Session, payload: TelegramMessage):
        user = UserRepository.get_by_telegram_id(db, payload.telegram_id)
        if user is not None:
            return user

        logger.info(
            "Recurring user missing | telegram_id=%s registering automatically",
            payload.telegram_id,
        )
        user_data = UserCreate(
            telegram_id=payload.telegram_id,
            username=payload.username or "unknown",
            first_name=payload.first_name,
        )
        UserService.create_user(db, user_data)
        return UserRepository.get_by_telegram_id(db, payload.telegram_id)

    @staticmethod
    def _advance_date(current_date: date, frequency: str) -> date:
        if frequency == "daily":
            return current_date + timedelta(days=1)
        if frequency == "weekly":
            return current_date + timedelta(days=7)
        if frequency == "monthly":
            next_month = current_date.month + 1
            year = current_date.year
            if next_month > 12:
                next_month = 1
                year += 1
            last_day = monthrange(year, next_month)[1]
            return date(year, next_month, min(current_date.day, last_day))
        if frequency == "yearly":
            year = current_date.year + 1
            last_day = monthrange(year, current_date.month)[1]
            return date(year, current_date.month, min(current_date.day, last_day))

        raise ValueError(f"Unsupported frequency: {frequency}")

    @staticmethod
    def create_recurring(
        db: Session,
        payload: TelegramMessage,
        recurring: RecurringCreate,
    ) -> RecurringResponse:
        user = RecurringService._get_or_create_user(db, payload)

        recurring_data = recurring.model_dump()
        recurring_data["user_id"] = user.id
        recurring_data["transaction_type"] = recurring.transaction_type.value
        recurring_data["frequency"] = recurring.frequency.value

        created_recurring = RecurringRepository.create(db, recurring_data)
        logger.info(
            "Recurring created | recurring_id=%s user_id=%s frequency=%s",
            created_recurring.id,
            created_recurring.user_id,
            created_recurring.frequency,
        )
        return RecurringResponse.model_validate(created_recurring)

    @staticmethod
    def list_recurring(
        db: Session,
        payload: TelegramMessage,
    ) -> list[RecurringResponse]:
        user = RecurringService._get_or_create_user(db, payload)
        recurring_items = RecurringRepository.get_by_user_id(db, user.id)
        return [
            RecurringResponse.model_validate(item)
            for item in recurring_items
        ]

    @staticmethod
    def delete_recurring(
        db: Session,
        payload: TelegramMessage,
        recurring_id: int,
    ) -> bool:
        user = RecurringService._get_or_create_user(db, payload)
        recurring = RecurringRepository.get_by_id(db, recurring_id)
        if recurring is None or recurring.user_id != user.id:
            logger.warning(
                "Recurring delete failed | telegram_id=%s recurring_id=%s not found",
                payload.telegram_id,
                recurring_id,
            )
            return False

        RecurringRepository.delete(db, recurring)
        logger.info(
            "Recurring deleted | recurring_id=%s user_id=%s",
            recurring_id,
            user.id,
        )
        return True

    @staticmethod
    def process_due_recurring_transactions(
        db: Session,
        current_date: date | None = None,
    ) -> list[int]:
        run_date = current_date or date.today()
        due_items = RecurringRepository.get_due_recurring_transactions(db, run_date)
        created_transaction_ids: list[int] = []

        for recurring in due_items:
            if recurring.last_executed_date == run_date:
                continue

            transaction_data = TransactionCreate(
                user_id=recurring.user_id,
                amount=recurring.amount,
                description=recurring.description,
                transaction_type=TransactionType(recurring.transaction_type),
                category=recurring.category,
                transaction_date=run_date,
            )

            created_transaction = TransactionService.create_transaction(
                db,
                transaction_data,
            )
            created_transaction_ids.append(created_transaction.id)

            next_execution_date = RecurringService._advance_date(
                recurring.next_execution_date,
                recurring.frequency,
            )
            RecurringRepository.update(
                db,
                recurring,
                {
                    "last_executed_date": run_date,
                    "next_execution_date": next_execution_date,
                },
            )

            logger.info(
                "Recurring executed | recurring_id=%s transaction_id=%s next_execution_date=%s",
                recurring.id,
                created_transaction.id,
                next_execution_date,
            )

        return created_transaction_ids