from typing import Type, Callable
from .configreader import ConfigReader


def __split_key(key: str) -> list[str]:
    return key.split(".")


def configurable(cls: Type, *, config_reader: ConfigReader) -> Type:
    settings = {}
    for name, attribute in cls.__dict__.items():
        if callable(attribute) and hasattr(attribute, "config_key"):
            settings[attribute.config_key] = attribute
    cls.settings = settings

    def load_config(self):
        def __load_key(key: str, config: dict):
            current_config = config
            for key in __split_key(key):
                current_config = current_config[key]
            return current_config

        config = config_reader()
        for key, setter in self.settings.items():
            setter(self, __load_key(key, config))

    cls.load_config = load_config
    return cls


def setting(setter: Callable, key: str) -> Callable:
    def wrapper(instance: Type) -> Type:
        setter.config_key = key
        return setter(instance)

    return wrapper
