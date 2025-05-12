"""Utilities for loading configuration files to a Python object. *Don't use this module until we find the best design.*

This module provides a declarative way to load configuration files to a Python object.
Via the decorator design pattern, you can define a class with designated config loader
and setting items. The class will be automatically populated with the values from the
configuration file.

Example usage:
```python
... # TODO: Add example usage
```
"""


from .configurable import setting, Configurable, Setting
from .tomlreader import TomlReader
from .configreader import ConfigReader

__all__ = [
    "setting",
    "TomlReader",
    "ConfigReader",
    "Configurable",
    "Setting",
]
