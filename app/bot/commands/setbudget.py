from telegram import Update
from telegram.ext import ContextTypes

from app.bot.services.api_client import send_set_budget_to_backend


async def setbudget_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.args:
        await update.message.reply_text("Usage: /setbudget <amount>")
        return

    try:
        budget_amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid budget amount.")
        return

    user = update.effective_user
    payload = {
        "telegram_id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "budget_amount": budget_amount,
    }

    response = await send_set_budget_to_backend(payload)

    await update.message.reply_text(response["reply"])