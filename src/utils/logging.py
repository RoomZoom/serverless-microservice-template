# src/utils/logging.py
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Union
from utils.config import get_env_variable


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def __init__(self, service_name: Optional[str] = None, environment: Optional[str] = None):
        super().__init__()
        self.service_name = service_name or get_env_variable(
            "SERVICE_NAME", "microservice"
        )
        self.environment = environment or get_env_variable("ENVIRONMENT", "dev")

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                extra_fields[key] = value

        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str)


class CorrelationFilter(logging.Filter):
    """Filter to add correlation ID to log records"""

    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the record"""
        if self.correlation_id:
            record.correlation_id = self.correlation_id
        return True


def setup_logging(
    level: Optional[str] = None,
    service_name: Optional[str] = None,
    environment: Optional[str] = None,
    use_json: Optional[bool] = None,
    correlation_id: Optional[str] = None,
) -> logging.Logger:
    """
    Setup structured logging for the microservice

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name of the service
        environment: Environment name (dev, staging, prod)
        use_json: Whether to use JSON formatting (default: True for prod, False for dev)
        correlation_id: Optional correlation ID to add to all logs

    Returns:
        Configured logger instance
    """
    # Get configuration from environment if not provided
    level = level or get_env_variable("LOG_LEVEL", "INFO") or "INFO"
    service_name = service_name or get_env_variable("SERVICE_NAME", "microservice") or "microservice"
    environment = environment or get_env_variable("ENVIRONMENT", "dev") or "dev"

    # Use JSON formatting by default in production
    if use_json is None:
        use_json = environment.lower() == "prod"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Set formatter
    if use_json:
        formatter = JSONFormatter(service_name, environment)
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)

    # Add correlation filter if provided
    if correlation_id:
        correlation_filter = CorrelationFilter(correlation_id)
        console_handler.addFilter(correlation_filter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    configure_library_loggers()

    return root_logger


def configure_library_loggers():
    """Configure logging for third-party libraries"""
    # Reduce boto3 logging noise
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Reduce Kafka logging noise
    logging.getLogger("kafka").setLevel(logging.WARNING)

    # Reduce FastAPI/uvicorn logging noise in production
    environment = get_env_variable("ENVIRONMENT", "dev") or "dev"
    if environment.lower() == "prod":
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)


def get_logger(name: str, correlation_id: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with optional correlation ID

    Args:
        name: Logger name (usually __name__)
        correlation_id: Optional correlation ID

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # Add correlation filter if provided
    if correlation_id:
        correlation_filter = CorrelationFilter(correlation_id)
        for handler in logger.handlers:
            handler.addFilter(correlation_filter)

    return logger


def log_function_call(func):
    """Decorator to log function calls with execution time"""

    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = datetime.utcnow()

        logger.info(
            f"Calling function {func.__name__}",
            extra={
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            },
        )

        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Function {func.__name__} completed successfully",
                extra={
                    "function": func.__name__,
                    "execution_time_seconds": execution_time,
                },
            )

            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "execution_time_seconds": execution_time,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise

    return wrapper


# Context manager for correlation ID
class CorrelationContext:
    """Context manager to add correlation ID to all logs within a context"""

    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self.original_filters = {}

    def __enter__(self):
        # Add correlation filter to all existing handlers
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            for handler in logger.handlers:
                correlation_filter = CorrelationFilter(self.correlation_id)
                handler.addFilter(correlation_filter)
                self.original_filters[handler] = correlation_filter

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Remove correlation filters
        for handler, correlation_filter in self.original_filters.items():
            handler.removeFilter(correlation_filter)


# Initialize logging when module is imported
setup_logging()
