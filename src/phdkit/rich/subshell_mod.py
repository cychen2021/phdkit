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

import os
from typing import IO, List, Protocol, Optional

from rich.text import Text
from rich.panel import Panel
from rich.live import Live
import subprocess
import time
from queue import Queue, Empty
from threading import Thread
import sys

ON_POSIX = "posix" in sys.builtin_module_names


def enqueue_output(out: IO[str], queue) -> Optional[Exception]:
    try:
        while not out.closed:
            line = out.readline()
            if not line:
                break
            queue.put(line)
        if not out.closed:
            out.close()
    except Exception as e:
        return e
    return None


class SubshellRunner(Protocol):
    def __call__(
        self,
        cmd: list[str],
        *,
        check: bool = False,
        discard_stdout: bool,
        discard_stderr: bool,
        capture_output: bool,
        **kwargs,
    ) -> int | tuple[int, str, str]: ...


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


class DummyLive:
    """A dummy context manager that does nothing, for use when rich Live
    is not desired (e.g. in simple subshell mode).
    """

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def refresh(self) -> None:
        return None


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

    # XXX: Should we also add an argument and/or a function to set this explicitly?
    use_simple_subshell = os.environ.get("PHDKIT_SIMPLE_SUBSHELL", "false").lower() in [
        "1",
        "true",
        "yes",
        "on",
    ]
    if not use_simple_subshell:
        panel = ScrollPanel(title, line_num)
    else:
        panel = None

    def __run(
        cmd: list[str],
        *,
        capture_output: bool = False,
        timeout: float | None = None,
        check: bool = False,
        discard_stderr: bool = False,
        discard_stdout: bool = False,
        **kwargs,
    ) -> int | tuple[int, str, str]:
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
            (
                Live(
                    vertical_overflow="visible",
                    get_renderable=panel,
                    auto_refresh=False,
                )
                if not use_simple_subshell
                else DummyLive()
            ) as live,
            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE if not discard_stdout else subprocess.DEVNULL,
                stderr=subprocess.PIPE if not discard_stderr else subprocess.DEVNULL,
                text=True,
                **kwargs,
            ) as p,
        ):
            try:
                # small pause to allow the live panel to initialize visually
                if not use_simple_subshell:
                    assert isinstance(live, Live)
                    live.refresh()
                time.sleep(0.5)
                assert p.stdout is not None
                assert not (capture_output and discard_stdout and discard_stderr)
                stdout_captured = [] if capture_output else None
                stderr_captured = [] if capture_output else None
                if not discard_stdout:
                    q_stdout = Queue()
                    t_stdout = Thread(target=enqueue_output, args=(p.stdout, q_stdout))
                    t_stdout.daemon = True  # thread dies with the program
                    t_stdout.start()
                if not discard_stderr:
                    q_stderr = Queue()
                    t_stderr = Thread(target=enqueue_output, args=(p.stderr, q_stderr))
                    t_stderr.daemon = True  # thread dies with the program
                    t_stderr.start()
                start_time = time.time()
                while True:
                    try:
                        if not discard_stdout:
                            stdout_line = q_stdout.get_nowait()
                        else:
                            stdout_line = None
                    except Empty:
                        stdout_line = None
                    try:
                        if not discard_stderr:
                            stderr_line = q_stderr.get_nowait()
                        else:
                            stderr_line = None
                    except Empty:
                        stderr_line = None

                    if stdout_line:
                        if not use_simple_subshell:
                            assert isinstance(live, Live)
                            assert panel is not None
                            panel.push(stdout_line.rstrip("\n"))
                            live.refresh()
                        else:
                            print(stdout_line, end="")
                    if stderr_line:
                        if not use_simple_subshell:
                            assert isinstance(live, Live)
                            assert panel is not None
                            panel.push(stderr_line.rstrip("\n"))
                            live.refresh()
                        else:
                            print(stderr_line, end="", file=sys.stderr)
                    if capture_output:
                        if stdout_line:
                            stdout_captured.append(stdout_line)  # type: ignore
                        if stderr_line:
                            stderr_captured.append(stderr_line)  # type: ignore
                    if p.poll() is not None:
                        break
                    elapsed = time.time() - start_time
                    if timeout is not None and elapsed > timeout:
                        p.kill()
                        raise subprocess.TimeoutExpired(cmd, timeout)
                return_code = p.wait()
                if return_code != 0 and check:
                    # read() after iteration will be empty, but include for API
                    raise subprocess.CalledProcessError(
                        return_code,
                        cmd,
                        output=p.stdout.read(),
                    )
                return (
                    return_code
                    if not capture_output
                    else (
                        return_code,
                        "".join(stdout_captured),
                        "".join(stderr_captured),
                    )  # type: ignore
                )
            finally:
                if not discard_stdout:
                    except1 = t_stdout.join(timeout=0.1)
                    if except1 is not None:
                        raise except1
                if not discard_stderr:
                    except2 = t_stderr.join(timeout=0.1)
                    if except2 is not None:
                        raise except2

    return __run
