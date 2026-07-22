from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RecurringTransactionType(str, Enum):
    income = "income"
    expense = "expense"


class RecurringFrequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class RecurringCreate(BaseModel):
    amount: float = Field(gt=0)
    description: str
    category: str
    transaction_type: RecurringTransactionType
    frequency: RecurringFrequency
    next_execution_date: date


class RecurringCommandRequest(BaseModel):
    telegram_id: str
    username: str | None = None
    first_name: str
    last_name: str | None = None
    amount: float = Field(gt=0)
    description: str
    category: str
    transaction_type: RecurringTransactionType
    frequency: RecurringFrequency


class RecurringDeleteRequest(BaseModel):
    telegram_id: str
    username: str | None = None
    first_name: str
    last_name: str | None = None
    recurring_id: int = Field(gt=0)


class RecurringResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    description: str
    category: str
    transaction_type: RecurringTransactionType
    frequency: RecurringFrequency
    next_execution_date: date
    last_executed_date: date | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
