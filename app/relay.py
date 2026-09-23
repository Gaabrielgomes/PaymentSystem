import time
import json
import pika
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.outbox_event import OutboxEvent

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

        db.commit()
        if pending:
            print(f"{len(pending)} published event(s).")
    finally:
        db.close()
        connection.close()

if __name__ == "__main__":
    while True:
        publish_pending_events()
        time.sleep(5)