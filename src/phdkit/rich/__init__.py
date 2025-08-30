"""Small, reusable helpers built on top of the `rich` library.

This package collects tiny utilities used by phdkit for simple terminal UIs.

Utilities included:

- `subshell`: run a subprocess and stream its stdout/stderr into a scrolling
	panel using `rich.live`.
- `LenientTimeRemainingColumn`: a progress-column that falls back to a
	global-average estimate when the default rich estimator hides the remaining
	time.

These helpers are intentionally lightweight and have minimal external
dependencies beyond `rich` itself.
"""

from .subshell_mod import subshell
from .lenient_time_remaining import LenientTimeRemainingColumn

__all__ = ["subshell", "LenientTimeRemainingColumn"]
