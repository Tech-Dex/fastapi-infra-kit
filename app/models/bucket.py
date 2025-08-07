from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Bucket(Base):
    __tablename__ = "buckets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    events = relationship(
        "Event", back_populates="bucket", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Bucket(id={self.id}, name={self.name})>"
