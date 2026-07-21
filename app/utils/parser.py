"""
Expense parser for Ledgerly.

Parses plain-text expense messages sent via Telegram.

Current format:  "<amount> <description>"
Example:         "250 pizza"

Designed to be a drop-in replacement target: when Gemini AI is
integrated in a future phase, only this module needs to change.
The rest of the architecture (BotService → TransactionService →
TransactionRepository) remains untouched.
"""

from app.core.exceptions import InvalidTransaction
from app.core.logger import logger


def parse_expense(message: str) -> dict:
    """
    Parse a plain-text expense message into a structured dict.

    Args:
        message: Raw text sent by the Telegram user.
                 Expected format: "<amount> <description>"

    Returns:
        A dict with keys:
            - amount (float): The expense amount.
            - description (str): What the money was spent on.
            - transaction_type (str): Always "expense" for now.
            - category (str): Defaults to "general" until AI categorisation.

    Raises:
        InvalidTransaction: If the message is empty, the amount is
                            missing, or the amount is not positive.
    """
    if not message or not message.strip():
        logger.warning("Expense parse failed | empty message received")
        raise InvalidTransaction("Message is empty.")

    parts = message.strip().split(maxsplit=1)

    # Validate that the first token is a numeric amount
    try:
        amount = float(parts[0])
    except ValueError:
        logger.warning(
            "Expense parse failed | first token is not a number: '%s'",
            parts[0],
        )
        raise InvalidTransaction(f"Amount not found in message: '{message}'")

    if amount <= 0:
        logger.warning(
            "Expense parse failed | non-positive amount=%.2f",
            amount,
        )
        raise InvalidTransaction(f"Amount must be greater than zero, got {amount}.")

    description = parts[1].strip() if len(parts) > 1 else ""

    parsed = {
        "amount": amount,
        "description": description,
        "transaction_type": "expense",
        "category": "general",  # placeholder — Gemini will classify this later
    }

    logger.info(
        "Expense parsed | amount=%.2f description='%s'",
        parsed["amount"],
        parsed["description"],
    )

    return parsed
