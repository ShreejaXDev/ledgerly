from datetime import date
from collections import defaultdict
from itertools import islice

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTransaction
from app.core.logger import logger
from app.repositories.user_repository import UserRepository
from app.schemas.bot import TelegramMessage
from app.schemas.budget import BudgetCreate, BudgetCommandRequest
from app.schemas.export import ExportRequest
from app.schemas.recurring import (
    RecurringCommandRequest,
    RecurringCreate,
    RecurringDeleteRequest,
)
from app.services.insights_service import InsightsService
from app.schemas.transaction import TransactionCreate, TransactionType
from app.schemas.user import UserCreate
from app.services.budget_service import BudgetService
from app.services.export_service import ExportService
from app.services.recurring_service import RecurringService
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService
from app.utils.gemini_parser import parse_transaction


class BotService:
    """Business logic for bot message processing."""

    @staticmethod
    def process_message(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        """
        Process an incoming Telegram message.

        Flow:
            1. Log the incoming message.
            2. Get or auto-register the Telegram user.
            3. Parse the message as an expense.
            4. Save the transaction via TransactionService.
            5. Return a formatted confirmation (or error) reply.

        Args:
            db:      SQLAlchemy database session (injected by FastAPI).
            payload: Validated TelegramMessage from the bot API.

        Returns:
            dict with a single "reply" key containing the Telegram reply text.
        """
        logger.info(
            "Telegram message received | telegram_id=%s username=%s message='%s'",
            payload.telegram_id,
            payload.username,
            payload.message,
        )

        # ── Step 1: Get or auto-register user ────────────────────────────────
        user = UserRepository.get_by_telegram_id(db, payload.telegram_id)

        if user is None:
            logger.info(
                "New user detected | telegram_id=%s — registering automatically",
                payload.telegram_id,
            )
            user_data = UserCreate(
                telegram_id=payload.telegram_id,
                username=payload.username or "unknown",
                first_name=payload.first_name,
            )
            UserService.create_user(db, user_data)
            # Fetch the newly created user to get their DB id
            user = UserRepository.get_by_telegram_id(db, payload.telegram_id)
        else:
            logger.info(
                "Existing user found | telegram_id=%s user_id=%s",
                payload.telegram_id,
                user.id,
            )

        # ── Step 2: Parse message via Gemini ─────────────────────────────────
        try:
            parsed = parse_transaction(payload.message)
        except InvalidTransaction:
            logger.warning(
                "Gemini parse failed | telegram_id=%s message='%s'",
                payload.telegram_id,
                payload.message,
            )
            return {
                "reply": (
                    "❌ Could not understand your message.\n\n"
                    "Try something like:\n"
                    "• 250 pizza\n"
                    "• Yesterday spent 350 on Uber\n"
                    "• Received salary 25000"
                )
            }

        # ── Step 3: Build TransactionCreate and save ──────────────────────────
        transaction_data = TransactionCreate(
            user_id=user.id,
            amount=parsed["amount"],
            description=parsed["description"],
            transaction_type=TransactionType(parsed["transaction_type"]),
            category=parsed["category"],
            transaction_date=date.fromisoformat(parsed["transaction_date"]),
        )

        transaction = TransactionService.create_transaction(db, transaction_data)

        logger.info(
            "Transaction saved | transaction_id=%s user_id=%s amount=%.2f "
            "category='%s' date=%s",
            transaction.id,
            transaction.user_id,
            transaction.amount,
            transaction.category,
            transaction.transaction_date,
        )

        # ── Step 4: Return confirmation reply ─────────────────────────────────
        tx_type_label = transaction.transaction_type.capitalize() \
            if isinstance(transaction.transaction_type, str) \
            else transaction.transaction_type.value.capitalize()

        budget_summary = BudgetService.get_budget_summary(
            db,
            TelegramMessage(
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                message="budget-check",
            ),
        )

        budget_alert = None
        if budget_summary is not None:
            budget_alert = BudgetService.get_budget_alert_message(
                budget_summary.budget_amount,
                budget_summary.spent_amount,
            )

        reply = (
                f"✅ Transaction Saved\n\n"
                f"Amount: ₹{transaction.amount:,.0f}\n"
                f"Category: {transaction.category}\n"
                f"Description: {transaction.description or '—'}\n"
                f"Date: {transaction.transaction_date}\n"
                f"Type: {tx_type_label}"
        )

        if budget_alert:
            reply = f"{reply}\n\n{budget_alert}"

        return {"reply": reply}

    @staticmethod
    def process_today(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        """Build a summary of today's transactions for the Telegram user."""
        logger.info(
            "Today's summary requested | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        transactions = TransactionService.get_todays_transactions_for_telegram_user(
            db,
            payload.telegram_id,
        )

        if not transactions:
            return {"reply": "No transactions found for today."}

        grouped_amounts: dict[str, dict[str, float]] = {
            "expense": defaultdict(float),
            "income": defaultdict(float),
        }

        total_income = 0.0
        total_expense = 0.0

        for transaction in transactions:
            transaction_type = getattr(transaction.transaction_type, "value", transaction.transaction_type)
            amount = float(transaction.amount)
            category = transaction.category

            grouped_amounts[transaction_type][category] += amount

            if transaction_type == TransactionType.income.value:
                total_income += amount
            else:
                total_expense += amount

        reply_lines: list[str] = ["📅 Today's Summary", ""]

        expense_lines = grouped_amounts[TransactionType.expense.value]
        if expense_lines:
            reply_lines.append("💸 Expenses:")
            for category, amount in sorted(expense_lines.items()):
                reply_lines.append(f"{category} - ₹{amount:,.0f}")
            reply_lines.append("")

        income_lines = grouped_amounts[TransactionType.income.value]
        if income_lines:
            reply_lines.append("💰 Income:")
            for category, amount in sorted(income_lines.items()):
                reply_lines.append(f"{category} - ₹{amount:,.0f}")
            reply_lines.append("")

        reply_lines.extend(
            [
                "--------------------",
                f"Total Income : ₹{total_income:,.0f}",
                f"Total Expense: ₹{total_expense:,.0f}",
                f"Net Balance : ₹{total_income - total_expense:,.0f}",
            ]
        )

        return {"reply": "\n".join(reply_lines)}

    @staticmethod
    def process_week(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        logger.info(
            "Weekly summary requested | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        transactions = TransactionService.get_transactions_for_last_7_days(
            db,
            payload.telegram_id,
        )

        if not transactions:
            return {"reply": "No transactions found for the last 7 days."}

        total_income = 0.0
        total_expense = 0.0
        expense_by_category: dict[str, float] = defaultdict(float)

        for transaction in transactions:
            transaction_type = getattr(transaction.transaction_type, "value", transaction.transaction_type)
            amount = float(transaction.amount)

            if transaction_type == TransactionType.income.value:
                total_income += amount
            else:
                total_expense += amount
                expense_by_category[transaction.category] += amount

        reply_lines = [
            "📅 Weekly Summary",
            "",
            f"Total Income : ₹{total_income:,.0f}",
            f"Total Expense: ₹{total_expense:,.0f}",
            f"Net Balance : ₹{total_income - total_expense:,.0f}",
        ]

        if expense_by_category:
            reply_lines.extend(["", "💸 Category-wise Expenses:"])
            for category, amount in sorted(
                expense_by_category.items(),
                key=lambda item: item[1],
                reverse=True,
            ):
                reply_lines.append(f"{category} ₹{amount:,.0f}")

        return {"reply": "\n".join(reply_lines)}

    @staticmethod
    def process_month(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        logger.info(
            "Monthly summary requested | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        transactions = TransactionService.get_transactions_for_current_month(
            db,
            payload.telegram_id,
        )

        if not transactions:
            return {"reply": "No transactions found for this month."}

        total_income = 0.0
        total_expense = 0.0
        reply_lines = ["📅 Monthly Summary", ""]

        for transaction in transactions:
            transaction_type = getattr(transaction.transaction_type, "value", transaction.transaction_type)
            amount = float(transaction.amount)
            if transaction_type == TransactionType.income.value:
                total_income += amount
            else:
                total_expense += amount

        reply_lines.extend([
            f"Total Income : ₹{total_income:,.0f}",
            f"Total Expense: ₹{total_expense:,.0f}",
            f"Net Balance : ₹{total_income - total_expense:,.0f}",
            "",
        ])

        for transaction in transactions:
            transaction_date = transaction.transaction_date.strftime("%d %b")
            reply_lines.append(transaction_date)
            reply_lines.append(f"{transaction.category} ₹{transaction.amount:,.0f}")
            reply_lines.append("")

        return {"reply": "\n".join(reply_lines).rstrip()}

    @staticmethod
    def process_summary(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        logger.info(
            "Overall summary requested | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        transactions = TransactionService.get_all_transactions_for_telegram_user(
            db,
            payload.telegram_id,
        )

        if not transactions:
            return {"reply": "No transactions found. Start by adding your first transaction."}

        total_income = 0.0
        total_expense = 0.0
        expense_by_category: dict[str, float] = defaultdict(float)
        income_by_category: dict[str, float] = defaultdict(float)

        for transaction in transactions:
            transaction_type = getattr(transaction.transaction_type, "value", transaction.transaction_type)
            amount = float(transaction.amount)

            if transaction_type == TransactionType.income.value:
                total_income += amount
                income_by_category[transaction.category] += amount
            else:
                total_expense += amount
                expense_by_category[transaction.category] += amount

        highest_expense_category = "—"
        if expense_by_category:
            highest_expense_category = max(
                expense_by_category.items(),
                key=lambda item: item[1],
            )[0]

        highest_income_source = "—"
        if income_by_category:
            highest_income_source = max(
                income_by_category.items(),
                key=lambda item: item[1],
            )[0]

        most_recent_transaction = max(
            transactions,
            key=lambda transaction: (transaction.transaction_date, transaction.id),
        )

        last_five_transactions = list(
            islice(reversed(transactions), 5)
        )

        reply_lines = [
            "📊 Overall Summary",
            "",
            f"Total Transactions : {len(transactions)}",
            f"Total Income : ₹{total_income:,.0f}",
            f"Total Expense: ₹{total_expense:,.0f}",
            f"Net Savings : ₹{total_income - total_expense:,.0f}",
            f"Highest Expense Category : {highest_expense_category}",
            f"Highest Income Source : {highest_income_source}",
            f"Most Recent Transaction : {most_recent_transaction.transaction_date.strftime('%d %b')} {most_recent_transaction.category} ₹{most_recent_transaction.amount:,.0f}",
            "",
            "Last 5 Transactions:",
        ]

        for transaction in last_five_transactions:
            reply_lines.append(
                f"{transaction.transaction_date.strftime('%d %b')} {transaction.category} ₹{transaction.amount:,.0f}"
            )

        return {"reply": "\n".join(reply_lines)}

    @staticmethod
    def process_set_budget(
        db: Session,
        payload: BudgetCommandRequest,
    ) -> dict:
        logger.info(
            "Set budget requested | telegram_id=%s amount=%.2f",
            payload.telegram_id,
            payload.budget_amount,
        )

        budget = BudgetService.set_budget(
            db,
            TelegramMessage(
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                message="/setbudget",
            ),
            BudgetCreate(budget_amount=payload.budget_amount),
        )

        summary = BudgetService.get_budget_summary(
            db,
            TelegramMessage(
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                message="/budget",
            ),
        )

        reply_lines = [
            f"💰 Monthly budget set to ₹{budget.budget_amount:,.0f}",
        ]

        if summary is not None:
            reply_lines.extend([
                "",
                f"Spent so far: ₹{summary.spent_amount:,.0f}",
                f"Remaining: ₹{summary.remaining_amount:,.0f}",
            ])

        return {"reply": "\n".join(reply_lines)}

    @staticmethod
    def process_budget(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        logger.info(
            "Budget summary requested | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        summary = BudgetService.get_budget_summary(db, payload)
        if summary is None:
            return {"reply": "No monthly budget found. Use /setbudget <amount> to create one."}

        reply = (
            "💰 Monthly Budget\n\n"
            f"Budget:\n₹{summary.budget_amount:,.0f}\n\n"
            f"Spent:\n₹{summary.spent_amount:,.0f}\n\n"
            f"Remaining:\n₹{summary.remaining_amount:,.0f}\n\n"
            f"Used:\n{summary.used_percentage:.0f}%\n\n"
            f"Progress Bar\n\n{summary.progress_bar}"
        )

        return {"reply": reply}

    @staticmethod
    def process_insights(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        logger.info(
            "Insights summary requested | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        return InsightsService.get_insights(db, payload)

    @staticmethod
    def process_add_recurring(
        db: Session,
        payload: RecurringCommandRequest,
    ) -> dict:
        logger.info(
            "Add recurring requested | telegram_id=%s frequency=%s",
            payload.telegram_id,
            payload.frequency,
        )

        recurring = RecurringService.create_recurring(
            db,
            TelegramMessage(
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                message="/addrecurring",
            ),
            RecurringCreate(
                amount=payload.amount,
                description=payload.description,
                category=payload.category,
                transaction_type=payload.transaction_type,
                frequency=payload.frequency,
                next_execution_date=date.today(),
            ),
        )

        return {
            "reply": (
                f"✅ Recurring transaction saved\n\n"
                f"ID: {recurring.id}\n"
                f"Amount: ₹{recurring.amount:,.0f}\n"
                f"Category: {recurring.category}\n"
                f"Type: {recurring.transaction_type.value}\n"
                f"Frequency: {recurring.frequency.value}\n"
                f"Next Run: {recurring.next_execution_date}"
            )
        }

    @staticmethod
    def process_list_recurring(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        logger.info(
            "List recurring requested | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        recurring_items = RecurringService.list_recurring(db, payload)
        if not recurring_items:
            return {"reply": "No recurring transactions found."}

        reply_lines = ["🔁 Recurring Transactions", ""]
        for item in recurring_items:
            reply_lines.append(
                f"ID {item.id} | ₹{item.amount:,.0f} | {item.category} | {item.frequency.value} | Next: {item.next_execution_date}"
            )

        return {"reply": "\n".join(reply_lines)}

    @staticmethod
    def process_delete_recurring(
        db: Session,
        payload: RecurringDeleteRequest,
    ) -> dict:
        logger.info(
            "Delete recurring requested | telegram_id=%s recurring_id=%s",
            payload.telegram_id,
            payload.recurring_id,
        )

        deleted = RecurringService.delete_recurring(
            db,
            TelegramMessage(
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                message="/deleterecurring",
            ),
            payload.recurring_id,
        )

        if not deleted:
            return {"reply": "Recurring transaction not found."}

        return {"reply": f"✅ Recurring transaction {payload.recurring_id} deleted."}

    @staticmethod
    def process_export(
        db: Session,
        payload: ExportRequest,
    ) -> dict:
        logger.info(
            "Export requested | telegram_id=%s format=%s",
            payload.telegram_id,
            payload.export_format,
        )

        export_result = ExportService.generate_export(
            db,
            TelegramMessage(
                telegram_id=payload.telegram_id,
                username=payload.username,
                first_name=payload.first_name,
                last_name=payload.last_name,
                message="/export",
            ),
            payload.export_format,
        )

        if export_result is None:
            return {"reply": "No transactions found to export."}

        return {
            "reply": (
                f"✅ Export ready\n\n"
                f"Format: {payload.export_format.value.upper()}\n"
                f"File: {export_result.filename}\n"
                f"Path: {export_result.file_path}"
            )
        }