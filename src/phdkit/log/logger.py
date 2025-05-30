import logging
from typing import Literal, TextIO, override
import json
from enum import Enum
import sys
from datetime import datetime
import io
from .notifier import EmailNotifier


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
    """Represents a logging output configuration.
    This class allows you to configure different logging outputs such as console,
    file, or email. Each output can have its own logging level, format, and
    whether to include timestamps automatically.
    Attributes:
        id (str | None): An optional identifier for the log output.
        kind (LogOutputKind): The type of log output (console, file, or email).
        file (str | None): The file path for file logging, if applicable.
        stream (TextIO | None): The stream for console logging, if applicable.
        level (LogLevel): The logging level for this output.
        email_notifier (EmailNotifier | None): An email notifier for email logging.
        format (Literal["plain", "jsonl"]): The format of the log output.
        auto_timestamp (bool): Whether to automatically include timestamps in logs.
    Methods:
        __init__: Initializes a LogOutput instance with the specified parameters.
        stdout: Creates a console log output to standard output.
        stderr: Creates a console log output to standard error.
        file: Creates a file log output.
        email: Creates an email log output using an EmailNotifier.
        flush: Flushes the underlying handler.
        handler: Returns the underlying logging handler for this output.
    """

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
        """Initializes a LogOutput instance.
        Args:
            id (str | None): An optional identifier for the log output.
            kind (LogOutputKind): The type of log output (console, file, or email).
            file (str | None): The file path for file logging, if applicable.
            stream (TextIO | None): The stream for console logging, if applicable.
            level (LogLevel): The logging level for this output.
            email_notifier (EmailNotifier | None): An email notifier for email logging.
            format (Literal["plain", "jsonl"]): The format of the log output.
            auto_timestamp (bool): Whether to automatically include timestamps in logs.
        Raises:
            AssertionError: If both file and stream are specified, or if the kind does not match the provided file/stream/email_notifier.
        """

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

        formatter = logging.Formatter("%(message)s")
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

    def __repr__(self):
        return (
            f"LogOutput(id={self.__id}, kind={self.__kind}, "
            f"level={self.__level}, format={self.__format}, "
            f"auto_timestamp={self.__auto_timestamp})"
        )

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
                header=f"{record.levelname}: {record.name}",
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
    def stdout(
        id: str | None = None,
        level: LogLevel = LogLevel.INFO,
        format: Literal["plain", "jsonl"] = "plain",
        auto_timestamp: bool = True,
    ) -> "LogOutput":
        """Creates a console log output to standard output."""

        return LogOutput(
            id,
            kind=LogOutputKind.CONSOLE,
            stream=sys.stdout,
            level=level,
            format=format,
            auto_timestamp=auto_timestamp,
        )

    @staticmethod
    def stderr(
        id: str | None = None,
        level: LogLevel = LogLevel.INFO,
        format: Literal["plain", "jsonl"] = "plain",
        auto_timestamp: bool = True,
    ) -> "LogOutput":
        """Creates a console log output to standard error."""

        return LogOutput(
            id,
            kind=LogOutputKind.CONSOLE,
            stream=sys.stderr,
            level=level,
            format=format,
            auto_timestamp=auto_timestamp,
        )

    @staticmethod
    def file(
        file: str,
        *,
        id: str | None = None,
        level: LogLevel = LogLevel.INFO,
        format: Literal["plain", "jsonl"] = "plain",
        auto_timestamp: bool = True,
    ) -> "LogOutput":
        """Creates a file log output."""

        return LogOutput(
            id,
            kind=LogOutputKind.FILE,
            file=file,
            level=level,
            format=format,
            auto_timestamp=auto_timestamp,
        )

    @staticmethod
    def email(
        email_notifier: EmailNotifier,
        *,
        id: str | None = None,
        level: LogLevel = LogLevel.WARNING,
        format: Literal["plain", "jsonl"] = "plain",
        auto_timestamp: bool = True,
    ) -> "LogOutput":
        """Creates an email log output using an EmailNotifier."""

        return LogOutput(
            id,
            kind=LogOutputKind.EMAIL,
            email_notifier=email_notifier,
            level=level,
            format=format,
            auto_timestamp=auto_timestamp,
        )


class Logger:
    """A logger that supports multiple output formats and destinations.
    This logger can log messages to different outputs such as console, file, or email,
    with support for different formats (plain text or JSONL) and optional timestamps.
    Attributes:
        name (str): The name of the logger.
        outputs (list[LogOutput]): A list of LogOutput instances that define where to log messages.
    Methods:
        __init__: Initializes the Logger with a name and optional outputs.
        add_output: Adds a new LogOutput to the logger.
        remove_output: Removes a LogOutput from the logger.
        log: Logs a message with a specified level, header, and message content.
        debug: Logs a debug message.
        info: Logs an informational message.
        warning: Logs a warning message.
        error: Logs an error message.
        critical: Logs a critical message.
    """

    __default_output = LogOutput.stderr(
        id="stderr",
        level=LogLevel.INFO,
        format="plain",
        auto_timestamp=True,
    )

    def __init__(
        self,
        name: str,
        *,
        outputs: list[LogOutput] | None = [],
    ):
        """Initializes the Logger with a name and optional outputs.
        Args:
            name (str): The name of the logger.
            outputs (list[LogOutput] | None): A list of LogOutput instances that define where to log messages.
                The logger will output to stderr by default. Set `outputs` to `None` to disable it.
        """

        self.name = name
        if outputs is not None and not outputs:
            outputs = [Logger.__default_output]
        elif outputs is None:
            outputs = []
        self.__underlying_logger: logging.Logger = logging.getLogger(name + ".plain")
        self.__underlying_logger_with_timestamp: logging.Logger = logging.getLogger(
            name + ".plain_timestamp"
        )
        self.__underlying_jsonl_logger: logging.Logger = logging.getLogger(
            name + ".jsonl"
        )
        self.__underlying_jsonl_logger_with_timestamp: logging.Logger = (
            logging.getLogger(name + ".jsonl_timestamp")
        )
        self.__underlying_logger.handlers.clear()
        self.__underlying_logger_with_timestamp.handlers.clear()
        self.__underlying_jsonl_logger.handlers.clear()
        self.__underlying_jsonl_logger_with_timestamp.handlers.clear()

        # The filtration will be hijacked according to `LogOutput`
        self.__underlying_logger.setLevel(logging.DEBUG)
        self.__underlying_logger_with_timestamp.setLevel(logging.DEBUG)
        self.__underlying_jsonl_logger.setLevel(logging.DEBUG)
        self.__underlying_jsonl_logger_with_timestamp.setLevel(logging.DEBUG)
        self.__underlying_logger.propagate = False
        self.__underlying_logger_with_timestamp.propagate = False
        self.__underlying_jsonl_logger.propagate = False
        self.__underlying_jsonl_logger_with_timestamp.propagate = False

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
                self.__underlying_jsonl_logger_with_timestamp.removeHandler(
                    output.handler
                )
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
        """Logs a message with a specified level, header, and message content.
        Args:
            level (Literal["debug", "info", "warning", "error", "critical"] | LogLevel):
                The logging level to use. Can be a string or a LogLevel enum.
            header (str): A header for the log message.
            message (object): The message content to log. It will be converted to a string.
        """

        if isinstance(level, LogLevel):
            level_number = level.value
        else:
            level_number = getattr(logging, level.upper())

        message_lines = str(message).splitlines()
        idented = []
        for line in message_lines:
            if line.strip():
                idented.append("  " + line)
            else:
                idented.append(line)
        indented_message = "\n".join(idented)

        if self.__underlying_logger.handlers:
            self.__underlying_logger.log(
                level_number, f"[{self.name}:{level}] {header}:\n{indented_message}\n"
            )
        if self.__underlying_jsonl_logger.handlers:
            self.__underlying_jsonl_logger.log(
                level_number,
                json.dumps(
                    {
                        "name": self.name,
                        "level": level,
                        "header": header,
                        "message": message,
                    }
                ),
            )
        timestamp = datetime.now().isoformat()
        if self.__underlying_logger_with_timestamp.handlers:
            self.__underlying_logger_with_timestamp.log(
                level_number,
                f"[{self.name}:{level} @ {timestamp}] {header}:\n{indented_message}\n",
            )
        if self.__underlying_jsonl_logger_with_timestamp.handlers:
            self.__underlying_jsonl_logger_with_timestamp.log(
                level_number,
                json.dumps(
                    {
                        "name": self.name,
                        "level": level,
                        "timestamp": timestamp,
                        "header": header,
                        "message": message,
                    }
                ),
            )

    def debug(self, header: str, message: object):
        """Logs a debug message.

        See :func:`log` for more details.
        """

        self.log("debug", header, message)

    def info(self, header: str, message: object):
        """Logs an informational message.

        See :func:`log` for more details.
        """

        self.log("info", header, message)

    def warning(self, header: str, message: object):
        """Logs a warning message.
        See :func:`log` for more details.
        """

        self.log("warning", header, message)

    def error(self, header: str, message: object):
        """Logs an error message.

        See :func:`log` for more details.
        """

        self.log("error", header, message)

    def critical(self, header: str, message: object):
        """Logs a critical message.

        See :func:`log` for more details.
        """

        self.log("critical", header, message)
