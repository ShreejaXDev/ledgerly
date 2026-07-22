import os

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.services.api_client import send_export_to_backend


async def export_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    export_format = "csv"
    if context.args:
        export_format = context.args[0].lower()

    if export_format not in {"csv", "xlsx", "pdf"}:
        await update.message.reply_text("Usage: /export <csv|xlsx|pdf>")
        return

    user = update.effective_user
    payload = {
        "telegram_id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "export_format": export_format,
    }

    response = await send_export_to_backend(payload)
    file_path = response.get("file_path")
    filename = response.get("filename", os.path.basename(file_path) if file_path else "export")

    if not file_path:
        await update.message.reply_text(response.get("reply", "No transactions found to export."))
        return

    with open(file_path, "rb") as file_handle:
        await update.message.reply_document(
            document=file_handle,
            filename=filename,
            caption="Here is your Ledgerly export.",
        )