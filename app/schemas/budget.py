from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    budget_amount: float = Field(gt=0)


class BudgetCommandRequest(BaseModel):
    telegram_id: str
    username: str | None = None
    first_name: str
    last_name: str | None = None
    budget_amount: float = Field(gt=0)


class BudgetResponse(BaseModel):
    id: int
    user_id: int
    budget_amount: float
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BudgetSummary(BaseModel):
    budget_amount: float
    spent_amount: float
    remaining_amount: float
    used_percentage: float
    progress_bar: str
