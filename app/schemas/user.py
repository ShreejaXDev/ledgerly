from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    telegram_id: str
    username: str
    first_name: str


class UserResponse(BaseModel):
    id: int
    telegram_id: str
    username: str
    first_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)