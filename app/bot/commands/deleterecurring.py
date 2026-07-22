from telegram import Update
from telegram.ext import ContextTypes

from app.bot.services.api_client import send_delete_recurring_to_backend


async def deleterecurring_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.args:
        await update.message.reply_text("Usage: /deleterecurring <recurring_id>")
        return

    try:
        recurring_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid recurring ID.")
        return

    user = update.effective_user
    payload = {
        "telegram_id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "recurring_id": recurring_id,
    }

    response = await send_delete_recurring_to_backend(payload)
    await update.message.reply_text(response["reply"])