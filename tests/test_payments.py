def test_create_payment_success(client):
    response = client.post("/payments", json={
        "idempotency_key": "test-key-001",
        "amount": "100.00",
        "payer_name": "Tester",
    })

    assert response.status_code == 201
    data = response.json()
    assert data["idempotency_key"] == "test-key-001"
    assert data["status"] == "PENDING"


def test_duplicate_idempotency_key_returns_same_payment(client):
    payload = {
        "idempotency_key": "test-key-002",
        "amount": "50.00",
        "payer_name": "Tester2",
    }

    first = client.post("/payments", json=payload)
    second = client.post("/payments", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]