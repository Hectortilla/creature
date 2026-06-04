"""Structured logging via structlog over the stdlib ``logging`` module.

Human-friendly console output in development; single-line JSON in production
(``LOG_JSON=true``). Correlation IDs bound by ``asgi-correlation-id`` and the
per-request/per-connection context (see ``game_runner``) are merged into every
log line, so an agent can filter a whole request or game by one id.

The existing ``logging.getLogger(__name__)`` call sites keep working unchanged —
their records are rendered by the same processor chain. See AGENTS.md and
docs/references/observability.md.
"""

from __future__ import annotations

import logging

import structlog


def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Route both structlog and stdlib ``logging`` through one processor chain."""
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
    ]

    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer = structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger. Prefer this over ``logging.getLogger`` in new code."""
    return structlog.get_logger(name)
