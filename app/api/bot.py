from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.bot import TelegramMessage
from app.schemas.budget import BudgetCommandRequest
from app.schemas.export import ExportRequest
from app.schemas.recurring import RecurringCommandRequest, RecurringDeleteRequest
from app.services.bot_services import BotService

router = APIRouter(prefix="/bot", tags=["Bot"])


@router.post("/message")
def receive_message(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Receive a message from the Telegram bot and process it."""
    return BotService.process_message(db, payload)


@router.post("/today")
def receive_today_summary(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Return today's transaction summary for the Telegram user."""
    return BotService.process_today(db, payload)


@router.post("/week")
def receive_week_summary(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Return weekly transaction summary for the Telegram user."""
    return BotService.process_week(db, payload)


@router.post("/month")
def receive_month_summary(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Return monthly transaction summary for the Telegram user."""
    return BotService.process_month(db, payload)


@router.post("/summary")
def receive_overall_summary(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Return an overall financial dashboard for the Telegram user."""
    return BotService.process_summary(db, payload)


@router.post("/setbudget")
def receive_set_budget(
    payload: BudgetCommandRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Create or update a user's monthly budget."""
    return BotService.process_set_budget(db, payload)


@router.post("/budget")
def receive_budget_summary(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Return the current monthly budget summary for the Telegram user."""
    return BotService.process_budget(db, payload)


@router.post("/insights")
def receive_insights(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """Return monthly financial insights for the Telegram user."""
    return BotService.process_insights(db, payload)


@router.post("/addrecurring")
def receive_add_recurring(
    payload: RecurringCommandRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Create a recurring transaction for the Telegram user."""
    return BotService.process_add_recurring(db, payload)


@router.post("/listrecurring")
def receive_list_recurring(
    payload: TelegramMessage,
    db: Session = Depends(get_db),
) -> dict:
    """List recurring transactions for the Telegram user."""
    return BotService.process_list_recurring(db, payload)


@router.post("/deleterecurring")
def receive_delete_recurring(
    payload: RecurringDeleteRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a recurring transaction for the Telegram user."""
    return BotService.process_delete_recurring(db, payload)


@router.post("/export")
def receive_export(
    payload: ExportRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Generate an export file for the Telegram user."""
    return BotService.process_export(db, payload)