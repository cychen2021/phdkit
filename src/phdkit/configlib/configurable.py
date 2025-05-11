from typing import Type, Callable, Any
from .configreader import ConfigReader
from abc import ABC


def __split_key(key: str) -> list[str]:
    return key.split(".")


class Configurable[T](Any, ABC):
    """A class that has been make configurable.

    This class is only for type hinting purposes. It is not meant to be used directly.
    """

    def load_config(self, config_file: str | None = None, env_file: str | None = None):
        """Load the configuration from files and set the settings.

        If not provided, the config will be loaded from the default locations.

        Args:
            config_file: The path to the configuration file.
            env_file: The path to the environment file. Secret values should be loaded from this file.
        """
        ...


def configurable(
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

    def __configurable[T](cls: Type[T]) -> Type[Configurable[T]]:
        settings = {}
        for name, attribute in cls.__dict__.items():
            if callable(attribute) and hasattr(attribute, "config_key"):
                settings[attribute.config_key] = attribute
        cls.settings = settings  # type: ignore

        def load_config(
            self, config_file: str | None = None, env_file: str | None = None
        ):
            def __load_key(key: str, config: dict):
                current_config = config
                for key in __split_key(key):
                    current_config = current_config[key]
                return current_config

            config = read_config(config_file)
            if config_key:
                route = __split_key(config_key)
                for key in route:
                    if key not in config:
                        raise KeyError(f"Key {key} not found in configuration file")
                    config = config[key]

            for key, setter in self.settings.items():
                setter(self, __load_key(key, config))
            if read_env:
                env_config = read_env(env_file)
                for key, setter in self.settings.items():
                    if key in env_config:
                        setter(self, __load_key(key, env_config))
            else:
                if env_file:
                    raise ValueError(
                        "The configurable doesn't accept a separate environment file"
                    )

        cls.load_config = load_config  # type: ignore
        return cls  # type: ignore

    return __configurable


def setting(config_key: str):
    """Decorator to mark a method as a setting setter.

    This decorator marks a method as a setting setter. The method should be a property setter
    that takes a value and sets it to the instance. The method should also have a `config_key`
    attribute that specifies the key in the configuration file that corresponds to this setting.

    Args:
        config_key: The key in the configuration file that corresponds to this setting, separated by dots.
    """

    def __setting(setter: Callable) -> Callable:
        def wrapper(instance: Type) -> Type:
            setter.config_key = config_key
            return setter(instance)

        return wrapper

    return __setting
