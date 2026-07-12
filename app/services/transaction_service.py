from sqlalchemy.orm import Session

from app.repositories.transaction_repository import TransactionRepository


class TransactionService:

    @staticmethod
    def create_transaction(db: Session, transaction):
        return TransactionRepository.create(
            db,
            transaction.model_dump()
        )

    @staticmethod
    def get_transactions(db: Session):
        return TransactionRepository.get_all(db)