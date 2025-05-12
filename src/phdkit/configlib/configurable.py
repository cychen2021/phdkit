from threading import Lock
from typing import Type, Callable, Any
from .configreader import ConfigLoader


def __split_key(key: str) -> list[str]:
    return key.split(".")


class __Config:
    _singleton = None
    _singleton_lock = Lock()

    def __new__(cls):
        if cls._singleton is None:
            with cls._singleton_lock:
                if (
                    cls._singleton is None
                ):  # Double check since there may be another thread is creating the singleton
                    cls._singleton = super().__new__(cls)
        return cls._singleton

    def __init__(self):
        self.registry: dict[
            type, tuple[str, ConfigLoader, ConfigLoader | None, dict[str, "Setting"]]
        ] = {}

    def register[T](
        self,
        klass: Type[T],
        load_config: ConfigLoader,
        *,
        load_env: ConfigLoader | None = None,
        config_key: str = "",
    ):
        """Register a class with a config key.

        This method books the class in the registry with a optional config key. `load_config` will be used to load the config file
        and `load_env`, if provided, will be used to load secret values from a separate config file or environment variables.

        Args:
            klass: The class to register
            load_config: A callable that reads the configuration file and returns a dictionary.
            load_env: A callable that reads the secret config values and returns a dictionary.
            config_key: The config key to use for this class. If provided, only the parts of the config file that correspond to this key will be loaded.
        """
        self.registry[klass] = (config_key, load_config, load_env, {})

    def add_setting[T](self, klass: Type[T], config_key: str, setting: "Setting"):
        """Add a setting to a class.

        This method adds a setting to the class. The setting should be an instance of the Setting class.
        Old settings, if present, will be replaced.

        Args:
            klass: The class to add the setting to
            config_key: The config key to use for this setting. If provided, only the parts of the config file that correspond to this key will be loaded.
            setting: The setting to add
        """

        if klass not in self.registry:
            raise ValueError(f"Class {klass} is not registered")
        self.registry[klass][3][config_key] = setting

    def get_setting(self, klass: Type[Any], config_key: str) -> "Setting":
        """Get the settings for a class with a config key.

        This method returns the settings for the class with the given config key. If the class is not registered, a ValueError will be raised.

        Args:
            klass: The class to get the settings for
            config_key: The config key to use for this class. If provided, only the parts of the config file that correspond to this key will be loaded.
        """
        if klass not in self.registry:
            raise ValueError(f"Class {klass} is not registered")
        if config_key not in self.registry[klass][3]:
            raise ValueError(
                f"Config key {config_key} is not registered for class {klass}"
            )
        return self.registry[klass][3][config_key]

    def load(
        self, instance: Any, config_file: str | None = None, env_file: str | None = None
    ):
        """Load the configuration from files and set the settings.

        If not provided, the config will be loaded from the default locations.

        Args:
            instance: The instance of the class to load the configuration for.
            config_file: The path to the configuration file.
            env_file: The path to the environment file. Secret values should be loaded from this file.
        """
        klass = type(instance)
        if klass not in self.registry:
            raise ValueError(f"Class {klass} is not registered")
        config_key, load_config, load_env, settings = self.registry[klass]

        def __load_key(key: str, config: dict):
            current_config = config
            for key in __split_key(key):
                current_config = current_config[key]
            return current_config

        config = load_config(config_file)
        if config_key:
            route = __split_key(config_key)
            for key in route:
                if key not in config:
                    raise KeyError(f"Key {key} not found in configuration file")
                config = config[key]

        for key, setting in settings.items():
            value = __load_key(key, config)
            if setting.fset is None:
                raise NotImplementedError(
                    f"Setting {key} does not have a setter method. Please implement a setter method for this setting."
                )
            setting.fset(instance, value)

        if load_env:
            env_config = load_env(env_file)
            for key, setting in settings.items():
                if key in env_config:
                    value = __load_key(key, env_config)
                    if setting.fset is None:
                        raise NotImplementedError(
                            f"Setting {key} does not have a setter method. Please implement a setter method for this setting."
                        )
                    setting.fset(instance, value)
        else:
            if env_file:
                raise ValueError(
                    "The configurable doesn't accept a separate environment file"
                )


Config = __Config()


class Setting[S, T]:
    def __init__(
        self,
        fget: Callable[[S], T] | None = None,
        fset: Callable[[S, T], None] | None = None,
    ):
        self.fset = fset
        self.fget = fget
        self.__property = property(fget=fget, fset=fset)

    def __set__(self, owner: S, value: T):
        self.__property.__set__(owner, value)

    def __get__(self, owner: S, owner_type: Type[S]) -> T:
        return self.__property.__get__(owner, owner_type)


def configurable(
    load_config: ConfigLoader,
    *,
    config_key: str = "",
    load_env: ConfigLoader | None = None,
):
    """Decorator to register a class as configurable.

    This decorator registers the class with the config key and loads the configuration from the file.
    The class should have a `__init__` method that takes no arguments.

    Args:
        config_key: The config key to use for this class. If provided, only the parts of the config file that correspond to this key will be loaded.
        load_config: A callable that reads the configuration file and returns a dictionary.
        load_env: A callable that reads the secret config values and returns a dictionary.
    """

    def decorator[T: Type](cls: T) -> T:
        Config.register(cls, load_config, load_env=load_env, config_key=config_key)
        return cls

    return decorator


class __setting:
    _singleton = None
    _singleton_lock = Lock()

    def __new__(cls):
        if cls._singleton is None:
            with cls._singleton_lock:
                if cls._singleton is None:
                    cls._singleton = super().__new__(cls)
        return cls._singleton

    def __init__(self):
        pass

    def __call__[T](
        self, config_key: str
    ) -> Callable[[Callable[[Any], T]], Setting[Any, T]]:
        """Decorator to register a method as a setting.

        This decorator registers the method as a setting with a config key. It will ignore the definition of the method
        and generate default getter and setter methods.

        Args:
            config_key: The config key to use for this setting. If provided, only the parts of the config file that correspond to this key will be loaded.
            method: The method to register as a setting.
        """

        def decorator(method: Callable[[Any], T]) -> Setting[Any, T]:
            name = method.__name__
            attr_name = f"__setting_{name}"

            def fget(the_self: Any) -> T:
                return getattr(the_self, attr_name)

            def fset(the_self: Any, value: T):
                setattr(the_self, attr_name, value)

            s = Setting(fget=fget, fset=fset)
            setattr(method.__self__, name, s)
            Config.add_setting(type(method.__self__), config_key, s)
            return s

        return decorator

    def setter[U, T](self, config_key: str):
        """Decorator to register a method as a setting setter."""

        def decorator(method: Callable[[U, T], None]):
            try:
                s = Config.get_setting(type(method.__self__), config_key)
                s = Setting(
                    fget=s.fget,
                    fset=method,
                )
            except ValueError:
                s = Setting(fget=None, fset=method)
            setattr(method.__self__, method.__name__, s)
            Config.add_setting(type(method.__self__), config_key, s)
            return s

        return decorator

    def getter[U, T](self, config_key: str):
        """Decorator to register a method as a setting getter."""

        def decorator(method: Callable[[U], T]):
            try:
                s = Config.get_setting(type(method.__self__), config_key)
                s = Setting(
                    fget=method,
                    fset=s.fset,
                )
            except ValueError:
                s = Setting(fget=method, fset=None)
            setattr(method.__self__, method.__name__, s)
            Config.add_setting(type(method.__self__), config_key, s)
            return s

        return decorator


setting = __setting()
