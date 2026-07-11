from pydantic import BaseModel


class UserCreate(BaseModel):
    telegram_id: str
    username: str
    first_name: str


class UserResponse(UserCreate):
    id: int

    class Config:
        from_attributes = True