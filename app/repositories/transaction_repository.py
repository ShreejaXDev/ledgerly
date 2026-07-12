from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:

    @staticmethod
    def create(db: Session, transaction_data: dict) -> Transaction:
        transaction = Transaction(**transaction_data)

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    @staticmethod
    def get_all(db: Session) -> list[Transaction]:
        return db.query(Transaction).all()

    @staticmethod
    def get_by_id(
        db: Session,
        transaction_id: int,
    ) -> Transaction | None:
        return (
            db.query(Transaction)
            .filter(Transaction.id == transaction_id)
            .first()
        )