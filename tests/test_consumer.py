import json
import uuid
from unittest.mock import MagicMock
from app.consumer import on_message
from app.models.processed_event import ProcessedEvent


def test_duplicate_event_processed_only_once(consumer_session_factory, monkeypatch):
    event_id = str(uuid.uuid4())
    payload = json.dumps({"payment_id": "abc-123", "amount": "10.00"}).encode()

    calls = []
    monkeypatch.setattr("app.consumer.process_payment_event", lambda p: calls.append(p))

    channel = MagicMock()
    method = MagicMock(delivery_tag=1)
    properties = MagicMock(message_id=event_id)

    on_message(channel, method, properties, payload)
    on_message(channel, method, properties, payload)

    assert len(calls) == 1, "the business effect shouldn't run twice"
    assert channel.basic_ack.call_count == 2, "both deliveries should be confirmed to the broker"

    check_session = consumer_session_factory()
    count = check_session.query(ProcessedEvent).filter(ProcessedEvent.event_id == event_id).count()
    assert count == 1