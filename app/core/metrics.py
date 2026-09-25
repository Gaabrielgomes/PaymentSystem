from prometheus_client import Counter

payments_created_total = Counter(
    "payments_created_total", "Total of new payments created"
)
payments_duplicate_blocked_total = Counter(
    "payments_duplicate_blocked_total", "Total of duplicate attempts blocked by idempotency"
)
outbox_events_published_total = Counter(
    "outbox_events_published_total", "Total of events published by the outbox relay"
)
consumer_events_processed_total = Counter(
    "consumer_events_processed_total", "Total of events processed successfully by the consumer"
)
consumer_events_duplicate_total = Counter(
    "consumer_events_duplicate_total", "Total of duplicate events ignored by the consumer"
)