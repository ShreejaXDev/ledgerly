import httpx

BASE_URL = "http://127.0.0.1:8000"


async def send_message_to_backend(message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/message",
            json={"message": message},
        )
        return response.json()