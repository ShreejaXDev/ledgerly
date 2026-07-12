from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    telegram_id: str
    username: str = Field(min_length=3, max_length=30)
    first_name: str = Field(min_length=2)


class UserResponse(BaseModel):
    id: int
    telegram_id: str
    username: str
    first_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)