from sqlalchemy.orm import Session

from app.core.logger import logger
from app.repositories.user_repository import UserRepository
from app.schemas.bot import TelegramMessage
from app.schemas.user import UserCreate
from app.services.user_service import UserService


class BotService:
    """Business logic for bot message processing."""

    @staticmethod
    def process_message(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        """
        Process an incoming Telegram message.

        - Registers the user automatically if they do not exist.
        - Delegates user creation entirely to UserService.
        - Returns a reply string for the bot to send back.
        """
        logger.info(
            "Telegram message received | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        existing_user = UserRepository.get_by_telegram_id(db, payload.telegram_id)

        if existing_user is None:
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
        else:
            logger.info(
                "Existing user found | telegram_id=%s user_id=%s",
                payload.telegram_id,
                existing_user.id,
            )

        return {"reply": f"I received: {payload.message}"}