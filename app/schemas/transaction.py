from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class TransactionCreate(BaseModel):
    user_id: int
    amount: float
    transaction_type: str
    category: str
    description: str | None = None
    merchant: str | None = None
    transaction_date: date


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: str
    category: str
    description: str | None
    merchant: str | None
    transaction_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)