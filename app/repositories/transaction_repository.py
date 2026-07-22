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
    def get_by_user_and_date(
        db: Session,
        user_id: int,
        transaction_date,
    ) -> list[Transaction]:
        return (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.transaction_date == transaction_date)
            .all()
        )

    @staticmethod
    def get_by_user_and_date_range(
        db: Session,
        user_id: int,
        start_date,
        end_date,
    ) -> list[Transaction]:
        return (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.transaction_date >= start_date)
            .filter(Transaction.transaction_date <= end_date)
            .order_by(Transaction.transaction_date.asc(), Transaction.id.asc())
            .all()
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int,
    ) -> list[Transaction]:
        return (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.asc(), Transaction.id.asc())
            .all()
        )

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