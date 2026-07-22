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


async def send_today_summary_to_backend(payload: dict) -> dict:
    """Request today's transaction summary from the FastAPI backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/today",
            json=payload,
        )
        return response.json()


async def send_week_summary_to_backend(payload: dict) -> dict:
    """Request weekly transaction summary from the FastAPI backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/week",
            json=payload,
        )
        return response.json()


async def send_month_summary_to_backend(payload: dict) -> dict:
    """Request monthly transaction summary from the FastAPI backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/month",
            json=payload,
        )
        return response.json()


async def send_overall_summary_to_backend(payload: dict) -> dict:
    """Request the overall transaction summary from the FastAPI backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/summary",
            json=payload,
        )
        return response.json()


async def send_set_budget_to_backend(payload: dict) -> dict:
    """Send a budget amount to the FastAPI backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/setbudget",
            json=payload,
        )
        return response.json()


async def send_budget_summary_to_backend(payload: dict) -> dict:
    """Request the current monthly budget summary from the backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/budget",
            json=payload,
        )
        return response.json()


async def send_insights_to_backend(payload: dict) -> dict:
    """Request monthly financial insights from the backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/insights",
            json=payload,
        )
        return response.json()


async def send_add_recurring_to_backend(payload: dict) -> dict:
    """Create a recurring transaction in the backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/addrecurring",
            json=payload,
        )
        return response.json()


async def send_list_recurring_to_backend(payload: dict) -> dict:
    """List recurring transactions from the backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/listrecurring",
            json=payload,
        )
        return response.json()


async def send_delete_recurring_to_backend(payload: dict) -> dict:
    """Delete a recurring transaction via the backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/deleterecurring",
            json=payload,
        )
        return response.json()


async def send_export_to_backend(payload: dict) -> dict:
    """Request a transaction export file from the backend."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/bot/export",
            json=payload,
        )
        return response.json()