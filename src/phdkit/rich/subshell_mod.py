"""Small utility to run subprocesses with a live, scrolling Rich Panel.

This module exposes a factory function `subshell` which returns a callable
that runs a subprocess and streams its stdout/stderr lines into a
Rich Panel that scrolls. It's useful for showing command output in a
terminal UI while keeping only the last N lines visible.

Example:
    run = subshell("Build", 10)
    rc = run(["/usr/bin/make"], check=True)
"""

from __future__ import annotations

from typing import List, Protocol

from rich.text import Text
from rich.panel import Panel
from rich.live import Live
import subprocess
import time


class SubshellRunner(Protocol):
    def __call__(self, cmd: list[str], *, check: bool = False, **kwargs) -> int: ...


class ScrollPanel:
    """A small helper that maintains a fixed-size list of lines and
    renders them as a Rich Panel.

    Args:
        title: Panel title to display.
        line_num: Number of content lines to keep visible in the panel.

    Behavior:
        - Lines are stored in insertion order.
        - When more than `line_num` lines are pushed, the oldest lines are
          dropped so that the panel always shows at most `line_num` lines.
    """

    def __init__(self, title: str, line_num: int) -> None:
        self.title = title
        self.line_num = int(line_num)
        # Use a mutable list as a ring buffer (simple implementation).
        self.__lines: List[str] = [""] * self.line_num

    def __call__(self) -> Panel:
        """Return a Rich Panel renderable representing the current buffer."""
        return Panel(
            Text("\n".join(self.__lines)),
            height=self.line_num + 2,  # add space for borders/title
            title=f"[bold]{self.title}[/bold]",
            border_style="dim",
        )

    def push(self, line: str) -> None:
        """Append a new line to the buffer and discard the oldest if needed.

        The line is stored as-is; callers may wish to call .strip() before
        pushing if they don't want trailing newlines preserved.
        """
        self.__lines.append(line)
        if len(self.__lines) > self.line_num:
            # drop the oldest line
            self.__lines.pop(0)


def subshell(title: str, line_num: int) -> SubshellRunner:
    """Factory that returns a function to run a subprocess and stream its
    output into a scrolling panel.

    Args:
        title: Title for the Rich Panel shown while the command runs.
        line_num: Number of lines to keep visible in the panel.

    Returns:
        A callable that accepts the command (as an iterable/sequence of
        program + args or a string, compatible with subprocess.Popen) and
        optional keyword arguments forwarded to subprocess.Popen. The
        returned callable runs the process, streams stdout/stderr into the
        panel, and returns the process exit code. If `check=True` is passed
        and the process exits non-zero, a CalledProcessError is raised.
    """

    panel = ScrollPanel(title, line_num)

    def __run(cmd: list[str], *, check: bool = False, **kwargs) -> int:
        """Run the given command and stream its stdout/stderr into a Live
        Rich Panel.

        Args:
            cmd: The command to execute (list/tuple or string) that is
                accepted by subprocess.Popen.
            check: If True, raise subprocess.CalledProcessError on non-zero
                exit codes.
            **kwargs: Additional kwargs forwarded to subprocess.Popen.

        Returns:
            The process return code.
        """

        with (
            Live(
                vertical_overflow="visible", get_renderable=panel, auto_refresh=False
            ) as live,
            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                **kwargs,
            ) as p,
        ):
            # small pause to allow the live panel to initialize visually
            live.refresh()
            time.sleep(0.5)
            assert p.stdout is not None
            # stream each line as it becomes available
            for line in p.stdout:
                panel.push(line.strip())
                live.refresh()
            return_code = p.wait()
            if return_code != 0 and check:
                # read() after iteration will be empty, but include for API
                raise subprocess.CalledProcessError(
                    return_code,
                    cmd,
                    output=p.stdout.read(),
                )
            return return_code

    return __run
