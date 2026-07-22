from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    amount = Column(Float, nullable=False)

    description = Column(String, nullable=False)

    category = Column(String, nullable=False)

    transaction_type = Column(String, nullable=False)

    frequency = Column(String, nullable=False)

    next_execution_date = Column(Date, nullable=False)

    last_executed_date = Column(Date)

    is_active = Column(Boolean, nullable=False, server_default=func.true())

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="recurring_transactions")