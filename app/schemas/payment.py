import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    idempotency_key: str
    amount: Decimal
    payer_name: str


class PaymentResponse(BaseModel):
    id: uuid.UUID
    idempotency_key: str
    amount: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)
