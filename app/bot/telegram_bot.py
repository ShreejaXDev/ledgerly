from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.core.config import BOT_TOKEN

from app.bot.commands.start import start_command
from app.bot.commands.help import help_command
from app.bot.commands.today import today_command
from app.bot.commands.week import week_command
from app.bot.commands.month import month_command
from app.bot.commands.summary import summary_command
from app.bot.commands.setbudget import setbudget_command
from app.bot.commands.budget import budget_command
from app.bot.commands.insights import insights_command
from app.bot.commands.addrecurring import addrecurring_command
from app.bot.commands.listrecurring import listrecurring_command
from app.bot.commands.deleterecurring import deleterecurring_command
from app.bot.commands.export import export_command
from app.bot.handlers.message_handler import (
    message_handler,
)


def main():

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    app.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "today",
            today_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "week",
            week_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "month",
            month_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "summary",
            summary_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "setbudget",
            setbudget_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "budget",
            budget_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "insights",
            insights_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "addrecurring",
            addrecurring_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "listrecurring",
            listrecurring_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "deleterecurring",
            deleterecurring_command,
        )
    )

    app.add_handler(
        CommandHandler(
            "export",
            export_command,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler,
        )
    )

    print("Ledgerly Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()