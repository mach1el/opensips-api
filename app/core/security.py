from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.core import settings

api_key_header = APIKeyHeader(
  name=settings.API_KEY_HEADER_NAME,
  auto_error=False,
)

async def get_api_key(api_key_header_value: str = Security(api_key_header)) -> str:
  """
  Validate incoming API key from header.

  - Header name is configurable via settings.API_KEY_HEADER_NAME (default: X-API-Key)
  - Value must exactly match settings.API_KEY
  """
  if not api_key_header_value:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Missing API key",
    )

  if api_key_header_value != settings.API_KEY:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid API key",
    )

  return api_key_header_value