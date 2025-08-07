from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bucket_id = Column(
        UUID(as_uuid=True), ForeignKey("buckets.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    bucket = relationship("Bucket", back_populates="events")

    def __repr__(self):
        return f"<Event(id={self.id}, bucket_id={self.bucket_id}, title={self.title})>"
