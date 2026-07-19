from telegram import Update
from telegram.ext import ContextTypes


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        """
👋 Welcome to Ledgerly!

Track your expenses by simply chatting.

Examples:

200 pizza

Uber 350

Salary 25000

Type /help for more commands.
"""
    )