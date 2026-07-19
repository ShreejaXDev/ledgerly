from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.core.config import BOT_TOKEN

from app.bot.commands.start import start_command
from app.bot.commands.help import help_command
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
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler,
        )
    )

    print("Ledgerly Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()