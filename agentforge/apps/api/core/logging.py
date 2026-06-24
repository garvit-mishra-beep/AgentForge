from __future__ import annotations

import logging
import structlog
from apps.api.core.config import settings


def bootstrap_logging() -> None:
    use_json = settings.ENVIRONMENT != "development" or settings.ENABLE_JSON_LOGS
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if not use_json else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
