from typing import Type, Callable
from .configreader import ConfigReader


def __split_key(key: str) -> list[str]:
    return key.split(".")


def configurable(read_config: ConfigReader, read_env: ConfigReader | None = None):
    def __configurable(cls: Type) -> Type:
        settings = {}
        for name, attribute in cls.__dict__.items():
            if callable(attribute) and hasattr(attribute, "config_key"):
                settings[attribute.config_key] = attribute
        cls.settings = settings

        def load_config(self, config_file: str | None = None):
            def __load_key(key: str, config: dict):
                current_config = config
                for key in __split_key(key):
                    current_config = current_config[key]
                return current_config

            config = read_config(config_file)
            for key, setter in self.settings.items():
                setter(self, __load_key(key, config))
            if read_env:
                env_config = read_env(config_file)
                for key, setter in self.settings.items():
                    if key in env_config:
                        setter(self, __load_key(key, env_config))

        cls.load_config = load_config
        return cls
    return __configurable


def setting(key: str):
    def __setting(setter: Callable) -> Callable:
        def wrapper(instance: Type) -> Type:
            setter.config_key = key
            return setter(instance)

        return wrapper
    return __setting
