from pydantic import BaseModel
from pydantic import Field


class InsightExpenseItem(BaseModel):
    transaction_date: str
    category: str
    description: str
    amount: float


class MonthlyInsightData(BaseModel):
    highest_expense_category: str | None = None
    highest_income_source: str | None = None
    average_daily_spending: float = 0.0
    most_expensive_day: str | None = None
    top_5_expenses: list[InsightExpenseItem] = Field(default_factory=list)
    largest_transaction: str | None = None
    income_total: float = 0.0
    expense_total: float = 0.0
    savings: float = 0.0
    income_vs_expense_trend: str | None = None


class InsightsResponse(BaseModel):
    reply: str
