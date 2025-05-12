# TODO: Add more functionalities

import tomllib
from typing import Callable, Protocol
from .configurable import ConfigLoader


class TomlReader(ConfigLoader):
    def __init__(self, path: str):
        self.path = path

    def __call__(self) -> dict:
        with open(self.path, "rb") as f:
            return tomllib.load(f)
