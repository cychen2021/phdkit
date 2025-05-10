from typing import Protocol


class ConfigReader(Protocol):
    def __call__(self, config_file: str | None) -> dict: ...
