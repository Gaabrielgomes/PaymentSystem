from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.payment import Payment
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
    db.commit()
    db.refresh(payment)
    return payment