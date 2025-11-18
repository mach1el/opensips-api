import logging
import logging.config

def setup_logging(level: str = "INFO") -> None:
  config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
      "default": {
        "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
      }
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "formatter": "default",
      }
    },
    "loggers": {
      "uvicorn": {"handlers": ["console"], "level": level},
      "uvicorn.error": {"handlers": ["console"], "level": level},
      "uvicorn.access": {"handlers": ["console"], "level": level},
      "app": {"handlers": ["console"], "level": level},
    },
    "root": {"handlers": ["console"], "level": level},
  }
  logging.config.dictConfig(config)
