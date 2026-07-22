from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    telegram_id = Column(
        String,
        unique=True,
        nullable=False
    )

    username = Column(String)

    first_name = Column(String)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    budget = relationship(
        "Budget",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    recurring_transactions = relationship(
        "RecurringTransaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )