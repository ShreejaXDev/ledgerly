from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.bot import TelegramMessage
from app.services.bot_services import BotService

router = APIRouter(prefix="/bot", tags=["Bot"])


@router.post("/message")
def receive_message(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Receive a message from the Telegram bot and process it."""
    return BotService.process_message(db, payload)