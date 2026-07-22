import json
from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency safety net
    genai = None

from app.core.config import GEMINI_API_KEY
from app.core.logger import logger
from app.repositories.user_repository import UserRepository
from app.schemas.bot import TelegramMessage
from app.schemas.insights import InsightExpenseItem, MonthlyInsightData
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService
from app.schemas.user import UserCreate


if genai is not None and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    _insights_model = genai.GenerativeModel("gemini-flash-latest")
else:
    _insights_model = None


class InsightsService:
    @staticmethod
    def _get_or_create_user(db: Session, payload: TelegramMessage):
        user = UserRepository.get_by_telegram_id(db, payload.telegram_id)
        if user is not None:
            return user

        logger.info(
            "Insights user missing | telegram_id=%s registering automatically",
            payload.telegram_id,
        )
        user_data = UserCreate(
            telegram_id=payload.telegram_id,
            username=payload.username or "unknown",
            first_name=payload.first_name,
        )
        UserService.create_user(db, user_data)
        return UserRepository.get_by_telegram_id(db, payload.telegram_id)

    @staticmethod
    def _build_monthly_insight_data(
        transactions,
    ) -> MonthlyInsightData:
        expense_by_category: dict[str, float] = defaultdict(float)
        income_by_category: dict[str, float] = defaultdict(float)
        expense_by_day: dict[str, float] = defaultdict(float)
        expense_transactions = []

        income_total = 0.0
        expense_total = 0.0

        for transaction in transactions:
            transaction_type = getattr(transaction.transaction_type, "value", transaction.transaction_type)
            amount = float(transaction.amount)
            transaction_date = transaction.transaction_date.isoformat()

            if transaction_type == "income":
                income_total += amount
                income_by_category[transaction.category] += amount
            else:
                expense_total += amount
                expense_by_category[transaction.category] += amount
                expense_by_day[transaction_date] += amount
                expense_transactions.append(transaction)

        highest_expense_category = None
        if expense_by_category:
            highest_expense_category = max(
                expense_by_category.items(),
                key=lambda item: item[1],
            )[0]

        highest_income_source = None
        if income_by_category:
            highest_income_source = max(
                income_by_category.items(),
                key=lambda item: item[1],
            )[0]

        most_expensive_day = None
        if expense_by_day:
            day, total = max(expense_by_day.items(), key=lambda item: item[1])
            most_expensive_day = f"{day} (₹{total:,.0f})"

        current_day_of_month = date.today().day
        average_daily_spending = expense_total / current_day_of_month if current_day_of_month else 0.0

        top_5_expenses = sorted(
            expense_transactions,
            key=lambda transaction: transaction.amount,
            reverse=True,
        )[:5]

        largest_transaction = None
        if transactions:
            largest_transaction_record = max(
                transactions,
                key=lambda transaction: float(transaction.amount),
            )
            largest_transaction = (
                f"{largest_transaction_record.transaction_date.isoformat()} "
                f"{largest_transaction_record.category} "
                f"₹{float(largest_transaction_record.amount):,.0f}"
            )

        if income_total > expense_total:
            trend = f"Income is ahead of expenses by ₹{income_total - expense_total:,.0f}."
        elif expense_total > income_total:
            trend = f"Expenses are ahead of income by ₹{expense_total - income_total:,.0f}."
        else:
            trend = "Income and expenses are currently balanced."

        return MonthlyInsightData(
            highest_expense_category=highest_expense_category,
            highest_income_source=highest_income_source,
            average_daily_spending=average_daily_spending,
            most_expensive_day=most_expensive_day,
            top_5_expenses=[
                InsightExpenseItem(
                    transaction_date=transaction.transaction_date.isoformat(),
                    category=transaction.category,
                    description=transaction.description or "—",
                    amount=float(transaction.amount),
                )
                for transaction in top_5_expenses
            ],
            largest_transaction=largest_transaction,
            income_total=income_total,
            expense_total=expense_total,
            savings=income_total - expense_total,
            income_vs_expense_trend=trend,
        )

    @staticmethod
    def _manual_insights(data: MonthlyInsightData) -> str:
        reply_lines = [
            "🧠 Financial Insights",
            "",
        ]

        if data.highest_expense_category:
            reply_lines.append(
                f"• Highest expense category: {data.highest_expense_category}"
            )
        if data.highest_income_source:
            reply_lines.append(
                f"• Highest income source: {data.highest_income_source}"
            )

        reply_lines.extend(
            [
                f"• Average daily spending: ₹{data.average_daily_spending:,.0f}",
                f"• Most expensive day: {data.most_expensive_day or '—'}",
                f"• Savings: ₹{data.savings:,.0f}",
                f"• Trend: {data.income_vs_expense_trend or '—'}",
            ]
        )

        if data.top_5_expenses:
            reply_lines.extend(["", "Top 5 Expenses:"])
            for item in data.top_5_expenses:
                reply_lines.append(
                    f"{item.transaction_date} {item.description} - ₹{item.amount:,.0f}"
                )

        if data.largest_transaction:
            reply_lines.extend(["", f"Largest transaction: {data.largest_transaction}"])

        return "\n".join(reply_lines)

    @staticmethod
    def get_insights(
        db: Session,
        payload: TelegramMessage,
    ) -> dict:
        logger.info(
            "Insights requested | telegram_id=%s username=%s",
            payload.telegram_id,
            payload.username,
        )

        user = InsightsService._get_or_create_user(db, payload)
        transactions = TransactionService.get_transactions_for_current_month(
            db,
            user.telegram_id,
        )

        if not transactions:
            return {"reply": "No transactions found for this month."}

        insight_data = InsightsService._build_monthly_insight_data(transactions)
        structured_payload = insight_data.model_dump()

        if _insights_model is not None:
            prompt = (
                "You are a financial advisor for a personal finance app. "
                "Use the structured monthly data below to generate concise, personalized "
                "financial insights. Focus on spending patterns, savings, and practical advice. "
                "Return only plain text with short paragraphs and bullets.\n\n"
                f"Structured data:\n{json.dumps(structured_payload, indent=2)}"
            )

            try:
                gemini_response = _insights_model.generate_content(prompt)
                raw_text = (gemini_response.text or "").strip()
                if raw_text:
                    logger.info(
                        "Insights generated via Gemini | telegram_id=%s",
                        payload.telegram_id,
                    )
                    return {"reply": f"📊 Financial Insights\n\n{raw_text}"}
            except Exception as exc:
                logger.warning(
                    "Gemini insights generation failed | telegram_id=%s error=%s",
                    payload.telegram_id,
                    exc,
                )

        logger.info(
            "Using manual insights fallback | telegram_id=%s",
            payload.telegram_id,
        )
        return {"reply": InsightsService._manual_insights(insight_data)}