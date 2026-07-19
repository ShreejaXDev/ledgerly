from telegram import Update
from telegram.ext import ContextTypes

from app.bot.services.api_client import send_message_to_backend


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_message = update.message.text

    response = await send_message_to_backend(user_message)

    await update.message.reply_text(
        response["reply"]
    )