from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.transaction_service import TransactionService
from app.database.dependencies import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
)
router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    return TransactionService.create_transaction(
        db,
        transaction,
    )


@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db)
):
    return TransactionService.get_transactions(db)