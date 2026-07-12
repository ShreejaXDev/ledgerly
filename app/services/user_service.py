from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository


class UserService:

    @staticmethod
    def create_user(db: Session, user):
        return UserRepository.create(
            db,
            user.model_dump()
        )

    @staticmethod
    def get_users(db: Session):
        return UserRepository.get_all(db)