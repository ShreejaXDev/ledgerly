from datetime import date
from calendar import monthrange

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.repositories.budget_repository import BudgetRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.bot import TelegramMessage
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetSummary
from app.schemas.user import UserCreate
from app.services.user_service import UserService


class BudgetService:
    @staticmethod
    def _get_or_create_user(db: Session, payload: TelegramMessage):
        user = UserRepository.get_by_telegram_id(db, payload.telegram_id)
        if user is not None:
            return user

        logger.info(
            "Budget user missing | telegram_id=%s registering automatically",
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
    def _get_month_range() -> tuple[date, date]:
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today.replace(day=monthrange(today.year, today.month)[1])
        return start_date, end_date

    @staticmethod
    def _build_progress_bar(used_percentage: float) -> str:
        filled = min(10, max(0, round(used_percentage / 10)))
        return "█" * filled + "░" * (10 - filled)

    @staticmethod
    def _get_monthly_spent_amount(db: Session, user_id: int) -> float:
        start_date, end_date = BudgetService._get_month_range()
        transactions = TransactionRepository.get_by_user_and_date_range(
            db,
            user_id,
            start_date,
            end_date,
        )
        return sum(
            transaction.amount
            for transaction in transactions
            if transaction.transaction_type == "expense"
        )

    @staticmethod
    def set_budget(
        db: Session,
        payload: TelegramMessage,
        budget: BudgetCreate,
    ) -> BudgetResponse:
        user = BudgetService._get_or_create_user(db, payload)

        existing_budget = BudgetRepository.get_by_user_id(db, user.id)
        budget_data = {"user_id": user.id, "budget_amount": budget.budget_amount}

        if existing_budget is None:
            logger.info(
                "Budget created | telegram_id=%s user_id=%s amount=%.2f",
                payload.telegram_id,
                user.id,
                budget.budget_amount,
            )
            result = BudgetRepository.create(db, budget_data)
        else:
            logger.info(
                "Budget updated | telegram_id=%s user_id=%s amount=%.2f",
                payload.telegram_id,
                user.id,
                budget.budget_amount,
            )
            result = BudgetRepository.update(db, existing_budget, budget_data)

        return BudgetResponse.model_validate(result)

    @staticmethod
    def get_budget_summary(
        db: Session,
        payload: TelegramMessage,
    ) -> BudgetSummary | None:
        user = BudgetService._get_or_create_user(db, payload)

        existing_budget = BudgetRepository.get_by_user_id(db, user.id)
        if existing_budget is None:
            logger.info(
                "Budget summary requested but missing | telegram_id=%s user_id=%s",
                payload.telegram_id,
                user.id,
            )
            return None

        spent_amount = BudgetService._get_monthly_spent_amount(db, user.id)
        remaining_amount = existing_budget.budget_amount - spent_amount
        used_percentage = (
            (spent_amount / existing_budget.budget_amount) * 100
            if existing_budget.budget_amount
            else 0.0
        )

        return BudgetSummary(
            budget_amount=existing_budget.budget_amount,
            spent_amount=spent_amount,
            remaining_amount=remaining_amount,
            used_percentage=used_percentage,
            progress_bar=BudgetService._build_progress_bar(used_percentage),
        )

    @staticmethod
    def get_budget_alert_message(
        budget_amount: float,
        spent_amount: float,
    ) -> str | None:
        if budget_amount <= 0:
            return None

        used_percentage = (spent_amount / budget_amount) * 100
        remaining = budget_amount - spent_amount

        if used_percentage >= 100:
            overspent = abs(remaining)
            return f"🚨 Budget exceeded by ₹{overspent:,.0f}"

        if used_percentage >= 80:
            return "⚠️ You have used 80% of your monthly budget."

        return None