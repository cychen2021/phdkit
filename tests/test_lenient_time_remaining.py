from datetime import timedelta

from rich.text import Text
from rich.progress import Task
from typing import cast

from phdkit.rich import LenientTimeRemainingColumn


class DummyTask:
    """Minimal stand-in for rich.progress.Task with needed attributes."""

    def __init__(
        self,
        *,
        started=False,
        total=None,
        finished=False,
        completed=0,
        elapsed=0,
        finished_time=None,
    ):
        self.started = started
        self.total = total
        self.finished = finished
        self.completed = completed
        self.elapsed = elapsed
        self.finished_time = finished_time


def test_passthrough_when_parent_provides_estimate(monkeypatch):
    col = LenientTimeRemainingColumn()

    # Create a dummy Text object representing a stable estimate
    stable_text = Text("0:00:05", style="progress.remaining")

    # Patch the parent TimeRemainingColumn.render to return our stable Text
    monkeypatch.setattr(
        "phdkit.rich.lenient_time_remaining.TimeRemainingColumn.render",
        lambda self, task: stable_text,
    )

    task = DummyTask(started=True, total=10, completed=5, elapsed=5)
    out = col.render(cast(Task, task))

    assert isinstance(out, Text)
    assert out.plain == "0:00:05"


def test_lenient_fallback_computes_estimate(monkeypatch):
    col = LenientTimeRemainingColumn()

    # Simulate parent returning the placeholder that indicates unreliable estimate
    monkeypatch.setattr(
        "phdkit.rich.lenient_time_remaining.TimeRemainingColumn.render",
        lambda self, task: Text("-:--:--"),
    )

    # Task with 4 completed out of 10, elapsed 8 seconds -> avg 2s/step -> remaining (6 steps) = 12s
    task = DummyTask(started=True, total=10, completed=4, elapsed=8)
    out = col.render(cast(Task, task))

    assert isinstance(out, Text)
    # timedelta string for 12 seconds is '0:00:12'
    assert out.plain == str(timedelta(seconds=12))


def test_no_fallback_when_not_started_or_missing_data(monkeypatch):
    col = LenientTimeRemainingColumn()

    # Parent returns placeholder
    monkeypatch.setattr(
        "phdkit.rich.lenient_time_remaining.TimeRemainingColumn.render",
        lambda self, task: Text("-:--:-"),
    )

    # Case 1: task not started
    task1 = DummyTask(started=False, total=10, completed=0, elapsed=0)
    out1 = col.render(cast(Task, task1))
    assert isinstance(out1, Text)
    assert out1.plain == "-:--:-"

    # Case 2: no total
    task2 = DummyTask(started=True, total=None, completed=0, elapsed=0)
    out2 = col.render(cast(Task, task2))
    assert out2.plain == "-:--:-"

    # Case 3: completed == 0 (can't compute avg)
    task3 = DummyTask(started=True, total=10, completed=0, elapsed=5)
    out3 = col.render(cast(Task, task3))
    assert out3.plain == "-:--:-"
