from functools import update_wrapper
from types import UnionType
from typing import Callable, Any

__all__ = ["infix"]


class InfixOp[T1, T2, T]:
    def __init__(self, function: Callable[[T1, T2], T]):
        self._function = function
        update_wrapper(self, self._function)
        self.lbind = LBind
        self.rbind = RBind

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)

    def left(self, other: T2):
        """Returns a partially applied infix operator"""
        return self.rbind(self._function, other)

    def right(self, other: T1):
        return self.lbind(self._function, other)

    def __ror__(self, other: T1):
        return self.right(other)


class RBind[T1, T2, T]:
    def __init__(self, function: Callable[[T1, T2], T], binded: Any):
        self._function = function
        update_wrapper(self, self._function)
        self.binded = binded

    def __call__(self, other: T1):
        return self._function(other, self.binded)

    def reverse(self, other: T2):
        return self._function(self.binded, other)

    def __repr__(self):
        return f"<{self.__class__.__name__}: Waiting for left side>"

    def __ror__(self, other: T1):
        return self._function(other, self.binded)


class LBind[T1, T2, T]:
    def __init__(self, function: Callable[[T1, T2], T], binded: Any):
        self._function = function
        update_wrapper(self, self._function)
        self.binded = binded

    def __call__(self, other: T2):
        return self._function(self.binded, other)

    def reverse(self, other: T1):
        return self._function(other, self.binded)

    def __repr__(self):
        return f"<{self.__class__.__name__}: Waiting for right side>"

    def __or__(self, other: T2):
        return self._function(self.binded, other)


def make_infix[P1, P2, T]() -> Callable[[Callable[[P1, P2], T]], InfixOp[P1, P2, T]]:
    return type(
        "_or_infix",
        (InfixOp,),
        {"__or__": InfixOp.left, "__ror__": InfixOp.right},
    )


def infix[P1, P2, T](func: Callable[[P1, P2], T]) -> InfixOp[P1, P2, T]:
    """Defining infix functions.

    Example usage:

    ```python
    from phdkit import infix

    @infix
    def add(x, y):
        return x + y

    result = 1 |add| 2  # Equivalent to add(1, 2)
    print(result)  # Output: 3
    ```
    """

    return make_infix()(func)
