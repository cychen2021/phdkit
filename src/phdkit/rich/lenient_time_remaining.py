"""A small `rich` progress column with a lenient time-remaining estimate.

The standard `rich` TimeRemainingColumn sometimes hides the remaining time
when the speed estimate is considered unreliable. This column attempts to be
more helpful by falling back to a simple global-average estimate when the
default estimator returns the placeholder string.

This is suitable for progress bars where showing a rough remaining time is
preferable to showing nothing.
"""

from __future__ import annotations

from datetime import timedelta

from rich.progress import (
    TimeRemainingColumn,
    Task,
)
from rich.text import Text


class LenientTimeRemainingColumn(TimeRemainingColumn):
    """Render a human-friendly remaining time.

    If the parent column returns the placeholder (meaning the estimator is
    unreliable), the class computes a fallback estimate using elapsed time and
    completed steps to form a global-average per-step time.
    """

    def render(self, task: Task) -> Text:
        # Try calling the parent (original) render method. If rich considers
        # the estimate stable, it will return a Text object with the time.
        remaining_time = super().render(task)

        # Check whether the original method returned the placeholder used by
        # rich ("-:--:--"). If so, try a lenient fallback.
        if remaining_time.plain == "-:--:--":
            # If the task has started, has a total and is not finished
            if task.started and task.total is not None and not task.finished:
                # Use our own "lenient" algorithm
                elapsed = task.finished_time if task.finished else task.elapsed
                if elapsed is not None and task.completed > 0:
                    # Compute global average time per step and remaining time
                    avg_time_per_step = elapsed / task.completed
                    time_remaining = avg_time_per_step * (task.total - task.completed)

                    # Format and return our own estimate
                    return Text(
                        str(timedelta(seconds=int(time_remaining))),
                        style="progress.remaining",
                    )

        # If the original estimate is available or we couldn't compute a
        # fallback, return the parent's output directly.
        return remaining_time
