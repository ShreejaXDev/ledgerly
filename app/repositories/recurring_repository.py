from datetime import date

from sqlalchemy.orm import Session

from app.models.recurring_transaction import RecurringTransaction


class RecurringRepository:
    @staticmethod
    def create(db: Session, recurring_data: dict) -> RecurringTransaction:
        recurring = RecurringTransaction(**recurring_data)

        db.add(recurring)
        db.commit()
        db.refresh(recurring)

        return recurring

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> list[RecurringTransaction]:
        return (
            db.query(RecurringTransaction)
            .filter(RecurringTransaction.user_id == user_id)
            .order_by(
                RecurringTransaction.next_execution_date.asc(),
                RecurringTransaction.id.asc(),
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        recurring_id: int,
    ) -> RecurringTransaction | None:
        return (
            db.query(RecurringTransaction)
            .filter(RecurringTransaction.id == recurring_id)
            .first()
        )

    @staticmethod
    def delete(db: Session, recurring: RecurringTransaction) -> None:
        db.delete(recurring)
        db.commit()

    @staticmethod
    def update(
        db: Session,
        recurring: RecurringTransaction,
        recurring_data: dict,
    ) -> RecurringTransaction:
        for field, value in recurring_data.items():
            setattr(recurring, field, value)

        db.commit()
        db.refresh(recurring)

        return recurring

    @staticmethod
    def get_due_recurring_transactions(
        db: Session,
        current_date: date,
    ) -> list[RecurringTransaction]:
        return (
            db.query(RecurringTransaction)
            .filter(RecurringTransaction.is_active.is_(True))
            .filter(RecurringTransaction.next_execution_date <= current_date)
            .all()
        )