"""
Centralized logging configuration for Zalanko backend.
Provides structured logging with request tracing capabilities.
"""

import logging
import sys
from typing import Optional
from uuid import uuid4
from contextvars import ContextVar
from config.settings import settings


# Context variable for request tracing
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request ID in log messages."""

    def format(self, record):
        # Add request ID to log record
        request_id = request_id_ctx.get()
        if request_id:
            record.request_id = request_id
        else:
            record.request_id = "no-request"

        return super().format(record)


def setup_logging() -> None:
    """Configure application logging."""

    # Create formatter
    formatter = RequestFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(console_handler)

    # Set specific logger levels
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID for tracing. Returns the request ID."""
    if request_id is None:
        request_id = str(uuid4())[:8]

    request_id_ctx.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return request_id_ctx.get()