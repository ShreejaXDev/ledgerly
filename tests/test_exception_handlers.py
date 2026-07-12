from datetime import date, timedelta


def test_user_already_exists_returns_409(client):
    payload = {
        "telegram_id": "123456",
        "username": "ledger_user",
        "first_name": "Alice",
    }

    first = client.post("/users/", json=payload)
    assert first.status_code == 200

    second = client.post("/users/", json=payload)
    assert second.status_code == 409
    assert second.json() == {"message": "User already exists"}


def test_transaction_not_found_returns_404(client):
    response = client.get("/transactions/99999")

    assert response.status_code == 404
    assert response.json() == {"message": "Transaction not found"}


def test_invalid_transaction_returns_400(client):
    user_payload = {
        "telegram_id": "654321",
        "username": "ledger_user_two",
        "first_name": "Bob",
    }
    user_response = client.post("/users/", json=user_payload)
    assert user_response.status_code == 200
    user_id = user_response.json()["id"]

    invalid_transaction_payload = {
        "user_id": user_id,
        "amount": 15.75,
        "transaction_type": "expense",
        "category": "food",
        "description": "Lunch",
        "merchant": "Cafe",
        "transaction_date": (date.today() + timedelta(days=1)).isoformat(),
    }
    response = client.post("/transactions/", json=invalid_transaction_payload)

    assert response.status_code == 400
    assert response.json() == {"message": "Invalid transaction"}
