from pydantic import BaseModel
from datetime import date


class TransactionCreate(BaseModel):
    user_id: int
    amount: float
    transaction_type: str
    category: str
    description: str | None = None
    merchant: str | None = None
    transaction_date: date


class TransactionResponse(TransactionCreate):
    id: int

    class Config:
        from_attributes = True