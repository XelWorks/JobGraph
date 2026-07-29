import json
import logging
import re
import sys
from typing import Any, Dict

from app.core.config import settings

# Sensitive fields and pattern list to automatically redact from JSON log records
SENSITIVE_KEYS = {
    "password", "pass", "token", "secret", "key",
    "authorization", "auth", "credential"
}

SECRET_PATTERNS = [
    (re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"(password|secret|key|token)=([^\s&]+)", re.IGNORECASE), r"\1=[REDACTED]"),
    (re.compile(r"AIza[0-9A-Za-z-_]{35}"), "[REDACTED_GEMINI_KEY]"),
]


def redact_sensitive_data(data: Any) -> Any:
    """Recursively traverses dict/list structures or strings to redact secret parameters."""
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            k_lower = k.lower()
            # If the dictionary key contains any sensitive keyword substring or exact match
            if any(s in k_lower for s in SENSITIVE_KEYS):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = redact_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        cleaned_str = data
        for pattern, replacement in SECRET_PATTERNS:
            cleaned_str = pattern.sub(replacement, cleaned_str)
        return cleaned_str
    return data


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter with automated secret redaction for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "message": redact_sensitive_data(record.getMessage()),
            "logger": record.name,
        }

        # Include custom extra fields passed to logger
        for k, v in record.__dict__.items():
            if k not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "msg", "name", "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName", "taskName", "message"
            }:
                if isinstance(k, str) and any(s in k.lower() for s in SENSITIVE_KEYS):
                    log_data[k] = "[REDACTED]"
                else:
                    log_data[k] = redact_sensitive_data(v)

        if record.exc_info:
            log_data["exception"] = redact_sensitive_data(self.formatException(record.exc_info))

        return json.dumps(log_data)


def setup_logging() -> None:
    """Initialize logging based on settings."""
    log_level = logging.getLevelName(settings.log_level)

    if settings.structured_logging:
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

