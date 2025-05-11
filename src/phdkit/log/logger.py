import logging
from typing import Literal, TextIO, override
import json
from enum import Enum
import sys
from datetime import datetime
import io
import os
import tomllib
from .notifier import EmailNotifier
from ..configlib import configurable, setting, ConfigReader


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogOutputKind(Enum):
    CONSOLE = "stream"
    FILE = "file"
    EMAIL = "email"


class LogOutput:
    def __init__(
        self,
        id: str | None = None,
        *,
        kind: LogOutputKind,
        file: str | None = None,
        stream: TextIO | None = None,
        level: LogLevel = LogLevel.INFO,
        email_notifier: EmailNotifier | None = None,  # type: ignore[arg-type]
        format: Literal["plain", "jsonl"] = "plain",
        auto_timestamp: bool = True,
    ):
        self.__id = id
        self.__kind = kind
        self.__format: Literal["plain", "jsonl"] = format
        self.__auto_timestamp: bool = auto_timestamp
        assert file is None or stream is None, "Cannot specify both file and stream"
        assert (
            (kind == LogOutputKind.FILE and file is not None)
            or (kind == LogOutputKind.CONSOLE and stream is not None)
            or (kind == LogOutputKind.EMAIL and email_notifier is not None)
        ), "File, stream, or email config must be specified"
        self.__level = level
        match kind:
            case LogOutputKind.FILE:
                assert file is not None
                self.__handler = logging.FileHandler(file)
            case LogOutputKind.CONSOLE:
                self.__handler = logging.StreamHandler(stream)
            case LogOutputKind.EMAIL:
                assert email_notifier is not None
                self.__handler = self.__EmailHandler(email_notifier)
        self.__handler.setLevel(level.value)

        match format:
            case "plain":
                formatter = logging.Formatter("[%(name)s:%(levelname)s] %(message)s")
            case "jsonl":
                formatter = logging.Formatter("%(message)s")

            case _:
                raise ValueError(f"Invalid format: {format}")
        self.__handler.setFormatter(formatter)

    @property
    def level(self) -> LogLevel:
        return self.__level

    @property
    def id(self) -> str | None:
        return self.__id

    @property
    def kind(self) -> LogOutputKind:
        return self.__kind

    @property
    def format(self) -> Literal["plain", "jsonl"]:
        return self.__format

    @property
    def auto_timestamp(self) -> bool:
        return self.__auto_timestamp

    class __EmailHandler(logging.NullHandler):
        def __init__(self, email_notifier: EmailNotifier):
            super().__init__()
            self.__email_notifier = email_notifier
            self.__stream = io.StringIO()
            self.__handler = logging.StreamHandler(self.__stream)

        @override
        def emit(self, record: logging.LogRecord):
            self.__handler.emit(record)
            content = self.__stream.getvalue()
            self.__email_notifier.send(
                subject=f"{record.levelname}: {record.name}",
                body=content,
            )
            self.__stream.truncate(0)
            self.__stream.seek(0)

        @override
        def flush(self):
            self.acquire()
            try:
                self.__handler.flush()
            finally:
                self.release()

        @override
        def handle(self, record: logging.LogRecord):
            if record.levelno < self.level:
                return
            self.__handler.handle(record)

        @override
        def createLock(self):
            super(logging.NullHandler, self).createLock()

        @override
        def setLevel(self, level: int | str) -> None:
            return super().setLevel(level)

    @property
    def handler(self) -> logging.Handler:
        return self.__handler

    def flush(self):
        self.__handler.flush()

    @staticmethod
    def stdout(id: str | None = None) -> "LogOutput":
        return LogOutput(id, kind=LogOutputKind.CONSOLE, stream=sys.stdout)

    @staticmethod
    def stderr(id: str | None = None) -> "LogOutput":
        return LogOutput(id, kind=LogOutputKind.CONSOLE, stream=sys.stderr)

    @staticmethod
    def file(file: str, *, id: str | None = None) -> "LogOutput":
        return LogOutput(id, kind=LogOutputKind.FILE, file=file)

    def set_formatter(self, formatter: logging.Formatter):
        self.__handler.setFormatter(formatter)


class Logger:
    def __init__(
        self,
        name: str,
        *,
        outputs: list[LogOutput] = [],
    ):
        self.__underlying_logger: logging.Logger = logging.getLogger(name)
        self.__underlying_logger_with_timestamp: logging.Logger = logging.getLogger(
            name
        )
        self.__underlying_jsonl_logger: logging.Logger = logging.getLogger(name)
        self.__underlying_jsonl_logger_with_timestamp: logging.Logger = (
            logging.getLogger(name)
        )

        self.__outputs = {}
        for output in outputs:
            match output.format, output.auto_timestamp:
                case "plain", False:
                    self.__underlying_logger.addHandler(output.handler)
                case "plain", True:
                    self.__underlying_logger_with_timestamp.addHandler(output.handler)
                case "jsonl", True:
                    self.__underlying_jsonl_logger_with_timestamp.addHandler(
                        output.handler
                    )
                case "jsonl", False:
                    self.__underlying_jsonl_logger.addHandler(output.handler)
            if output.id is not None:
                self.__outputs[output.id] = output

    def add_output(self, output: LogOutput):
        match output.format, output.auto_timestamp:
            case "plain", False:
                self.__underlying_logger.addHandler(output.handler)
            case "plain", True:
                self.__underlying_logger_with_timestamp.addHandler(output.handler)
            case "jsonl", True:
                self.__underlying_jsonl_logger_with_timestamp.addHandler(output.handler)
            case "jsonl", False:
                self.__underlying_jsonl_logger.addHandler(output.handler)
        if output.id is not None:
            self.__outputs[output.id] = output

    def remove_output(self, output: str | LogOutput):
        if isinstance(output, str):
            output = self.__outputs[output]
        assert isinstance(output, LogOutput)
        match output.format, output.auto_timestamp:
            case "plain", False:
                self.__underlying_logger.removeHandler(output.handler)
            case "plain", True:
                self.__underlying_logger_with_timestamp.removeHandler(output.handler)
            case "jsonl", True:
                self.__underlying_jsonl_logger_with_timestamp.removeHandler(output.handler)
            case "jsonl", False:
                self.__underlying_jsonl_logger.removeHandler(output.handler)
        if output.id is not None:
            del self.__outputs[output.id]

    def log(
        self,
        level: Literal["debug", "info", "warning", "error", "critical"] | LogLevel,
        header: str,
        message: object,
    ):
        if isinstance(level, LogLevel):
            level_number = level.value
        else:
            level_number = getattr(logging, level.upper())

        self.__underlying_logger.log(level_number, f"{header}: {message}")
        self.__underlying_jsonl_logger.log(
            level_number,
            json.dumps({"header": header, "message": message}),
        )
        timestamp = datetime.now().isoformat()
        self.__underlying_logger_with_timestamp.log(
            level_number, f"{header}@{timestamp}: {message}"
        )
        self.__underlying_jsonl_logger_with_timestamp.log(
            level_number,
            json.dumps(
                {
                    "timestamp": timestamp,
                    "header": header,
                    "message": message,
                }
            ),
        )

    def debug(self, header: str, message: object):
        self.log("debug", header, message)

    def info(self, header: str, message: object):
        self.log("info", header, message)

    def warning(self, header: str, message: object):
        self.log("warning", header, message)

    def error(self, header: str, message: object):
        self.log("error", header, message)

    def critical(self, header: str, message: object):
        self.log("critical", header, message)
