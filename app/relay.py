import time
import json
import pika
from prometheus_client import start_http_server
from app.db.session import SessionLocal
from app.models.outbox_event import OutboxEvent
from app.core.config import settings
from app.core.log_config import setup_logging
from app.core.metrics import outbox_events_published_total

logger = setup_logging("relay")
QUEUE_NAME = "payments_events"

def get_channel():
    credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_pass)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost", credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    return connection, channel

def publish_pending_events():
    db = SessionLocal()
    try:
        connection, channel = get_channel()
    except Exception:
        db.close()
        raise

    try:
        pending = db.query(OutboxEvent).filter(OutboxEvent.status == "PENDING").all()

        for event in pending:
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=json.dumps(event.payload),
                properties=pika.BasicProperties(
                    message_id=str(event.id),
                    delivery_mode=2,
                ),
            )
            event.status = "PUBLISHED"
            db.add(event)
            outbox_events_published_total.inc()

        db.commit()
        if pending:
            logger.info(f"{len(pending)} published event(s).")
    finally:
        db.close()
        connection.close()

if __name__ == "__main__":
    start_http_server(8001)
    logger.info("Metrics server for relay available at port :8001/metrics")
    while True:
        publish_pending_events()
        time.sleep(5)