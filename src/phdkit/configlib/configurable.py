from typing import Type, Callable, Any
from .configreader import ConfigReader
from abc import ABC


def __split_key(key: str) -> list[str]:
    return key.split(".")


class Setting[T]:
    def __init__(self, config_key: str, setter: Callable[["Configurable", T], None] | None = None, getter: Callable[["Configurable"], T] | None = None):
        self.config_key = config_key
        self.setter = setter
        self.getter = getter

    def __set_name__(self, owner: "Configurable", name: str):
        owner.settings[self.config_key] = name

    def __set__(self, owner: "Configurable", value: T):
        if value is not None:
            assert isinstance(value, str)
        if self.setter is not None:
            self.setter(owner, value)
        else:
            setattr(owner, self.config_key, value)

    def __get__(self, owner: "Configurable", owner_type: Type["Configurable"]) -> T:
        if self.getter is not None:
            return self.getter(owner)
        return getattr(owner, self.config_key)


def setting(config_key: str, setter: Callable[["Configurable", Any], None] | None = None, getter: Callable[["Configurable"], Any] | None = None) -> Setting[Any]:
    return Setting(config_key, setter, getter)


class Configurable(ABC):
    """A configurable."""

    def __init__(
        self,
        read_config: ConfigReader,
        read_env: ConfigReader | None = None,
        *,
        config_key: str = "",
    ):
        """Configure a class with settings from a configuration file.

        This decorator allows you to define a class with settings that can be loaded from configuration
        files. The configuration can be separated into two parts: the main configuration file and
        one that contain secret values (can be loaded from a git-ignored file or environment variables).
        The decorated class should contain property setters that are decorated with the `@setting` decorator
        to store the configuration values.

        Note that this decorator will discard type information due to the limitations of the Python type hinting system.

        Args:
            read_config: A callable that reads the configuration file and returns a dictionary.
            read_env: A callable that reads the secret config values and returns a dictionary.
            config_key: A dot-separated key. If set, only parts corresponding to this key in the configuration file will be loaded.
        """
        self.read_config = read_config
        self.read_env = read_env
        self.config_key = config_key
        self.settings: dict[str, str] = {}

    def load_config(self, config_file: str | None = None, env_file: str | None = None):
        """Load the configuration from files and set the settings.

        If not provided, the config will be loaded from the default locations.

        Args:
            config_file: The path to the configuration file.
            env_file: The path to the environment file. Secret values should be loaded from this file.
        """

        def __load_key(key: str, config: dict):
            current_config = config
            for key in __split_key(key):
                current_config = current_config[key]
            return current_config

        config = self.read_config(config_file)
        if self.config_key:
            route = __split_key(self.config_key)
            for key in route:
                if key not in config:
                    raise KeyError(f"Key {key} not found in configuration file")
                config = config[key]

        for key, setting in self.settings.items():
            value = __load_key(key, config)
            setattr(self, setting, value)

        if self.read_env:
            env_config = self.read_env(env_file)
            for key, setting in self.settings.items():
                if key in env_config:
                    value = __load_key(key, env_config)
                    setattr(self, setting, value)
        else:
            if env_file:
                raise ValueError(
                    "The configurable doesn't accept a separate environment file"
                )
