from datetime import timedelta

from rich.progress import (
    TimeRemainingColumn,
    Task,
)
from rich.text import Text


class LenientTimeRemainingColumn(TimeRemainingColumn):
    """
    A "lenient" time-remaining column.
    When the default speed estimate is unreliable, it falls back to using the
    global average speed to compute the remaining time instead of hiding it.
    """

    def render(self, task: "Task") -> Text:
        # Try calling the parent (original) render method.
        # If rich considers the estimate stable, it will return a Text object.
        remaining_time = super().render(task)

        # Check whether the original method returned the placeholder "?:??:??"
        # which indicates rich considers the estimate unreliable.
        if remaining_time.plain == "-:--:-":
            # If the task has started, has a total and is not finished
            if task.started and task.total is not None and not task.finished:
                # Use our own "lenient" algorithm
                elapsed = task.finished_time if task.finished else task.elapsed
                if elapsed is not None and task.completed > 0:
                    # Compute global average time per step
                    avg_time_per_step = elapsed / task.completed
                    # Compute remaining time
                    time_remaining = avg_time_per_step * (task.total - task.completed)

                    # Format and return our own estimate
                    return Text(
                        str(timedelta(seconds=int(time_remaining))),
                        style="progress.remaining",
                    )

        # If the original estimate is available, return it directly
        return remaining_time
