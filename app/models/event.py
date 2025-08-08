from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.core import CoreBase


class Event(CoreBase):
    __tablename__ = "events"

    bucket_id = Column(
        UUID(as_uuid=True), ForeignKey("buckets.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    bucket = relationship("Bucket", back_populates="events")

    def __repr__(self):
        return f"<Event(id={self.id}, bucket_id={self.bucket_id}, title={self.title}, message={self.message})>"
