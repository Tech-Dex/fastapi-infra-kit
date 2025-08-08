from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.core import ConfigModel


class EventCreate(ConfigModel):
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    message: str = Field(..., min_length=1, description="Event message")


class EventResponse(ConfigModel):
    id: UUID = Field(..., description="Event ID")
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    message: str = Field(..., min_length=1, description="Event message")
    created_at: datetime = Field(..., description="Event creation time")
