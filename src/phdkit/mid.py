"""Defining infix functions.

Example usage:

```python
from phdkit.mid import infix

@infix
def add(x, y):
    return x + y

result = 1 |add| 2  # Equivalent to add(1, 2)
print(result)  # Output: 3
```
"""

from functools import update_wrapper

__all__ = ["infix"]


class base_infix(object):
    def __init__(self, function):
        self._function = function
        update_wrapper(self, self._function)
        self.lbind = type(f"_or_lbind", (lbind,), {"__or__": lbind.__call__})
        self.rbind = type(f"_or_rbind", (rbind,), {"__ror__": rbind.__call__})

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)

    def left(self, other):
        """Returns a partially applied infix operator"""
        return self.rbind(self._function, other)

    def right(self, other):
        return self.lbind(self._function, other)


class rbind(object):
    def __init__(self, function, binded):
        self._function = function
        update_wrapper(self, self._function)
        self.binded = binded

    def __call__(self, other):
        return self._function(other, self.binded)

    def reverse(self, other):
        return self._function(self.binded, other)

    def __repr__(self):
        return f"<{self.__class__.__name__}: Waiting for left side>"


class lbind(object):
    def __init__(self, function, binded):
        self._function = function
        update_wrapper(self, self._function)
        self.binded = binded

    def __call__(self, other):
        return self._function(self.binded, other)

    def reverse(self, other):
        return self._function(other, self.binded)

    def __repr__(self):
        return f"<{self.__class__.__name__}: Waiting for right side>"


def make_infix():
    return type(
        f"_or_infix",
        (base_infix,),
        {"__or__": base_infix.left, "__ror__": base_infix.right},
    )


infix = make_infix()
