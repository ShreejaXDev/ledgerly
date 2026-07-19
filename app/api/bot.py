from fastapi import APIRouter

router = APIRouter(
    prefix="/bot",
    tags=["Bot"]
)

@router.post("/message")
async def process_message(payload: dict):
    text = payload.get("message", "")

    return {
        "reply": f"I received: {text}"
    }