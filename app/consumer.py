import json
import pika
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.models.processed_event import ProcessedEvent
from app.core.config import settings
from prometheus_client import start_http_server
from app.core.log_config import setup_logging
from app.core.metrics import consumer_events_processed_total, consumer_events_duplicate_total

logger = setup_logging("consumer")
QUEUE_NAME = "payments_events"

def process_payment_event(payload: dict):
    print(f"Processing payment: {payload}")

def on_message(channel, method, properties, body):
    event_id = properties.message_id
    db = SessionLocal()
    try:
        already_processed = db.query(ProcessedEvent).filter(
            ProcessedEvent.event_id == event_id
        ).first()

        if already_processed:
            consumer_events_duplicate_total.inc()
            logger.info(f"Event {event_id} already processed, ignoring.")
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        payload = json.loads(body)
        process_payment_event(payload)
        consumer_events_processed_total.inc()

        try:
            db.add(ProcessedEvent(event_id=event_id))
            db.commit()
        except IntegrityError:
            db.rollback()
            print(f"Event {event_id} already processed by another instance.")

        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing event {event_id}: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        db.close()

def main():
    credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_pass)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)

    start_http_server(8002)
    logger.info("Metrics server for consumer available at port :8002/metrics")
    channel.start_consuming()

if __name__ == "__main__":
    main()