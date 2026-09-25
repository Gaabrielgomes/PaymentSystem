import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.now)
    processed_at = Column(DateTime, nullable=True)
