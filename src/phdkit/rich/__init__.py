"""A wrapper over `rich` to implement simple TUIs.

TODO
"""

from .subshell_mod import subshell
from .lenient_time_remaining import LenientTimeRemainingColumn

__all__ = ["subshell", "LenientTimeRemainingColumn"]
