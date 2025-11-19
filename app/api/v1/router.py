from fastapi import APIRouter, Depends
from app.core import get_api_key
from .endpoints import health
from .endpoints import dialplan

api_router = APIRouter(dependencies=[Depends(get_api_key)])
api_router.include_router(health.router, tags=["health"])

# ------------------------------ Dialplan Endpoints ------------------------------
api_router.include_router(dialplan.router, prefix="/dialplan", tags=["dialplan"])