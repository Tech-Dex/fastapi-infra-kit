from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.core import ConfigModel


class BucketResponse(ConfigModel):
    id: UUID = Field(..., description="Event ID")
    name: str = Field(..., min_length=1, max_length=255, description="Bucket name")
    created_at: datetime = Field(..., description="Bucket creation time")
    updated_at: datetime = Field(..., description="Bucket update time")
    deleted_at: Optional[datetime] = Field(
        None, description="Bucket deletion time, if applicable"
    )
