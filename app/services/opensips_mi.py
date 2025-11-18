import logging
from typing import Any, Dict

import httpx
from app.core import settings

logger = logging.getLogger(__name__)


async def mi_execute(command: str) -> Dict[str, Any]:
  """
  Call OpenSIPS MI JSON-RPC to excute command.

  curl equivalent:
    curl -X POST localhost:8989/mi \
      -H 'Content-Type: application/json' \
      -d '{"jsonrpc": "2.0", "id": "1", "method": "dp_reload"}'

  Returns the parsed JSON-RPC response, or a synthetic error object
  if the HTTP request fails.
  """
  host = getattr(settings, "OPENSIPS_MI_HOST", "localhost")
  port = getattr(settings, "OPENSIPS_MI_PORT", 8989)

  url = f"http://{host}:{port}/mi"
  payload: Dict[str, Any] = {
    "jsonrpc": "2.0",
    "id": "1",
    "method": command,
  }

  try:
    async with httpx.AsyncClient() as client:
      resp = await client.post(url, json=payload, timeout=5.0)
      resp.raise_for_status()

      try:
        data = resp.json()
      except ValueError:
        # Not JSON, wrap as error-like object
        logger.warning(f"OpenSIPS MI {command} non-JSON response: %s", resp.text)
        data = {
          "jsonrpc": "2.0",
          "error": {
            "code": -32700,
            "message": "Parse error: non-JSON response from MI",
            "raw": resp.text,
          },
          "id": payload["id"],
        }

      logger.info(f"OpenSIPS MI {command} response: %s", data)
      return data

  except httpx.RequestError as e:
    logger.error(f"Error calling OpenSIPS MI {command}: %s", e)
    return {
      "jsonrpc": "2.0",
      "error": {
        "code": -32000,
        "message": f"Network error calling MI: {e}",
      },
      "id": payload["id"],
    }

  except httpx.HTTPStatusError as e:
    logger.error(
      f"OpenSIPS MI {command} returned bad status %s: %s",
      e.response.status_code,
      e.response.text,
    )
    return {
      "jsonrpc": "2.0",
      "error": {
        "code": -32001,
        "message": f"HTTP {e.response.status_code} from MI",
        "raw": e.response.text,
      },
      "id": payload["id"],
    }
