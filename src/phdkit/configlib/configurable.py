from threading import Lock
from typing import (
    Type,
    Callable,
    Any,
    overload,
    Protocol,
    Self,
)
from .configreader import ConfigLoader


class _Unset:
    __instance = None

    def __new__(cls) -> "_Unset":
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance


Unset = _Unset()


def split_key(key: str) -> list[str]:
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
            type,
            tuple[str, ConfigLoader | None, ConfigLoader | None, dict[str, "Setting"]],
        ] = {}
        self.default_values: dict[type, dict[str, Any]] = {}

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

        class __SingleConfig:
            def load(self, config_file: str | None = None, env_file: str | None = None):
                """Load the configuration from files and set the settings.

                This method is equivalent to the `load` method of the `Config` class.
                If not provided, the config will be loaded from the default locations.

                Args:
                    config_file: The path to the configuration file.
                    env_file: The path to the environment file. Secret values should be loaded from this file.
                """
                Config.load(instance, config_file, env_file)

            def update(
                self,
                *,
                load_config: ConfigLoader | None = None,
                load_env: ConfigLoader | None = None,
                config_key: str = "",
            ):
                """Update the configuration set-ups for a class.

                This method is equivalent to the `update` method of the `Config` class.
                If not provided, the config will be loaded from the default locations.

                Args:
                    load_config: A callable that reads the configuration file and returns a dictionary.
                    load_env: A callable that reads the secret config values and returns a dictionary.
                    config_key: The config key to use for this class. If provided, only the parts of the config file that correspond to this key will be loaded.
                """
                Config.update(
                    instance,
                    load_config=load_config,
                    load_env=load_env,
                    config_key=config_key,
                )

        return __SingleConfig()

    def register[T](
        self,
        klass: Type[T],
        load_config: ConfigLoader | None = None,
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
        self.default_values[klass] = {}

    def update[T](
        self,
        klass: Type[T],
        *,
        load_config: ConfigLoader | None = None,
        load_env: ConfigLoader | None = None,
        config_key: str = "",
    ):
        """Update the config registry of a class.

        This method updates the config registry of a class with a optional config key. `load_config` will be used to load the config file
        and `load_env`, if provided, will be used to load secret values from a separate config file or environment variables.
        A class will be registered if it isn't in the registries before.

        Args:
            klass: The class to register
            load_config: A callable that reads the configuration file and returns a dictionary.
            load_env: A callable that reads the secret config values and returns a dictionary.
            config_key: The config key to use for this class. If provided, only the parts of the config file that correspond to this key will be loaded.
        """

        if klass not in self.registry:
            self.register(klass, load_config, load_env=load_env, config_key=config_key)
        else:
            (config_key0, load_config0, load_env0, settings) = self.registry[klass]
            config_key1 = config_key if config_key else config_key0
            load_config1 = load_config if load_config is not None else load_config0
            load_env1 = load_env if load_env is not None else load_env0
            self.registry[klass] = (config_key1, load_config1, load_env1, settings)

    def contains[T](self, klass: Type[T], config_key: str) -> bool:
        """Check if a class is registered with a config key.

        This method checks if the class is registered with the given config key. If the class is not registered, a ValueError will be raised.

        Args:
            klass: The class to check
            config_key: The config key to use for this class. If provided, only the parts of the config file that correspond to this key will be loaded.
        """
        return klass in self.registry and self.registry[klass][0] == config_key

    def add_setting[I, V](
        self,
        klass: Type[I],
        config_key: str,
        setting: "Setting[I, V]",
        default: _Unset | V = Unset,
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
        if default is not Unset:
            self.default_values[klass][config_key] = default

    def add_default_value[I](self, klass: Type[I], config_key: str, value: object):
        """Add a default value for a setting.

        This method adds a default value for a setting. The setting should be an instance of the Setting class.
        Old default values, if present, will be replaced.

        Args:
            klass: The class to add the default value to
            config_key: The config key to use for this setting. If provided, only the parts of the config file that correspond to this key will be loaded.
            value: The default value to add
        """
        if klass not in self.default_values:
            self.default_values[klass] = {}
        self.default_values[klass][config_key] = value

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
            for key in split_key(key):
                if key not in current_config:
                    raise KeyError(f"Key {key} not found in configuration file")
                current_config = current_config[key]
            return current_config

        def __merge_config(config1: dict, config2: dict) -> dict:
            """Recursively merge two dictionaries.

            When there are overlapping keys, if both values are dictionaries, they are merged recursively.
            Otherwise, the value from config2 overwrites the value from config1.

            Args:
                config1: The base dictionary
                config2: The dictionary to merge on top of config1

            Returns:
                A new dictionary with merged values
            """
            result = config1.copy()

            for key, value in config2.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    # If both values are dictionaries, merge them recursively
                    result[key] = __merge_config(result[key], value)
                else:
                    # Otherwise, overwrite the value
                    result[key] = value

            return result

        if load_config is None:
            raise ValueError(
                f"Config file loader is not provided for class {klass}. Please provide one."
            )
        config = load_config(config_file)
        if load_env:
            env_config = load_env(env_file)
            config = __merge_config(config, env_config)
        else:
            if env_file:
                raise ValueError(
                    "The configurable doesn't accept a separate environment file"
                )

        if config_key:
            route = split_key(config_key)
            for key in route:
                if key not in config:
                    raise KeyError(f"Key {key} not found in configuration file")
                config = config[key]

        for key, setting in settings.items():
            try:
                value = __load_key(key, config)
            except KeyError as e:
                if config_key in self.default_values[klass]:
                    # If the key is not found in the config, use the default value
                    return self.default_values[klass][config_key]
                raise e
            if setting.fset is None:
                raise NotImplementedError(
                    f"Setting {key} does not have a setter method. Please implement a setter method for this setting."
                )
            setting.fset(instance, value)


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
        Config.update(
            cls, load_config=load_config, load_env=load_env, config_key=config_key
        )
        return cls

    return decorator


class Descriptor[I, V](Protocol):
    def __init__(self, method: Callable[[I], V]) -> None: ...

    def __set_name__(self, owner: Type[I], name: str) -> None: ...

    @overload
    def __get__(self, instance: None, owner: Type[I]) -> "Descriptor": ...

    @overload
    def __get__(self, instance: I, owner: Type[I]) -> V: ...

    def __get__(self, instance: I | None, owner: Type[I]) -> "V | Descriptor": ...

    def __set__(self, instance: I, value: V) -> None: ...

    def setter(self, fset: Callable[[I, V], None]) -> "Descriptor[I, V]":
        """Decorator to register a method as a setting setter.

        Note that due to unknown reasons, the setter must be of a different name of the getter, or otherwise
        the type checkers (at least the one used by VSCode) will report a obscured method name error. This is
        different from the built-in `property.setter` decorator.

        Args:
            fset: The setter method to register as a setting setter.
        """
        ...


def mangle_attr(the_self, attr):
    # return public attrs unchanged
    if not attr.startswith("__") or attr.endswith("__") or "." in attr:
        return attr
    # if source is an object, get the class
    if not hasattr(the_self, "__bases__"):
        the_self = the_self.__class__
    # mangle attr
    return f"_{the_self.__name__.lstrip('_')}{attr}"


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
        self, config_key: str, *, default: _Unset | Any = Unset
    ) -> Callable[[Callable[[T], S]], Descriptor[T, S]]:
        """Decorator to register a method as a setting.

        This decorator registers the method as a setting with a config key. It will ignore the definition of the method
        and generate default getter and setter methods.

        Args:
            config_key: The config key to use for this setting. If provided, only the parts of the config file that correspond to this key will be loaded.
            method: The method to register as a setting.
        """

        class __decorator[I, V]:
            # XXX: Could we refine `default` to a more specific type?
            def __init__(self, method: Callable[[I], V], default: _Unset | Any = Unset):
                self.method = method
                name = self.method.__name__
                attr_name = f"__{name}"

                def fget(the_self: Any) -> V:
                    return getattr(the_self, mangle_attr(the_self, attr_name))

                def fset(the_self: Any, value: V) -> None:
                    setattr(the_self, mangle_attr(the_self, attr_name), value)

                s = Setting(fget=fget, fset=fset)
                self.setting: Setting[Any, V] = s
                self.default = default

            def __set_name__(self, owner: Type[I], name: str):
                # The `setting` decorator will be invoked before the `configurable` decorator.
                #  We must guarantee the existence of the registry.
                Config.update(owner)
                Config.add_setting(owner, config_key, self.setting, self.default)

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
                if instance is None:
                    raise ValueError(
                        "Setting getter cannot be called on the class itself. Please call it on an instance of the class."
                    )
                if self.setting.fget is None:
                    raise NotImplementedError(
                        f"Setting {self.method.__name__} does not have a getter method. Please implement a getter method for this setting."
                    )
                return self.setting.fget(instance)

            def __set__(self: Self, instance: I, value: V):
                if self.setting.fset is None:
                    raise NotImplementedError(
                        f"Setting {self.method.__name__} does not have a setter method. Please implement a setter method for this setting."
                    )
                self.setting.fset(instance, value)

            def setter(self: Self, fset: Callable[[I, V], None]) -> "__decorator[I, V]":
                raise NotImplementedError(
                    f"Setting {self.method.__name__} already has a setter method. You cannot add another!"
                )

        # The wrapper is only to please the type checker
        def __wrapper(
            method: Callable[[T], S]
        ) -> __decorator[T, S]:
            return __decorator(method, default=default)

        return __wrapper

    def getter[T, S](
        self, config_key: str
    ) -> Callable[[Callable[[T], S]], Descriptor[T, S]]:
        """Decorator to register a method as a setting getter."""

        class __getter[I, V]:
            def __init__(
                self, method: Callable[[I], V], *, default: _Unset | V = Unset
            ):
                self.method = method
                s = Setting(fget=self.method, fset=None)
                self.setting = s
                self.default = default
                self.owner: Type[I] | None = None

            def __set_name__(self, owner: Type[I], name: str):
                self.owner = owner
                Config.update(owner)
                if Config.contains(owner, config_key):
                    raise ValueError(
                        f"Config key {config_key} is already registered for class {owner}"
                    )
                Config.add_setting(owner, config_key, self.setting, self.default)

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
                if instance is None:
                    raise ValueError(
                        "Setting getter cannot be called on the class itself. Please call it on an instance of the class."
                    )
                if self.setting.fget is None:
                    raise NotImplementedError(
                        f"Setting {self.method.__name__} does not have a getter method. Please implement a getter method for this setting."
                    )
                return self.setting.fget(instance)

            def __set__(self, instance: I, value: V):
                if self.setting.fset is None:
                    raise NotImplementedError(
                        f"Setting {self.method.__name__} does not have a setter method. Please implement a setter method for this setting."
                    )
                self.setting.fset(instance, value)

            def setter(self, fset: Callable[[I, V], None]) -> "__getter[I, V]":
                self.setting.fset = fset
                assert self.owner is not None
                return self

        def __wrapper(method: Callable[[T], S]) -> __getter[T, S]:
            return __getter(method)

        return __wrapper


setting = __setting()
