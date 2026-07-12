from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    @staticmethod
    def create(db: Session, user_data: dict) -> User:
        user = User(**user_data)

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_all(db: Session) -> list[User]:
        return db.query(User).all()

    @staticmethod
    def get_by_telegram_id(
        db: Session,
        telegram_id: str,
    ) -> User | None:
        return (
            db.query(User)
            .filter(User.telegram_id == telegram_id)
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )