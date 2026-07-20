from pydantic import BaseModel


class TelegramMessage(BaseModel):
    telegram_id: str
    username: str | None = None
    first_name: str
    last_name: str | None = None
    message: str