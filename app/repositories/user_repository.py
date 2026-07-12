from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:

    @staticmethod
    def create(db: Session, user_data: dict):
        user = User(**user_data)

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_all(db: Session):
        return db.query(User).all()