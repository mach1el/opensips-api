from fastapi import APIRouter
from .endpoints import health
from .endpoints import dialplan

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])

#-------------------------------------- Dialplan Endpoints -------------------------------------- 
api_router.include_router(dialplan.router, prefix="/dialplan", tags=["dialplan"])