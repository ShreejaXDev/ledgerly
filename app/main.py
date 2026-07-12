from fastapi import FastAPI

from app.database.db import engine
from app.database.base import Base
import app.models

from app.api.users import router as user_router
from app.api.transactions import router as transaction_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ledgerly API")

app.include_router(user_router)
app.include_router(transaction_router)


@app.get("/")
def root():
    return {"message": "Ledgerly API Running 🚀"}