from typing import Protocol


class ConfigLoader(Protocol):
    def __call__(self, config_file: str | None) -> dict: ...
