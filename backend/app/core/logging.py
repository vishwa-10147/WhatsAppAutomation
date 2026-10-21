import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer() if settings.app_env == "production"
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.app_env == "development" else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "") -> structlog.BoundLogger:
    return structlog.get_logger(name)


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("request")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import time
        start_time = time.time()

        # Headers in ASGI scope are a list of (name, value) tuples
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode() or \
                     structlog.contextvars.get_contextvars().get("request_id", "-")

        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                self.logger.info(
                    "http_request",
                    method=scope["method"],
                    path=scope["path"],
                    status_code=message["status"],
                    process_time_ms=round(process_time * 1000, 2),
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)


configure_logging()