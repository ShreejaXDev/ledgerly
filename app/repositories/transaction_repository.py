from sqlalchemy.orm import Session
from app.models.transaction import Transaction


class TransactionRepository:

    @staticmethod
    def create(db: Session, transaction_data: dict):
        transaction = Transaction(**transaction_data)

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    @staticmethod
    def get_all(db: Session):
        return db.query(Transaction).all()