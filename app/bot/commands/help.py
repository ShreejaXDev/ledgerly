from telegram import Update
from telegram.ext import ContextTypes


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        """
Ledgerly Commands

/start

/help

/today

/week

/month

/summary

/insights

/setbudget

/budget

/addrecurring

/listrecurring

/deleterecurring

/export
"""
    )