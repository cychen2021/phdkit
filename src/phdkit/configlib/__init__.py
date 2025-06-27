"""Utilities for loading configuration files to a Python object.

This module provides a declarative way to load configuration files to a Python object.
Via the decorator design pattern, you can define a class with designated config loader
and setting items. The class will be automatically populated with the values from the
configuration file.

Example usage:

```python
@configurable(load_config=TomlReader(), load_env=TomlReader())
class SomeApp:
    @setting("auto_gen")
    def auto_generated_getter_and_setter(self) -> bool: ...

    @setting.getter("manuall")
    def manual_setter_and_getter(self) -> bool:
        return self._manual

    @manual_setter_and_getter.setter
    def set_manual_setter_and_getter(self, value: bool) -> None:
        self._manual = value
if __name__ == "__main__":
    app = SomeApp()
    config[app].load("config.toml", "env.toml")
```

Attributes:
    Config: The singleton that manages configurations.
    config: An alias for Config.
    setting: A decorator to mark a method as a setting.
"""

# TODO: Add docs for `configurable_fn` and `setting_fn`

from .configurable import setting, configurable, Config, config
from .configurable_fn import configurable_fn, setting_fn
from .tomlreader import TomlReader
from .configreader import ConfigLoader

__all__ = [
    "setting",
    "TomlReader",
    "ConfigLoader",
    "configurable",
    "Config",
    "setting",
    "config",
    "configurable_fn",
    "setting_fn",
]
