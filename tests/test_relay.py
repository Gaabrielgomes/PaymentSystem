import uuid
import pytest
import pika
from unittest.mock import patch, MagicMock
from app.models.payment import Payment
from app.models.outbox_event import OutboxEvent
from app.relay import publish_pending_events


def _create_pending_event(session):
    payment = Payment(
        idempotency_key=f"relay-{uuid.uuid4()}",
        amount="10.00",
        payer_name="Relay Tester",
        status="PENDING",
    )
    session.add(payment)
    session.flush()
    event = OutboxEvent(aggregate_id=payment.id, payload={"payment_id": str(payment.id)}, status="PENDING")
    session.add(event)
    session.commit()
    return event.id


def test_broker_failure_keeps_event_pending(relay_session_factory):
    session = relay_session_factory()
    event_id = _create_pending_event(session)

    with patch("app.relay.pika.BlockingConnection", side_effect=Exception("broker unavailable")):
        try:
            with pytest.raises(pika.exceptions.AMQPConnectionError):
                publish_pending_events()
        except Exception:
            pass

    check_session = relay_session_factory()
    event = check_session.query(OutboxEvent).filter(OutboxEvent.id == event_id).first()
    assert event.status == "PENDING"


def test_broker_recovery_publishes_pending_event(relay_session_factory):
    session = relay_session_factory()
    event_id = _create_pending_event(session)

    fake_channel = MagicMock()
    fake_connection = MagicMock()
    fake_connection.channel.return_value = fake_channel

    with patch("app.relay.pika.BlockingConnection", return_value=fake_connection):
        publish_pending_events()
        
    published_ids = [
        call.kwargs["properties"].message_id
        for call in fake_channel.basic_publish.call_args_list
    ]
    assert str(event_id) in published_ids

    check_session = relay_session_factory()
    event = check_session.query(OutboxEvent).filter(OutboxEvent.id == event_id).first()
    assert event.status == "PUBLISHED"