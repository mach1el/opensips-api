from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import settings
from app.core import setup_logging
from app.api.v1 import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
  setup_logging(settings.LOG_LEVEL)
  yield

def create_app() -> FastAPI:
  app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
  )

  app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

  app.include_router(api_router, prefix=settings.API_PREFIX)
  return app

app = create_app()
