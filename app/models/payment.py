import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String, unique=True, nullable=False)
    amount = Column(Numeric(19, 2), nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.now)