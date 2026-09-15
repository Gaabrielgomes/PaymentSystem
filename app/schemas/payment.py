import uuid
from decimal import Decimal
from pydantic import BaseModel

class PaymentCreate(BaseModel):
    idempotency_key: str
    amount: Decimal
    payer_name: str

class PaymentResponse(BaseModel):
    id: uuid.UUID
    idempotency_key: str
    amount: Decimal
    status: str

    class Config:
        from_attributes = True