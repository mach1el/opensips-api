import asyncpg
from typing import Optional
from app.core.config import settings

_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
  global _pool
  if _pool is None:
    _pool = await asyncpg.create_pool(
      host=settings.POSTGRES_HOST,
      port=settings.POSTGRES_PORT,
      user=settings.POSTGRES_USER,
      password=settings.POSTGRES_PASSWORD,
      database=settings.POSTGRES_DB,
      min_size=1,
      max_size=5,
    )
  return _pool
