import threading
from app.models.payment import Payment


def test_concurrent_requests_same_idempotency_key_create_only_one_payment(concurrent_client, db_session):
    payload = {
        "idempotency_key": "concurrent-key-001",
        "amount": "200.00",
        "payer_name": "Concurrent Tester",
    }
    results = []
    errors = []

    def make_request():
        try:
            response = concurrent_client.post("/payments", json=payload)
            results.append(response)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=make_request) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"{len(errors)} request(s) threw unhandled exception: {errors}"
    assert len(results) == 10, f"waited for 10 responses, got {len(results)}"
    assert all(r.status_code == 201 for r in results), [r.status_code for r in results]

    ids = {r.json()["id"] for r in results}
    assert len(ids) == 1, f"waited for one unique payment, found {len(ids)}"

    count_in_db = db_session.query(Payment).filter(
        Payment.idempotency_key == "concurrent-key-001"
    ).count()
    assert count_in_db == 1