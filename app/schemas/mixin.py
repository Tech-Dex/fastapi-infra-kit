from fastapi_pagination.cursor import CursorPage

from app.schemas.bucket import BucketResponse
from app.schemas.event import EventResponse


class BucketEventMixin(BucketResponse):
    event: EventResponse


class BucketEventsMixin(BucketResponse):
    events: CursorPage[EventResponse]
