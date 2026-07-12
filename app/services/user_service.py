from sqlalchemy.orm import Session

from app.core.exceptions import UserAlreadyExists, UserNotFound
from app.core.logger import logger
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse


class UserService:
    """Business logic for user operations."""

    @staticmethod
    def create_user(
        db: Session,
        user: UserCreate,
    ) -> UserResponse:
        """Create a user after enforcing business constraints."""
        existing_user = UserRepository.get_by_telegram_id(
            db,
            user.telegram_id,
        )
        if existing_user:
            logger.error(
                "User creation failed | telegram_id=%s already exists",
                user.telegram_id,
            )
            raise UserAlreadyExists()

        created_user = UserRepository.create(db, user.model_dump())
        logger.info(
            "User Created | user_id=%s telegram_id=%s",
            created_user.id,
            created_user.telegram_id,
        )
        return UserResponse.model_validate(created_user)

    @staticmethod
    def get_users(db: Session) -> list[UserResponse]:
        """Fetch users as response schemas."""
        users = UserRepository.get_all(db)
        logger.info("User Fetch | count=%s", len(users))
        return [UserResponse.model_validate(user) for user in users]

    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int,
    ) -> UserResponse:
        """Fetch one user by id with domain-level not-found handling."""
        user = UserRepository.get_by_id(db, user_id)
        if user is None:
            logger.error("User fetch failed | user_id=%s not found", user_id)
            raise UserNotFound()

        logger.info("User Fetch | user_id=%s", user_id)
        return UserResponse.model_validate(user)