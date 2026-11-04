import logging
import sys

import structlog
from asgi_correlation_id import correlation_id

_HANDLER_MARKER = "_doc_qa_handler"
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


def add_request_id(
    logger: object, method_name: str, event_dict: structlog.typing.EventDict
) -> structlog.typing.EventDict:
    """Structlog processor adding the current request's correlation ID as `request_id`.

    Nothing is added outside a request (for example startup logs).
    """
    request_id = correlation_id.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(level: str = "INFO", *, json_logs: bool = True) -> None:
    """Route structlog, stdlib and uvicorn logging through one structlog formatter.

    Output goes to stdout, one JSON object per line (or a colored console format when
    `json_logs` is False, for local development). Safe to call repeatedly: it replaces only
    the handler it installed earlier and leaves other handlers (such as pytest's) alone.

    Args:
        level: Root log level name, for example ``"INFO"``.
        json_logs: Render JSON when True, human-readable console output otherwise.
    """
    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_request_id,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *([structlog.processors.dict_tracebacks] if json_logs else []),
            renderer,
        ],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    setattr(handler, _HANDLER_MARKER, True)

    root = logging.getLogger()
    for existing in [h for h in root.handlers if getattr(h, _HANDLER_MARKER, False)]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Uvicorn installs its own handlers; hand its records to the root handler instead.
    for name in _UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
