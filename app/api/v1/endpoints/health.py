from fastapi import APIRouter
from app.core import settings

router = APIRouter()

@router.get("/healthz")
async def healthz():
  return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}
