from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.transaction_service import TransactionService

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


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_by_id(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    return TransactionService.get_transaction_by_id(db, transaction_id)