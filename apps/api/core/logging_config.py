"""Structured logging configuration with JSON and text formatters."""

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


def setup_logging(log_level: str = "INFO", log_format: str = "text") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)

    if log_format.lower() == "json":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logging.basicConfig(level=level, handlers=[handler], force=True)
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
            force=True,
        )


class CorrelationFilter(logging.Filter):
    """Add correlation_id from request state to log records."""

    def __init__(self, get_correlation_id):
        super().__init__()
        self._get_id = get_correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        cid = self._get_id()
        if cid:
            record.correlation_id = cid
        return True
