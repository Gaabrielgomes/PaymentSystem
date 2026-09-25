from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.log_config import setup_logging
from app.core.metrics import payments_created_total, payments_duplicate_blocked_total
from app.db.session import get_db
from app.models.outbox_event import OutboxEvent
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentResponse

logger = setup_logging("api")

router = APIRouter(prefix="/payments", tags=["payments"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=PaymentResponse, status_code=201)
def create_payment(payload: PaymentCreate, db: DbSession):
    existing = (
        db.query(Payment)
        .filter(Payment.idempotency_key == payload.idempotency_key)
        .first()
    )

    if existing:
        payments_duplicate_blocked_total.inc()
        logger.info(f"Repeated idempotency key: {payload.idempotency_key}")
        return existing

    payment = Payment(
        idempotency_key=payload.idempotency_key,
        amount=payload.amount,
        payer_name=payload.payer_name,
        status="PENDING",
    )
    db.add(payment)

    try:
        db.flush()

        event = OutboxEvent(
            aggregate_id=payment.id,
            payload={
                "payment_id": str(payment.id),
                "idempotency_key": payment.idempotency_key,
                "amount": str(payment.amount),
                "payer_name": payment.payer_name,
            },
            status="PENDING",
        )
        db.add(event)
        db.commit()
        payments_created_total.inc()
        logger.info(f"Payment created: {payment.id}")
    except IntegrityError:
        db.rollback()
        payments_duplicate_blocked_total.inc()
        logger.info(f"Concurrency issue detected for key: {payload.idempotency_key}")
        return (
            db.query(Payment)
            .filter(Payment.idempotency_key == payload.idempotency_key)
            .first()
        )

    db.refresh(payment)
    return payment
