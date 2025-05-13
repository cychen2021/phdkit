"""Utilities for loading configuration files to a Python object.

This module provides a declarative way to load configuration files to a Python object.
Via the decorator design pattern, you can define a class with designated config loader
and setting items. The class will be automatically populated with the values from the
configuration file.

Note that type checkers (at least the one that VS Code uses) cannot infer the type of
the setting items correctly for current implementation. It seems that the type checkers
handle the built-in `property` decorator in an ad-hoc way. The current status is the
best we can do.

Example usage:

```python
@configurable(load_config=TomlReader(), load_env=TomlReader())
class SomeApp:
    @setting("auto_gen")
    def auto_generated_getter_and_setter(self) -> bool: ...

    @setting.getter("manuall")
    def manual_setter_and_getter(self) -> bool:
        return self._manual

    @manual_setter_and_getter.setter("manual")
    def manual_setter_and_getter(self, value: bool) -> None:
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

from .configurable import setting, configurable, Config
from .tomlreader import TomlReader
from .configreader import ConfigLoader

__all__ = ["setting", "TomlReader", "ConfigLoader", "configurable", "Config", "setting"]
