"""
Gemini AI parser for Ledgerly.

Sends a plain-text user message to Google Gemini and receives a
structured JSON transaction object in return.

Drop-in design:
    Phase 4 used parse_expense() from parser.py.
    Phase 5 replaces that call with parse_transaction() from this file.
    BotService, TransactionService, and all repositories are unchanged.

Future replacement:
    When you want to swap AI providers (e.g. OpenAI, Claude), only this
    file needs to change. The rest of the architecture stays identical.
"""

import json
from datetime import date

import google.generativeai as genai

from app.core.config import GEMINI_API_KEY
from app.core.exceptions import InvalidTransaction
from app.core.logger import logger

# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY is not set. "
        "Add it to your .env file before starting the server."
    )

genai.configure(api_key=GEMINI_API_KEY)

_model = genai.GenerativeModel("gemini-flash-latest")

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """\
You are a financial transaction parser for an expense-tracking app.

Today's date is {today}.

The user sent this message:
\"{message}\"

Extract the following fields from the message and return ONLY a single valid JSON object. Do NOT include markdown, code fences, explanations, or any other text — just the raw JSON.

Fields:
- amount       (number, must be > 0)
- description  (string, short human-readable label, e.g. "Pizza", "Uber", "Salary")
- category     (string, one of: Food, Transport, Shopping, Health, Entertainment, Utilities, Income, Other)
- transaction_type  (string, either "expense" or "income")
- transaction_date  (string, ISO 8601 format YYYY-MM-DD; resolve relative dates like "yesterday" or "last Monday" using today's date; default to today if no date is mentioned)

Rules:
- If the message describes money spent / paid / bought, use transaction_type = "expense".
- If the message describes money received / earned / salary / credited, use transaction_type = "income".
- category should be "Income" when transaction_type is "income".
- Return ONLY the JSON object. No extra keys. No extra text.

Examples:

Input: "250 pizza"
Output: {{"amount":250,"description":"Pizza","category":"Food","transaction_type":"expense","transaction_date":"{today}"}}

Input: "Yesterday spent 350 on Uber"
Output: {{"amount":350,"description":"Uber","category":"Transport","transaction_type":"expense","transaction_date":"{yesterday}"}}

Input: "Received salary 25000"
Output: {{"amount":25000,"description":"Salary","category":"Income","transaction_type":"income","transaction_date":"{today}"}}
"""

# ---------------------------------------------------------------------------
# Required output fields
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = {
    "amount",
    "description",
    "category",
    "transaction_type",
    "transaction_date",
}

_VALID_TRANSACTION_TYPES = {"expense", "income"}


# ---------------------------------------------------------------------------
# Public parser function
# ---------------------------------------------------------------------------


def parse_transaction(message: str) -> dict:
    """
    Parse a plain-text user message into a structured transaction dict
    using Google Gemini.

    Args:
        message: Raw text sent by the Telegram user, e.g. "250 pizza".

    Returns:
        A dict with keys:
            - amount           (float)  : Positive transaction amount.
            - description      (str)    : Human-readable label.
            - category         (str)    : Spending/income category.
            - transaction_type (str)    : "expense" or "income".
            - transaction_date (str)    : ISO 8601 date string (YYYY-MM-DD).

    Raises:
        InvalidTransaction: If the message is empty, Gemini returns
                            malformed JSON, or required fields are missing
                            or fail validation.
    """
    if not message or not message.strip():
        logger.warning("Gemini parse failed | empty message received")
        raise InvalidTransaction("Message is empty.")

    today = date.today()
    from datetime import timedelta
    yesterday = today - timedelta(days=1)

    prompt = _PROMPT_TEMPLATE.format(
        today=today.isoformat(),
        yesterday=yesterday.isoformat(),
        message=message.strip(),
    )

    logger.info(
        "Gemini request | message='%s' today=%s",
        message.strip(),
        today.isoformat(),
    )

    # ── Call Gemini ──────────────────────────────────────────────────────────
    try:
        gemini_response = _model.generate_content(prompt)
        raw_text = gemini_response.text.strip()
    except Exception as exc:
        logger.error("Gemini API error | %s", exc)
        raise InvalidTransaction(
            f"Gemini API call failed: {exc}"
        ) from exc

    logger.info("Gemini response | raw='%s'", raw_text)

    # ── Strip accidental markdown fences (safety net) ───────────────────────
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        # Remove opening fence (```json or ```) and closing fence (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_text = "\n".join(lines).strip()

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        parsed: dict = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error(
            "Gemini parse failed | invalid JSON returned: '%s'", raw_text
        )
        raise InvalidTransaction(
            f"Gemini returned invalid JSON: {raw_text!r}"
        ) from exc

    # ── Field presence check ─────────────────────────────────────────────────
    missing = _REQUIRED_FIELDS - parsed.keys()
    if missing:
        logger.error(
            "Gemini parse failed | missing fields %s in response: %s",
            missing,
            parsed,
        )
        raise InvalidTransaction(
            f"Gemini response missing required fields: {missing}"
        )

    # ── Business validation ──────────────────────────────────────────────────
    try:
        amount = float(parsed["amount"])
    except (TypeError, ValueError):
        logger.error(
            "Gemini parse failed | non-numeric amount: %s", parsed["amount"]
        )
        raise InvalidTransaction(
            f"Amount is not a valid number: {parsed['amount']!r}"
        )

    if amount <= 0:
        logger.error(
            "Gemini parse failed | non-positive amount=%.2f", amount
        )
        raise InvalidTransaction(
            f"Amount must be greater than zero, got {amount}."
        )

    transaction_type = str(parsed["transaction_type"]).lower().strip()
    if transaction_type not in _VALID_TRANSACTION_TYPES:
        logger.error(
            "Gemini parse failed | invalid transaction_type='%s'",
            transaction_type,
        )
        raise InvalidTransaction(
            f"transaction_type must be 'expense' or 'income', "
            f"got {transaction_type!r}."
        )

    # Validate date is a parseable ISO 8601 string
    try:
        date.fromisoformat(str(parsed["transaction_date"]))
    except ValueError:
        logger.error(
            "Gemini parse failed | invalid transaction_date='%s'",
            parsed["transaction_date"],
        )
        raise InvalidTransaction(
            f"transaction_date is not a valid ISO date: "
            f"{parsed['transaction_date']!r}"
        )

    result = {
        "amount": amount,
        "description": str(parsed["description"]).strip(),
        "category": str(parsed["category"]).strip(),
        "transaction_type": transaction_type,
        "transaction_date": str(parsed["transaction_date"]),
    }

    logger.info(
        "Transaction parsed | amount=%.2f description='%s' "
        "category='%s' type='%s' date='%s'",
        result["amount"],
        result["description"],
        result["category"],
        result["transaction_type"],
        result["transaction_date"],
    )

    return result
