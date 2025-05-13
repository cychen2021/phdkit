from threading import Lock
from typing import (
    Type,
    Callable,
    Any,
    type_check_only,
    overload,
    Protocol,
    Self,
    TypeVar,
)
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

    def __getitem__(self, instance: Any):
        """Another form of the `load` method.

        This method returns an object that loads the configuration for the given instance as another form of the `load` method.

        Example usage:

        ```python
        config[obj].load("config.toml", "env.toml")
        ```

        equivalent to

        ```python
        Config.load(obj, "config.toml", "env.toml")
        ```
        """

        class __Load:
            def load(self, config_file: str | None = None, env_file: str | None = None):
                """Load the configuration from files and set the settings.

                This method is equivalent to the `load` method of the `Config` class.
                If not provided, the config will be loaded from the default locations.

                Args:
                    config_file: The path to the configuration file.
                    env_file: The path to the environment file. Secret values should be loaded from this file.
                """
                Config.load(instance, config_file, env_file)

        return __Load()

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

    def contains[T](self, klass: Type[T], config_key: str) -> bool:
        """Check if a class is registered with a config key.

        This method checks if the class is registered with the given config key. If the class is not registered, a ValueError will be raised.

        Args:
            klass: The class to check
            config_key: The config key to use for this class. If provided, only the parts of the config file that correspond to this key will be loaded.
        """
        return klass in self.registry and self.registry[klass][0] == config_key

    def add_setting[I, V](
        self, klass: Type[I], config_key: str, setting: "Setting[I, V]"
    ):
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

    def get_setting[I](self, klass: Type[I], config_key: str) -> "Setting[I, Any]":
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
config = __Config()


class Setting[I, V]:
    """A setting"""

    def __init__(
        self,
        fget: Callable[[I], V] | None = None,
        fset: Callable[[I, V], None] | None = None,
    ):
        self.fget = fget
        self.fset = fset

    def __get__(self, instance: I | None, owner: Type[I]) -> V:
        if self.fget is None:
            raise NotImplementedError(
                f"Setting does not have a getter method. Please implement a getter method for this setting."
            )
        if instance is None:
            raise NotImplementedError(
                f"Setting does not have a getter method. Please implement a getter method for this setting."
            )
        return self.fget(instance)

    def __set__(self, instance: I, value: V) -> None:
        if self.fset is None:
            raise NotImplementedError(
                f"Setting does not have a setter method. Please implement a setter method for this setting."
            )
        self.fset(instance, value)


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


@type_check_only
class __Descriptor[I, V](Protocol):
    def __init__(self, method: Callable[[I], V]) -> None: ...

    def __set_name__(self, owner: Type[I], name: str) -> None: ...

    @overload
    def __get__(self, instance: None, owner: Type[I]) -> "__Descriptor": ...

    @overload
    def __get__(self, instance: I, owner: Type[I]) -> V: ...

    def __get__(self, instance: I | None, owner: Type[I]) -> "V | __Descriptor": ...

    def __set__(self, instance: I, value: V) -> None: ...


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

    def __call__[T, S](
        self, config_key: str
    ) -> Callable[[Callable[[T], S]], __Descriptor[T, S]]:
        """Decorator to register a method as a setting.

        This decorator registers the method as a setting with a config key. It will ignore the definition of the method
        and generate default getter and setter methods.

        Args:
            config_key: The config key to use for this setting. If provided, only the parts of the config file that correspond to this key will be loaded.
            method: The method to register as a setting.
        """

        class __decorator[I, V]:
            def __init__(self, method: Callable[[I], V]):
                self.method = method
                name = self.method.__name__
                attr_name = f"__setting_{name}"

                def fget(the_self: Any) -> V:
                    return getattr(the_self, attr_name)

                def fset(the_self: Any, value: V) -> None:
                    setattr(the_self, attr_name, value)

                s = Setting(fget=fget, fset=fset)
                self.setting = s

            def __set_name__(self, owner: Type[I], name: str):
                Config.add_setting(owner, config_key, self.setting)

            @overload
            def __get__(self, instance: I, owner: Type[I]) -> V:
                if self.setting.fget is None:
                    raise NotImplementedError(
                        f"Setting {self.method.__name__} does not have a getter method. Please implement a getter method for this setting."
                    )
                return self.setting.fget(instance)

            @overload
            def __get__(self, instance: None, owner: Type[Any]) -> "__decorator":
                raise NotImplementedError(
                    f"Setting {self.method.__name__} does not have a getter method. Please implement a getter method for this setting."
                )

            def __get__(self, instance: I | None, owner: Type[I]) -> "V | __decorator":
                raise NotImplementedError(
                    f"Setting {self.method.__name__} does not have a getter method. Please implement a getter method for this setting."
                )

            def __set__(self: Self, instance: I, value: V):
                if self.setting.fset is None:
                    raise NotImplementedError(
                        f"Setting {self.method.__name__} does not have a setter method. Please implement a setter method for this setting."
                    )
                self.setting.fset(instance, value)

        def __wrapper(method: Callable[[T], S]) -> __decorator[T, S]:
            return __decorator(method)

        return __wrapper

    def getter[T, S](
        self, config_key: str
    ) -> Callable[[Callable[[T], S]], __Descriptor[T, S]]:
        """Decorator to register a method as a setting getter."""

        class __getter[I, V]:
            def __init__(self, method: Callable[[I], V]):
                self.method = method

            def __set_name__(self, owner: Type[I], name: str):
                if Config.contains(owner, config_key):
                    raise ValueError(
                        f"Config key {config_key} is already registered for class {owner}"
                    )
                s = Setting(fget=self.method, fset=None)
                self.setting = s
                Config.add_setting(owner, config_key, s)

            @overload
            def __get__(self, instance: I, owner: Type[I]) -> V:
                if self.setting.fget is None:
                    raise NotImplementedError(
                        f"Setting {self.method.__name__} does not have a getter method. Please implement a getter method for this setting."
                    )
                return self.setting.fget(instance)

            @overload
            def __get__(self, instance: None, owner: Type[I]) -> "__getter":
                raise NotImplementedError(
                    f"Setting {self.method.__name__} does not have a getter method. Please implement a getter method for this setting."
                )

            def __get__(self, instance: I | None, owner: Type[I]) -> "V | __getter":
                raise NotImplementedError(
                    f"Setting {self.method.__name__} does not have a getter method. Please implement a getter method for this setting."
                )

            def __set__(self, instance: I, value: V):
                if self.setting.fset is None:
                    raise NotImplementedError(
                        f"Setting {self.method.__name__} does not have a setter method. Please implement a setter method for this setting."
                    )
                self.setting.fset(instance, value)

            def setter(self: Self, fset: Callable[[I, V], None]) -> None:
                """Decorator to register a method as a setting setter."""
                self.setting.fset = fset

        def __wrapper(method: Callable[[T], S]) -> __getter[T, S]:
            return __getter(method)

        return __wrapper


setting = __setting()
