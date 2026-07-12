from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class TransactionCreate(BaseModel):
    user_id: int
    amount: float = Field(gt=0)
    transaction_type: TransactionType
    category: str
    description: str | None = None
    merchant: str | None = None
    transaction_date: date


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: TransactionType
    category: str
    description: str | None
    merchant: str | None
    transaction_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)