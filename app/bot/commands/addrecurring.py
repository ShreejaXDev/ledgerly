from telegram import Update
from telegram.ext import ContextTypes

from app.bot.services.api_client import send_add_recurring_to_backend


async def addrecurring_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if len(context.args) < 5:
        await update.message.reply_text(
            "Usage: /addrecurring <amount> <daily|weekly|monthly|yearly> <income|expense> <category> <description>"
        )
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid amount.")
        return

    frequency = context.args[1].lower()
    transaction_type = context.args[2].lower()
    category = context.args[3]
    description = " ".join(context.args[4:])

    user = update.effective_user
    payload = {
        "telegram_id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "amount": amount,
        "description": description,
        "category": category,
        "transaction_type": transaction_type,
        "frequency": frequency,
    }

    response = await send_add_recurring_to_backend(payload)
    await update.message.reply_text(response["reply"])