import tomllib
from typing import Callable, Protocol
from .configurable import ConfigReader

class TomlReader(ConfigReader):
    def __init__(self, path: str):
        self.path = path

    def __call__(self) -> dict:
        with open(self.path, "rb") as f:
            return tomllib.load(f)