import logging
from typing import Literal, TextIO, override
import json
from enum import Enum
import sys
from datetime import datetime
import io
from threading import Lock

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
    
class EmailConfig:
    ...

class LogOutput:
    def __init__(self, kind: LogOutputKind, file: str | None = None, 
                       stream: TextIO | None = None, email_config: EmailConfig | None = None):
        self.__kind = kind
        assert file is None or stream is None, "Cannot specify both file and stream"
        assert (kind == LogOutputKind.FILE and file is not None) or \
               (kind == LogOutputKind.CONSOLE and stream is not None) or \
               (kind == LogOutputKind.EMAIL and email_config is not None), \
                "File, stream, or email config must be specified"
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
            ...
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
        def createLock(self) -> Lock:
            return Lock()
    
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
    def __init__(self, name: str, *, format: Literal["plain", "jsonl"] = "plain", auto_timestamp: bool = True, outputs: list[LogOutput] = []):
        self.__underlying_logger: logging.Logger = logging.getLogger(name)
        self.__format: Literal["plain", "jsonl"] = format
        self.__auto_timestamp = auto_timestamp
        match format, auto_timestamp:
            case "plain", True:
                formatter = logging.Formatter("[%(name)s:%(levelname)s] %(asciitime)s: %(message)s")
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

    def log(self, level: Literal["debug", "info", "warning", "error", "critical"] | LogLevel, header: str, message: object):
        if isinstance(level, LogLevel):
            level_number = level.value
        else:
            level_number = getattr(logging, level.upper())

        if self.__format == "plain":
            self.__underlying_logger.log(level_number, f"{header}: {message}")
        elif self.__format == "jsonl":
            timestamp = datetime.now().isoformat()
            self.__underlying_logger.log(level_number, json.dumps({"timestamp": timestamp, "header": header, "message": message}))
    
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