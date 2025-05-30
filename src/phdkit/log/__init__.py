"""Improved logging.

This module provides a flexible logging system that supports multiple output formats
and destinations, including console, file, and email. It allows for different logging levels,
formats (plain text or JSONL), and optional timestamps. The `Logger` class can be used to log messages
with various severity levels, and the `LogOutput` class defines the configuration for each logging output.
The `LogOutput` class can be used to create console outputs (to stdout or stderr), file outputs, or email outputs.
It is designed to be extensible, allowing users to add or remove logging outputs dynamically.
The `Logger` class manages multiple `LogOutput` instances and provides methods to log messages at different levels.

Usage:
    log_output = LogOutput.stdout(
        id="my_stdout",
        level=LogLevel.INFO,
        format="plain",
        auto_timestamp=True
    )
    logger = Logger("my_logger", outputs=[log_output])
    logger.info("Header", "This is a log message.")
"""

from .logger import Logger, LogOutput, LogOutputKind, EmailNotifier, LogLevel

__all__ = ["Logger", "LogOutput", "LogOutputKind", "EmailNotifier", "LogLevel"]
