import json
import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """Initialize logging based on settings."""
    log_level = logging.getLevelName(settings.log_level)

    if settings.structured_logging:
        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "logger": record.name,
                }
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                return json.dumps(log_data)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())

        # Reset default handlers
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        root.addHandler(handler)
        root.setLevel(log_level)
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
