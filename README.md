# phdkit - Scripting Utilities for PhD Students

[![CI](https://github.com/cychen2021/phdkit/actions/workflows/ci.yml/badge.svg)](https://github.com/cychen2021/phdkit/actions/workflows/ci.yml)

## Overview

phdkit is a small utility library that bundles helpful tooling for research scripting and automation aimed at PhD students and researchers. It provides compact, well-tested primitives for common tasks encountered in data processing and workflow scripts: a high-performance IntervalTree for managing time or range-based data, a flexible logging system with optional email notifications, a declarative configuration loader that reads TOML/env sources, lightweight batching utilities, and small terminal UI helpers built on top of rich. The package emphasizes simplicity, clear APIs, and ease-of-use in scripts and notebooks so you can focus on research logic rather than tooling.

## Features

### Algorithms

#### Interval Tree

A high-performance Red-Black tree based interval tree implementation for efficiently managing and querying overlapping intervals.

**Key Features:**

- O(log n) insertion and deletion
- O(log n + k) overlap queries (where k is the number of results)
- Half-open interval semantics [start, end)
- Support for point queries and range queries
- Generic data payload support

**Example Usage:**

```python
from phdkit.alg import IntervalTree, Interval

# Create intervals
tree = IntervalTree()
tree.insert(Interval(1, 5, "Task A"))
tree.insert(Interval(3, 8, "Task B"))

# Find overlapping intervals
overlaps = tree.search(2, 6)  # Returns intervals overlapping [2, 6)

# Find intervals containing a point
containing = tree.query_point(4)  # Returns intervals containing point 4
```

### Logging and email notification

This package provides a small but flexible logging system with multiple output destinations (console, file, email) and formats (plain or JSONL). It includes an `EmailNotifier` helper for sending log messages by email.

Key types and behavior:

- `LogOutput` — configure an output destination. Supports console (stdout/stderr), file, and email outputs. Each output can be configured with a logging level, format (`plain` or `jsonl`), and whether timestamps are included.
- `Logger` — a logger that can attach multiple `LogOutput` instances. It exposes `debug`, `info`, `warning`, `error`, and `critical` convenience methods and a generic `log` method. JSONL outputs serialize log records as JSON objects.
- `EmailNotifier` — helper class (decorated with the `configurable` system) which reads SMTP configuration and can `send(header, body)` to deliver an email. It is used by `LogOutput.email(...)` to create an email-backed log output.

Example:

```python
from phdkit.log import Logger, LogOutput, LogLevel
from phdkit.log import EmailNotifier

# Console output
out = LogOutput.stdout(id="console", level=LogLevel.INFO, format="plain")
logger = Logger("myapp", outputs=[out])
logger.info("Startup", "Application started")

# File output
file_out = LogOutput.file("logs/myapp.log", level=LogLevel.DEBUG)
logger.add_output(file_out)

# Email notifier (requires configuration via configlib)
notifier = EmailNotifier()
# EmailNotifier is configurable via the configlib decorators and will pull settings from config/env
# If configured, create an email-backed LogOutput:
# email_out = LogOutput.email(notifier, level=LogLevel.WARNING)
# logger.add_output(email_out)
```

### Configuration management

The `configlib` package provides a declarative configuration loader and helpers to populate classes from TOML or environment sources.

Key concepts:

- `@configurable(load_config=..., load_env=...)` — class decorator that registers the class with the global configuration manager. The decorated class can then be loaded from files using `Config.load(instance, config_file, env_file)` or the shorthand `config[instance].load(config_file, env_file)`.
- `@setting("key.path")` / `setting.getter(...)` — used to declare configurable properties on a class. The decorator creates descriptors that store defaults and expose getters/setters which are set when configuration is loaded.
- `TomlReader` — a config reader for TOML files (used by the examples and `EmailNotifier`).

Example (simplified):

```python
from phdkit.configlib import configurable, setting, TomlReader, config

@configurable(load_config=TomlReader(), load_env=TomlReader())
class AppConfig:
    @setting("app.name", default="phdkit-sample")
    def name(self) -> str: ...

app = AppConfig()
config[app].load("config.toml", "env.toml")
print(app.name)
```

### Task batching

TODO

### Declaratively plotting

TODO

### Terminal UI helpers (rich)

This subpackage contains small utilities built on top of the `rich` library for
interactive terminal output:

- `LenientTimeRemainingColumn` — a progress-bar column that shows a lenient
    remaining-time estimate when the default rich estimator suppresses the value.
- `subshell` / `ScrollPanel` — a tiny helper to run subprocesses and stream
    their stdout/stderr into a scrollable panel rendered with `rich.live.Live`.

Example (lenient time column):

```python
from rich.progress import Progress
from phdkit.rich import LenientTimeRemainingColumn

with Progress(LenientTimeRemainingColumn()) as progress:
        task = progress.add_task("work", total=100)
        # update task.completed / task.advance in a loop
```

Example (subshell runner):

```python
from phdkit.rich import subshell

run = subshell("List dir", 20)
rc = run(["ls", "-la"])  # streams output into a live scrolling panel
```

### Other utilities

#### Infix functions

The `infix` decorator in `phdkit.infix_fn` allows you to define custom infix operators. Wrap a binary function with `@infix` and you can use the `|f|` syntax to call it. The implementation also provides helpers for left/right binding when partially applying one side of the operator.

Example:

```python
from phdkit.infix_fn import infix

@infix
def add(x, y):
    return x + y

result = 1 |add| 2  # equals add(1, 2)
```
