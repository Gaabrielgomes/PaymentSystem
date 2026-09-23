
# PaymentSystem

A payment processing system built as a portfolio project, applying engineering patterns used in real financial systems: idempotency guarantees, atomic writes via the transactional outbox pattern, asynchronous processing with messaging, and observability.

Processed payments are **fictitious** — the project does not yet integrate with any real payment gateway (Pix, card, boleto) but it will sooner. The focus for now is on consistency and non-duplication guarantees.

## Why this project exists

Most junior portfolios show basic CRUD. This project solves a real engineering problem: guaranteeing that a payment request is never processed twice, even under concurrent requests, network failures, or message redelivery — the same kind of guarantee real financial production systems need to uphold.

## Architecture

```
Client
   |
   v
REST API (FastAPI)
  - Receives payment request
  - Validates idempotency key
   |
   | 1 atomic transaction
   v
PostgreSQL
  - payments table
  - outbox_events table
   |
   | periodic read
   v
Outbox Relay
  (publishes pending events every 5s)
   |
   v
RabbitMQ (payments_events queue)
   |
   v
Consumer (idempotent)
  - Checks if event was already processed
  - Applies the business effect
```

**Guarantees implemented:**

| Guarantee                  | Where        | How                                                                                               |
| -------------------------- | ------------ | ------------------------------------------------------------------------------------------------- |
| Idempotency on input       | API          | `unique` constraint on `idempotency_key`, checked before creation                             |
| Database/event consistency | API          | `payment` and `outbox_event` written in the same transaction (outbox pattern)                 |
| Concurrency                | API          | `IntegrityError` caught when two simultaneous requests race for the same key                    |
| Publishing resilience      | Outbox Relay | Event stays`PENDING` if the broker fails; retried on the next cycle                             |
| Idempotency on consumption | Consumer     | `processed_events` table with `event_id` as primary key; protects against RabbitMQ redelivery |

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL, Alembic (migrations)
- **Messaging:** RabbitMQ (pika)
- **Observability:** structured logging per service, Prometheus metrics
- **Testing:** pytest, Testcontainers
- **Local infrastructure:** Docker Compose

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git

## Environment setup

1. Clone the repository and create the virtual environment:

   ```bash
   git clone <repository-url>
   cd PaymentSystem
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file at the project root (not versioned) based on `.env.example`:

   ```
   POSTGRES_USER=payment_user
   POSTGRES_PASSWORD=your_local_password
   POSTGRES_DB=payments
   DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5433/${POSTGRES_DB}
   RABBITMQ_USER=payment_user
   RABBITMQ_PASSWORD=your_local_password
   ```

   **Note:** Postgres runs on port `5433` (not the default `5432`), to avoid conflicting with a native Postgres installation that might already exist on the machine.
3. Start the containers:

   ```bash
   docker compose up -d
   docker compose ps   # confirm payment_db and payment_rabbitmq show "running"
   ```
4. Apply the migrations:

   ```bash
   alembic upgrade head
   ```

## Running the application

Three independent processes, each in its own terminal:

```bash
uvicorn app.main:app --reload      # API — http://localhost:8000
python -m app.relay                # Outbox Relay
python -m app.consumer             # Consumer
```

Interactive API docs: `http://localhost:8000/docs`

## Manual testing

```bash
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"idempotency_key": "abc-123", "amount": 150.00, "payer_name": "John Doe"}'
```

Repeating the same request with the same `idempotency_key` should return the same `id`, without creating a new record.

## Automated tests

```bash
pytest tests/ -v
```

The suite covers the five guarantees listed above, including a real concurrency test (multiple threads racing for the same `idempotency_key`) and tests simulating broker failure and message redelivery.

## Observability

Each service exposes its own Prometheus metrics:

| Service      | Endpoint                          |
| ------------ | --------------------------------- |
| API          | `http://localhost:8000/metrics` |
| Outbox Relay | `http://localhost:8001/metrics` |
| Consumer     | `http://localhost:8002/metrics` |

RabbitMQ management panel: `http://localhost:15672`

## Project structure

```
app/
├── core/          # config, logging, metrics
├── db/            # SQLAlchemy connection and base
├── models/        # entities (Payment, OutboxEvent, ProcessedEvent)
├── schemas/       # Pydantic input/output schemas
├── routers/       # API endpoints
├── main.py        # FastAPI application
├── relay.py       # outbox relay
└── consumer.py    # idempotent consumer
tests/             # automated test suite
alembic/           # migrations
```

## Current status and next steps

Completed: API with idempotency, outbox pattern, messaging, idempotent consumer, automated tests for the five core guarantees, observability.

Planned: integration with bank APIs, OAuth2 authentication, HTTPS.

## License

Personal portfolio project, no commercial usage license defined.
