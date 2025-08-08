from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.core import CoreBase


class Bucket(CoreBase):
    __tablename__ = "buckets"

    name = Column(String(255), unique=True, nullable=False, index=True)

    events = relationship(
        "Event", back_populates="bucket", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Bucket(id={self.id}, name={self.name})>"
