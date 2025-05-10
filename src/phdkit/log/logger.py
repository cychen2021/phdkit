import logging
from typing import Literal, TextIO, override
import json
from enum import Enum
import sys
from datetime import datetime
import io
import os
import tomllib
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


def __read_email_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {}
        if "MAILOG_RECEIVER" in os.environ:
            config["mailog_receiver"] = os.environ["MAILOG_RECEIVER"]
        else:
            config["mailog_receiver"] = None

        if "MAILOG_SMTP" in os.environ:
            config["mailog_smtp"] = os.environ["MAILOG_SMTP"]
        else:
            config["mailog_smtp"] = None

        if "MAILOG_SENDER" in os.environ:
            config["mailog_sender"] = os.environ["MAILOG_SENDER"]
        else:
            config["mailog_sender"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        assert set(config.keys()).issubset(
            {"mailog_receiver", "mailog_smtp", "mailog_sender"}
        )
        if "mailog_receiver" not in config:
            config["mailog_receiver"] = None
        if "mailog_smtp" not in config:
            config["mailog_smtp"] = None
        if "mailog_sender" not in config:
            config["mailog_sender"] = None
    return config


def __read_email_env_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {}
        if "MAILOG_PASSWORD" in os.environ:
            config["mailog_password"] = os.environ["MAILOG_PASSWORD"]
        else:
            config["mailog_password"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        assert set(config.keys()).issubset({"mailog_password"})
        if "mailog_password" not in config:
            config["mailog_password"] = None
    return config

# TODO: The design pattern can be improved
@configurable(__read_email_config, __read_email_env_config)
class EmailConfig:
    def __init__(self):
        self.__receiver = None
        self.__smtp = None
        self.__sender = None
        self.__password = None

    @property
    def receiver(self) -> str | None:
        if self.__receiver is None:
            raise ValueError("Receiver email address is not set")
        return self.__receiver

    @receiver.setter
    @setting("mailog_receiver")
    def receiver(self, value: str):
        self.__receiver = value

    @property
    def smtp(self) -> str | None:
        if self.__smtp is None:
            raise ValueError("SMTP server is not set")
        return self.__smtp

    @smtp.setter
    @setting("mailog_smtp")
    def smtp(self, value: str):
        self.__smtp = value

    @property
    def sender(self) -> str | None:
        if self.__sender is None:
            raise ValueError("Sender email address is not set")
        return self.__sender

    @sender.setter
    @setting("mailog_sender")
    def sender(self, value: str):
        self.__sender = value

    @property
    def password(self) -> str | None:
        if self.__password is None:
            raise ValueError("Email password is not set")
        return self.__password

    @password.setter
    @setting("mailog_password")
    def password(self, value: str):
        self.__password = value


class LogOutput:
    def __init__(
        self,
        kind: LogOutputKind,
        file: str | None = None,
        stream: TextIO | None = None,
        email_config: EmailConfig | None = None, # type: ignore[assignment]
    ):
        self.__kind = kind
        assert file is None or stream is None, "Cannot specify both file and stream"
        assert (
            (kind == LogOutputKind.FILE and file is not None)
            or (kind == LogOutputKind.CONSOLE and stream is not None)
            or (kind == LogOutputKind.EMAIL and email_config is not None)
        ), "File, stream, or email config must be specified"
        self.__file_name = file
        self.__stream = stream
        self.__email_config = email_config
        match kind:
            case LogOutputKind.FILE:
                assert file is not None
                self.__handler = logging.FileHandler(file)
            case LogOutputKind.CONSOLE:
                self.__handler = logging.StreamHandler(stream)
            case LogOutputKind.EMAIL:
                assert email_config is not None
                self.__handler = self.__EmailHandler(email_config)

    class __EmailHandler(logging.NullHandler):
        def __init__(self, email_config: EmailConfig):
            self.__email_config = email_config
            self.__stream = io.StringIO()
            self.__handler = logging.StreamHandler(self.__stream)

        @override
        def emit(self, record: logging.LogRecord):
            self.__handler.emit(record)
            content = self.__stream.getvalue()
            ...  # TODO: Implement email sending
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
            self.__handler.handle(record)

        @override
        def createLock(self):
            super(logging.NullHandler, self).createLock()

    @property
    def handler(self) -> logging.Handler:
        return self.__handler

    def flush(self):
        self.__handler.flush()

    @staticmethod
    def stdout() -> "LogOutput":
        return LogOutput(LogOutputKind.CONSOLE, stream=sys.stdout)

    @staticmethod
    def stderr() -> "LogOutput":
        return LogOutput(LogOutputKind.CONSOLE, stream=sys.stderr)

    @staticmethod
    def file(file: str) -> "LogOutput":
        return LogOutput(LogOutputKind.FILE, file=file)

    def set_formatter(self, formatter: logging.Formatter):
        self.__handler.setFormatter(formatter)


class Logger:
    def __init__(
        self,
        name: str,
        *,
        format: Literal["plain", "jsonl"] = "plain",
        auto_timestamp: bool = True,
        outputs: list[LogOutput] = [],
    ):
        self.__underlying_logger: logging.Logger = logging.getLogger(name)
        self.__format: Literal["plain", "jsonl"] = format
        self.__auto_timestamp = auto_timestamp
        match format, auto_timestamp:
            case "plain", True:
                formatter = logging.Formatter(
                    "[%(name)s:%(levelname)s] %(asciitime)s: %(message)s"
                )
            case "plain", False:
                formatter = logging.Formatter("[%(name)s:%(levelname)s] %(message)s")
            case "jsonl", True:
                formatter = logging.Formatter("%(message)s")
            case "jsonl", False:
                formatter = logging.Formatter("%(message)s")

            case _:
                raise ValueError(f"Invalid format: {format}")

        for output in outputs:
            output.set_formatter(formatter)
            self.__underlying_logger.addHandler(output.handler)

    @property
    def auto_timestamp(self) -> bool:
        return self.__auto_timestamp

    @property
    def format(self) -> Literal["plain", "jsonl"]:
        return self.__format

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

        if self.__format == "plain":
            self.__underlying_logger.log(level_number, f"{header}: {message}")
        elif self.__format == "jsonl":
            timestamp = datetime.now().isoformat()
            self.__underlying_logger.log(
                level_number,
                json.dumps(
                    {"timestamp": timestamp, "header": header, "message": message}
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
