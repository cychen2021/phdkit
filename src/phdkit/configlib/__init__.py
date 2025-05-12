"""Utilities for loading configuration files to a Python object.

This module provides a declarative way to load configuration files to a Python object.
Via the decorator design pattern, you can define a class with designated config loader
and setting items. The class will be automatically populated with the values from the
configuration file.

Example usage:
```python
... # TODO: Add example usage
```

Attributes:
    Config: The singleton that manages configurations.
    setting: A decorator to mark a method as a setting.
"""


from .configurable import setting, configurable, Config
from .tomlreader import TomlReader
from .configreader import ConfigLoader

__all__ = [
    "setting",
    "TomlReader",
    "ConfigLoader",
    "configurable",
    "Config",
    "setting"
]
