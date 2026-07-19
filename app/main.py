from fastapi import FastAPI

from app.database.db import engine
from app.database.base import Base
import app.models
from app.core.handlers import register_exception_handlers
from app.core.middleware import RequestContextLoggingMiddleware

from app.api.users import router as user_router
from app.api.transactions import router as transaction_router
from app.api.bot import router as bot_router

app = FastAPI(title="Ledgerly API")
app.add_middleware(RequestContextLoggingMiddleware)
register_exception_handlers(app)

app.include_router(user_router)
app.include_router(transaction_router)
app.include_router(bot_router)


@app.get("/")
def root():
    return {"message": "Ledgerly API Running 🚀"}