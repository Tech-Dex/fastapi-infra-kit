from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    message: str = Field(..., min_length=1, description="Event message")


class EventResponse(BaseModel):
    id: UUID = Field(..., description="Event ID")
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    message: str = Field(..., min_length=1, description="Event message")
    created_at: datetime = Field(..., description="Event creation time")

    class Config:
        from_attributes = True
