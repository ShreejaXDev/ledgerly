import httpx

BASE_URL = "http://127.0.0.1:8000"


async def send_message_to_backend(payload: dict) -> dict:
    """Send the full Telegram user payload to the FastAPI backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/message",
            json=payload,
        )
        return response.json()