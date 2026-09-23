from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import get_db
from app.models.payment import Payment
from app.models.outbox_event import OutboxEvent
from app.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("", response_model=PaymentResponse, status_code=201)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    existing = db.query(Payment).filter(
        Payment.idempotency_key == payload.idempotency_key
    ).first()

    if existing:
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
            aggregate_id = payment.id,
            payload = {
                "payment_id": str(payment.id),
                "idempotency_key": payment.idempotency_key,
                "amount": str(payment.amount),
                "payer_name": payment.payer_name,
            },
            status = "PENDING"
        )
        db.add(event)

        db.commit()
    except IntegrityError:
        db.rollback()
        return db.query(Payment).filter(
            Payment.idempotency_key == payload.idempotency_key
        ).first()

    db.refresh(payment)
    return payment