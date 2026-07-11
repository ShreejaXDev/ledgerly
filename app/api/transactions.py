from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import Transaction
from app.schemas.transaction import TransactionCreate

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/")
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    db_transaction = Transaction(**transaction.model_dump())

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction


@router.get("/")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()