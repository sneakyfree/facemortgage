"""
Structured logging configuration for FaceMortgage.

Provides JSON-formatted logs for production environments and human-readable
logs for development.
"""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Optional

from src.app.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs log records as JSON objects for easy parsing by log aggregation
    systems like ELK, Datadog, or CloudWatch.
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_path: bool = True,
        extra_fields: Optional[dict[str, Any]] = None,
    ):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_path = include_path
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        log_data: dict[str, Any] = {}

        # Add timestamp
        if self.include_timestamp:
            log_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add log level
        if self.include_level:
            log_data["level"] = record.levelname

        # Add logger name
        if self.include_logger:
            log_data["logger"] = record.name

        # Add message
        log_data["message"] = record.getMessage()

        # Add source location
        if self.include_path:
            log_data["path"] = f"{record.pathname}:{record.lineno}"
            log_data["function"] = record.funcName

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "taskName", "message",
            ):
                try:
                    json.dumps(value)  # Check if serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        # Add static extra fields
        log_data.update(self.extra_fields)

        return json.dumps(log_data, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development environments.

    Uses colors and formatting to make logs easy to scan in terminal.
    """

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with colors for terminal output."""
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET

        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build the message
        message = f"{color}{timestamp} | {record.levelname:8s}{reset} | {record.name} | {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging() -> None:
    """
    Configure logging based on the current environment.

    - Production: JSON formatted logs, INFO level by default
    - Development: Human-readable colored logs, DEBUG level

    Also configures log levels for third-party libraries to reduce noise.
    """
    # Determine log level from settings
    log_level_name = getattr(settings, "log_level", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Determine environment
    environment = getattr(settings, "environment", "development").lower()
    is_production = environment in ("production", "prod", "staging")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter based on environment
    if is_production:
        formatter = JSONFormatter(
            extra_fields={
                "service": "facemortgage-api",
                "environment": environment,
            }
        )
    else:
        formatter = DevelopmentFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure third-party library log levels
    # These are typically too verbose at DEBUG level
    third_party_loggers = {
        "uvicorn": logging.INFO,
        "uvicorn.access": logging.WARNING,
        "uvicorn.error": logging.INFO,
        "fastapi": logging.INFO,
        "sqlalchemy": logging.WARNING,
        "sqlalchemy.engine": logging.WARNING,
        "sqlalchemy.pool": logging.WARNING,
        "aiosqlite": logging.WARNING,
        "asyncpg": logging.WARNING,
        "httpx": logging.WARNING,
        "httpcore": logging.WARNING,
        "hpack": logging.WARNING,
        "redis": logging.WARNING,
        "aiobotocore": logging.WARNING,
        "botocore": logging.WARNING,
        "boto3": logging.WARNING,
        "s3transfer": logging.WARNING,
        "urllib3": logging.WARNING,
        "websockets": logging.INFO,
        "watchfiles": logging.WARNING,
        "stripe": logging.WARNING,
    }

    for logger_name, level in third_party_loggers.items():
        # Only set if log level is lower than configured
        # This prevents silencing them if user explicitly wants DEBUG
        if log_level > logging.DEBUG:
            logging.getLogger(logger_name).setLevel(level)
        else:
            # In debug mode, allow third-party loggers to log at INFO minimum
            logging.getLogger(logger_name).setLevel(max(level, logging.DEBUG))

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level_name,
            "environment": environment,
            "formatter": "json" if is_production else "development",
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Convenience function for getting loggers throughout the application.

    Args:
        name: The logger name, typically __name__ of the calling module.

    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)
