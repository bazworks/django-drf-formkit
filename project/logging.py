import os
import sys

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
USE_JSON_LOGS = os.getenv("USE_JSON_LOGS", "false").lower() in ["1", "true", "yes"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[{levelname}] {asctime} {name} | {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json" if USE_JSON_LOGS else "default",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "myapp": {  # Example for your Django app
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}  # You can import this LOGGING dict in your settings.py
