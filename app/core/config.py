from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List
import os

class Settings(BaseSettings):
  model_config = SettingsConfigDict(extra="ignore")

  APP_NAME: str = "custom-dialplan"
  APP_VERSION: str = "0.4.0"
  ENV: str = os.getenv("ENV", "prod")
  API_PREFIX: str = "/api/v1"
  LOG_LEVEL: str = "INFO"

  CORS_ORIGINS: List[str] = ["*"]

  API_KEY: str = Field(
    ...,
    description="Global API key required to access the API"
  )
  API_KEY_HEADER_NAME: str = Field(
    "X-API-Key",
    description="HTTP header name that carries the API key"
  )

  DATABASE_URL: str | None = None
  POSTGRES_USER: str = "postgres"
  POSTGRES_PASSWORD: str = "postgres"
  POSTGRES_HOST: str = "localhost"
  POSTGRES_PORT: int = 5432
  POSTGRES_DB: str = "postgres"

  DB_POOL_SIZE: int = 5
  DB_MAX_OVERFLOW: int = 10

  OPENSIPS_MI_HOST: str = "localhost"
  OPENSIPS_MI_PORT: int = 8989

  @field_validator("CORS_ORIGINS", mode="before")
  @classmethod
  def split_cors(cls, v):
    if isinstance(v, str):
      return [s.strip() for s in v.split(",") if s.strip()]
    return v

  @field_validator("API_KEY")
  def validate_api_key(cls, v: str) -> str:
    if not v or not v.strip():
      raise ValueError("API_KEY cannot be empty")
    return v
  
  @field_validator("DATABASE_URL", mode="before")
  @classmethod
  def _assemble_db_url(cls, v):
    """
    Compose DATABASE_URL if not explicitly provided.
    Uses async driver `asyncpg` for SQLAlchemy 2.x.
    """
    if v and str(v).strip():
      return v

    user = os.getenv("POSTGRES_USER", "postgres")
    pwd = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "custom_dialplan")
    return f"postgresql+asyncpg://{user}:{pwd}@{host}:{port}/{db}"

  @field_validator("OPENSIPS_MI_HOST")
  def validate_opensips_host(cls, v):
    if not v or not v.strip():
      raise ValueError("OPENSIPS_MI_HOST cannot be empty")
    return v

  @field_validator("OPENSIPS_MI_PORT")
  def validate_opensips_port(cls, v):
    if not (1 <= v <= 65535):
      raise ValueError("OPENSIPS_MI_PORT must be between 1 and 65535")
    return v

settings = Settings()