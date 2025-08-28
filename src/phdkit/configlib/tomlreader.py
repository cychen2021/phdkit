# TODO: Add more functionalities

import tomllib
from .configurable import ConfigLoader


class TomlReader(ConfigLoader):
    def __init__(self, default_path: str):
        self.default_path = default_path

    def __call__(self, path: str | None = None) -> dict:
        with open(path or self.default_path, "rb") as f:
            return tomllib.load(f)
