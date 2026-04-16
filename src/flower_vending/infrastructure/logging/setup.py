"""Structured logging configuration for the vending machine runtime."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, MutableMapping
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from flower_vending.infrastructure.config.models import LoggingConfig


_STANDARD_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}


class JsonLogFormatter(logging.Formatter):
    """Render log records as JSON lines with correlation-friendly extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in _STANDARD_FIELDS:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


class StructuredLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Keep correlation and transaction identifiers attached to log records."""

    def bind(self, **extra: Any) -> "StructuredLoggerAdapter":
        merged = dict(self._base_extra())
        merged.update(extra)
        return StructuredLoggerAdapter(self.logger, merged)

    def process(self, msg: object, kwargs: MutableMapping[str, Any]) -> tuple[object, MutableMapping[str, Any]]:
        extra = dict(self._base_extra())
        supplied_extra = kwargs.pop("extra", {})
        if isinstance(supplied_extra, Mapping):
            extra.update(supplied_extra)
        kwargs["extra"] = extra
        return msg, kwargs

    def _base_extra(self) -> Mapping[str, object]:
        return {} if self.extra is None else self.extra


def close_logging(logger: StructuredLoggerAdapter | logging.Logger) -> None:
    target = logger.logger if isinstance(logger, StructuredLoggerAdapter) else logger
    for handler in list(target.handlers):
        handler.flush()
        handler.close()
        target.removeHandler(handler)


def configure_logging(config: LoggingConfig, *, logger_name: str = "flower_vending") -> StructuredLoggerAdapter:
    log_directory = Path(config.directory)
    log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    close_logging(logger)
    logger.propagate = False

    formatter: logging.Formatter
    formatter = JsonLogFormatter() if config.json_logs else logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_directory / config.filename,
        maxBytes=config.rotation.max_bytes,
        backupCount=config.rotation.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if config.stderr:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return StructuredLoggerAdapter(logger, {})
