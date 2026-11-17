import logging
import sys
from typing import Any, Dict
import structlog
from contextvars import ContextVar

# Context variables for distributed request tracing
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")
tenant_id_ctx: ContextVar[str] = ContextVar("tenant_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")


def add_correlation_context(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Injects correlation, tenant, and user IDs into structured log records."""
    corr_id = correlation_id_ctx.get()
    if corr_id:
        event_dict["correlation_id"] = corr_id
    org_id = tenant_id_ctx.get()
    if org_id:
        event_dict["organization_id"] = org_id
    u_id = user_id_ctx.get()
    if u_id:
        event_dict["user_id"] = u_id
    return event_dict


def setup_logging(debug: bool = False) -> None:
    """Configures structured JSON logging for production and human-readable logging in debug."""
    log_level = logging.DEBUG if debug else logging.INFO

    # Configure standard library logging handler
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        add_correlation_context,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if debug:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "redthread") -> structlog.stdlib.BoundLogger:
    """Returns a pre-configured structured logger."""
    return structlog.get_logger(name)
