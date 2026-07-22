from telegram import Update
from telegram.ext import ContextTypes

from app.bot.services.api_client import send_today_summary_to_backend


async def today_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    payload = {
        "telegram_id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "message": "/today",
    }

    response = await send_today_summary_to_backend(payload)

    await update.message.reply_text(
        response["reply"],
    )