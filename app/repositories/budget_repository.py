from sqlalchemy.orm import Session

from app.models.budget import Budget


class BudgetRepository:
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Budget | None:
        return (
            db.query(Budget)
            .filter(Budget.user_id == user_id)
            .first()
        )

    @staticmethod
    def create(db: Session, budget_data: dict) -> Budget:
        budget = Budget(**budget_data)

        db.add(budget)
        db.commit()
        db.refresh(budget)

        return budget

    @staticmethod
    def update(
        db: Session,
        budget: Budget,
        budget_data: dict,
    ) -> Budget:
        for field, value in budget_data.items():
            setattr(budget, field, value)

        db.commit()
        db.refresh(budget)

        return budget