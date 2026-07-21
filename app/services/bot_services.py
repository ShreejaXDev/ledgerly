from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTransaction
from app.core.logger import logger
from app.repositories.user_repository import UserRepository
from app.schemas.bot import TelegramMessage
from app.schemas.transaction import TransactionCreate, TransactionType
from app.schemas.user import UserCreate
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService
from app.utils.gemini_parser import parse_transaction


class BotService:
    """Business logic for bot message processing."""

    @staticmethod
    def process_message(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        """
        Process an incoming Telegram message.

        Flow:
            1. Log the incoming message.
            2. Get or auto-register the Telegram user.
            3. Parse the message as an expense.
            4. Save the transaction via TransactionService.
            5. Return a formatted confirmation (or error) reply.

        Args:
            db:      SQLAlchemy database session (injected by FastAPI).
            payload: Validated TelegramMessage from the bot API.

        Returns:
            dict with a single "reply" key containing the Telegram reply text.
        """
        logger.info(
            "Telegram message received | telegram_id=%s username=%s message='%s'",
            payload.telegram_id,
            payload.username,
            payload.message,
        )

        # ── Step 1: Get or auto-register user ────────────────────────────────
        user = UserRepository.get_by_telegram_id(db, payload.telegram_id)

        if user is None:
            logger.info(
                "New user detected | telegram_id=%s — registering automatically",
                payload.telegram_id,
            )
            user_data = UserCreate(
                telegram_id=payload.telegram_id,
                username=payload.username or "unknown",
                first_name=payload.first_name,
            )
            UserService.create_user(db, user_data)
            # Fetch the newly created user to get their DB id
            user = UserRepository.get_by_telegram_id(db, payload.telegram_id)
        else:
            logger.info(
                "Existing user found | telegram_id=%s user_id=%s",
                payload.telegram_id,
                user.id,
            )

        # ── Step 2: Parse message via Gemini ─────────────────────────────────
        try:
            parsed = parse_transaction(payload.message)
        except InvalidTransaction:
            logger.warning(
                "Gemini parse failed | telegram_id=%s message='%s'",
                payload.telegram_id,
                payload.message,
            )
            return {
                "reply": (
                    "❌ Could not understand your message.\n\n"
                    "Try something like:\n"
                    "• 250 pizza\n"
                    "• Yesterday spent 350 on Uber\n"
                    "• Received salary 25000"
                )
            }

        # ── Step 3: Build TransactionCreate and save ──────────────────────────
        transaction_data = TransactionCreate(
            user_id=user.id,
            amount=parsed["amount"],
            description=parsed["description"],
            transaction_type=TransactionType(parsed["transaction_type"]),
            category=parsed["category"],
            transaction_date=date.fromisoformat(parsed["transaction_date"]),
        )

        transaction = TransactionService.create_transaction(db, transaction_data)

        logger.info(
            "Transaction saved | transaction_id=%s user_id=%s amount=%.2f "
            "category='%s' date=%s",
            transaction.id,
            transaction.user_id,
            transaction.amount,
            transaction.category,
            transaction.transaction_date,
        )

        # ── Step 4: Return confirmation reply ─────────────────────────────────
        tx_type_label = transaction.transaction_type.capitalize() \
            if isinstance(transaction.transaction_type, str) \
            else transaction.transaction_type.value.capitalize()

        return {
            "reply": (
                f"✅ Transaction Saved\n\n"
                f"Amount: ₹{transaction.amount:,.0f}\n"
                f"Category: {transaction.category}\n"
                f"Description: {transaction.description or '—'}\n"
                f"Date: {transaction.transaction_date}\n"
                f"Type: {tx_type_label}"
            )
        }