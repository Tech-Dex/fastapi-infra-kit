from fastapi import APIRouter

from app.api.v1.http import bucket, event

router_http: APIRouter = APIRouter()
PREFIX: str = "/v1"


router_http.include_router(bucket.router, prefix="/buckets", tags=["Bucket"])
router_http.include_router(
    event.router, prefix="/buckets/{bucket_name}/events", tags=["Events"]
)
